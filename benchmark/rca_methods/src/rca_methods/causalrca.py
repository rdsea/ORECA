import math
import time
import warnings

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as f
import torch.optim as optim
from sknetwork.ranking import PageRank
from torch.autograd import Variable
from torch.optim import lr_scheduler

from rca_methods.base_rca import BaseRCA
from rca_methods.io.time_series import drop_constant, preprocess

warnings.filterwarnings("ignore")
_EPS = 1e-10

MAX_LR = 1e-2
MIN_LR = 1e-4


class MLPEncoder(nn.Module):  # NOTE
    """MLP encoder module."""

    def __init__(
        self,
        n_in,
        n_xdims,
        n_hid,
        n_out,
        adj_a,
        batch_size,
        do_prob=0.0,
        factor=True,
        tol=0.1,
    ):
        super().__init__()

        self.adj_A = nn.Parameter(
            Variable(torch.from_numpy(adj_a).double(), requires_grad=True)
        )
        self.factor = factor

        self.Wa = nn.Parameter(torch.zeros(n_out), requires_grad=True)
        self.fc1 = nn.Linear(n_xdims, n_hid, bias=True)
        self.fc2 = nn.Linear(n_hid, n_out, bias=True)
        self.dropout_prob = do_prob
        self.batch_size = batch_size
        self.z = nn.Parameter(torch.tensor(tol))
        self.z_positive = nn.Parameter(
            torch.ones_like(torch.from_numpy(adj_a)).double()
        )
        self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight.data)
            elif isinstance(m, nn.BatchNorm1d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def forward(self, inputs):
        if torch.sum(self.adj_A != self.adj_A):
            print("nan error \n")

        # to amplify the value of A and accelerate convergence.
        adj_a1 = torch.sinh(3.0 * self.adj_A)

        # adj_Aforz = I-A^T
        adj_a_for_z = self.preprocess_adj_new(adj_a1)

        adj_a = torch.eye(adj_a1.size()[0]).double()
        h1 = f.relu(self.fc1(inputs))
        x = self.fc2(h1)
        logits = torch.matmul(adj_a_for_z, x + self.Wa) - self.Wa

        return x, logits, adj_a1, adj_a, self.z, self.z_positive, self.adj_A, self.Wa


class MLPDecoder(nn.Module):  # NOTE
    """MLP decoder module."""

    def __init__(
        self,
        n_in_node,
        n_in_z,
        n_out,
        encoder,
        data_variable_size,
        batch_size,
        n_hid,
        do_prob=0.0,
    ):
        super().__init__()

        self.out_fc1 = nn.Linear(n_in_z, n_hid, bias=True)
        self.out_fc2 = nn.Linear(n_hid, n_out, bias=True)

        self.batch_size = batch_size
        self.data_variable_size = data_variable_size

        self.dropout_prob = do_prob

        self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight.data)
                m.bias.data.fill_(0.0)
            elif isinstance(m, nn.BatchNorm1d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def forward(self, inputs, input_z, n_in_node, origin_a, adj_a_tilt, w_a):
        # adj_A_new1 = (I-A^T)^(-1)
        adj_a_new1 = self.preprocess_adj_new1(origin_a)
        mat_z = torch.matmul(adj_a_new1, input_z + w_a) - w_a

        h3 = f.relu(self.out_fc1(mat_z))
        out = self.out_fc2(h3)

        return mat_z, out, adj_a_tilt


class CausalRCA(BaseRCA):  # NOTE
    """CausalRCA RCA method."""

    def __init__(self, profile: bool = False):
        """Initialize the CausalRCA RCA method."""
        super().__init__(profile)
        self.CONFIG = self._create_config()

    def _run(
        self, dataset: pd.DataFrame, injection_time: int | None, top_k=5, **kwargs
    ) -> list[tuple[str, float]]:
        """Run the CausalRCA RCA method.

        Args:
            dataset (pd.DataFrame): The input dataset containing time series data.
            injection_time (int | None): The timestamp when the fault was injected.
            top_k (int, optional): The number of top root causes to return. Defaults to 5.
            **kwargs: Additional keyword arguments.

        Returns:
            list[tuple[str, float]]: A list of tuples containing root causes and their scores.
        """
        data = dataset
        dataset_name = kwargs.get("dataset", None)
        # with_bg = kwargs.get("with_bg", False)

        if isinstance(data, dict):  # multimodal
            metric = data["metric"]
            logts = data["logts"]
            # traces_err = data["tracets_err"]
            # traces_lat = data["tracets_lat"]

            # === metric ===
            metric = metric.iloc[::15, :]

            # == metric ==
            normal_metric = metric[metric["time"] < injection_time]
            anomal_metric = metric[metric["time"] >= injection_time]
            normal_metric = preprocess(
                data=normal_metric,
                dataset=dataset_name,
                dk_select_useful=kwargs.get("dk_select_useful", False),
            )
            anomal_metric = preprocess(
                data=anomal_metric,
                dataset=dataset_name,
                dk_select_useful=kwargs.get("dk_select_useful", False),
            )
            intersect = [x for x in normal_metric.columns if x in anomal_metric.columns]
            normal_metric = normal_metric[intersect]
            anomal_metric = anomal_metric[intersect]
            metric = pd.concat(
                [normal_metric, anomal_metric], axis=0, ignore_index=True
            )
            data = metric
            print(f"{normal_metric.shape=}")
            print(f"{anomal_metric.shape=}")
            print(f"{metric.shape=}")
            print("with metric", data.shape)

            # == logts ==
            logts = drop_constant(logts)
            normal_logts = logts[logts["time"] < injection_time].drop(columns=["time"])
            anomal_logts = logts[logts["time"] >= injection_time].drop(columns=["time"])
            log = pd.concat([normal_logts, anomal_logts], axis=0, ignore_index=True)
            data = pd.concat([data, log], axis=1)
            print(f"{normal_logts.shape=}")
            print(f"{anomal_logts.shape=}")
            print(f"{log.shape=}")
            print("with log", data.shape)
            data.to_csv("debug_withlog.csv", index=False)

            # print(f"{normalize=} {addup=}")

            # # == traces_err ==
            # if dataset_name == "mm-tt" or dataset_name == "mm-ob":
            #     traces_err = traces_err.fillna(method='ffill')
            #     traces_err = traces_err.fillna(0)
            #     traces_err = drop_constant(traces_err)

            #     normal_traces_err = traces_err[traces_err["time"] < injection_time].drop(columns=["time"])
            #     anomal_traces_err = traces_err[traces_err["time"] >= injection_time].drop(columns=["time"])
            #     trace = pd.concat([normal_traces_err, anomal_traces_err], axis=0, ignore_index=True)
            #     data = pd.concat([data, trace], axis=1)
            #     print(f"{normal_traces_err.shape=}")
            #     print(f"{anomal_traces_err.shape=}")
            #     print(f"{trace.shape=}")
            #     print("with traces_err", data.shape)
            #
            #  # == traces_lat ==
            # if dataset_name == "mm-tt" or dataset_name == "mm-ob":
            #     traces_lat = traces_lat.fillna(method='ffill')
            #     traces_lat = traces_lat.fillna(0)
            #     traces_lat = drop_constant(traces_lat)
            #     normal_traces_lat = traces_lat[traces_lat["time"] < injection_time].drop(columns=["time"])
            #     anomal_traces_lat = traces_lat[traces_lat["time"] >= injection_time].drop(columns=["time"])
            #     trace = pd.concat([normal_traces_lat, anomal_traces_lat], axis=0, ignore_index=True)
            #     data = pd.concat([data, trace], axis=1)
            #     print(f"{normal_traces_lat.shape=}")
            #     print(f"{anomal_traces_lat.shape=}")
            #     print(f"{trace.shape=}")
            #     print("with traces_lat", data.shape)

            # dump to debug.csv
            # data.to_csv("debug.csv", index=False)
            # drop duplicated columns
            data = data.loc[:, ~data.columns.duplicated()]
            data = data.fillna(0)

        else:
            data = preprocess(
                data=data,
                dataset=dataset_name,
                dk_select_useful=kwargs.get("dk_select_useful", False),
            )

        data /= data.max()

        data_sample_size = data.shape[0]
        data_variable_size = data.shape[1]

        node_names = data.columns.to_list()

        # graph construction, get the adj
        train_data = data

        # Generate off-diagonal interaction graph
        np.ones([data_variable_size, data_variable_size]) - np.eye(data_variable_size)

        # add adjacency matrix A
        num_nodes = data_variable_size
        adj_a = np.zeros((num_nodes, num_nodes))

        encoder = MLPEncoder(
            data_variable_size * self.CONFIG.x_dims,
            self.CONFIG.x_dims,
            self.CONFIG.encoder_hidden,
            int(self.CONFIG.z_dims),
            adj_a,
            batch_size=self.CONFIG.batch_size,
            do_prob=self.CONFIG.encoder_dropout,
            factor=self.CONFIG.factor,
        ).double()

        decoder = MLPDecoder(
            data_variable_size * self.CONFIG.x_dims,
            self.CONFIG.z_dims,
            self.CONFIG.x_dims,
            encoder,
            data_variable_size=data_variable_size,
            batch_size=self.CONFIG.batch_size,
            n_hid=self.CONFIG.decoder_hidden,
            do_prob=self.CONFIG.decoder_dropout,
        ).double()

        # ===================================
        # set up training parameters
        # ===================================
        optimizer = optim.Adam(
            list(encoder.parameters()) + list(decoder.parameters()), lr=self.CONFIG.lr
        )

        scheduler = lr_scheduler.StepLR(
            optimizer, step_size=self.CONFIG.lr_decay, gamma=self.CONFIG.gamma
        )

        # Linear indices of an upper triangular mx, used for acc calculation
        triu_indices = self.get_triu_offdiag_indices(data_variable_size)
        tril_indices = self.get_tril_offdiag_indices(data_variable_size)

        if self.CONFIG.cuda:
            encoder.cuda()
            decoder.cuda()
            triu_indices = triu_indices.cuda()
            tril_indices = tril_indices.cuda()

        # compute constraint h(A) value
        def _h_a(a, m):
            expm_a = self.matrix_poly(a * a, m)
            h_a = torch.trace(expm_a) - m
            return h_a

        prox_plus = torch.nn.Threshold(0.0, 0.0)

        def stau(w, tau):
            w1 = prox_plus(torch.abs(w) - tau)
            return torch.sign(w) * w1

        def update_optimizer(optimizer, original_lr, c_a):
            """related LR to c_A, whenever c_A gets big, reduce LR proportionally"""

            estimated_lr = original_lr / (math.log10(c_a) + 1e-10)
            if estimated_lr > MAX_LR:
                lr = MAX_LR
            elif estimated_lr < MIN_LR:
                lr = MIN_LR
            else:
                lr = estimated_lr

            # set LR
            for parame_group in optimizer.param_groups:
                parame_group["lr"] = lr

            return optimizer, lr

        # ===================================
        # training:
        # ===================================
        def train(epoch, best_val_loss, lambda_a, c_a, optimizer):
            time.time()
            nll_train = []
            kl_train = []
            mse_train = []

            encoder.train()
            decoder.train()
            scheduler.step()

            # update optimizer
            optimizer, lr = update_optimizer(optimizer, self.CONFIG.lr, c_a)

            for i in range(1):
                data_batch = train_data[
                    i * data_sample_size : (i + 1) * data_sample_size
                ]
                data_batch = torch.tensor(
                    data_batch.to_numpy().reshape(
                        data_sample_size, data_variable_size, 1
                    )
                )
                if self.CONFIG.cuda:
                    data_batch = data_batch.cuda()
                data_batch = Variable(data_batch).double()

                optimizer.zero_grad()

                (
                    enc_x,
                    logits,
                    origin_a,
                    adj_a_tilt_encoder,
                    z_gap,
                    z_positive,
                    my_a,
                    w_a,
                ) = encoder(data_batch)  # logits is of size: [num_sims, z_dims]
                edges = logits
                # print(origin_a)
                dec_x, output, adj_a_tilt_decoder = decoder(
                    data_batch,
                    edges,
                    data_variable_size * self.CONFIG.x_dims,
                    origin_a,
                    adj_a_tilt_encoder,
                    w_a,
                )

                if torch.sum(output != output):
                    print("nan error\n")

                target = data_batch
                preds = output
                variance = 0.0

                # reconstruction accuracy loss
                loss_nll = self.nll_gaussian(preds, target, variance)

                # KL loss
                loss_kl = self.kl_gaussian_sem(logits)

                # ELBO loss:
                loss = loss_kl + loss_nll
                # add A loss
                one_adj_a = origin_a  # torch.mean(adj_A_tilt_decoder, dim =0)
                sparse_loss = self.CONFIG.tau_a * torch.sum(torch.abs(one_adj_a))

                # other loss term
                if self.CONFIG.use_a_connect_loss:
                    connect_gap = self.a_connect_loss(
                        one_adj_a, self.CONFIG.graph_threshold, z_gap
                    )
                    loss += (
                        lambda_a * connect_gap + 0.5 * c_a * connect_gap * connect_gap
                    )

                if self.CONFIG.use_a_positiver_loss:
                    positive_gap = self.a_positive_loss(one_adj_a, z_positive)
                    loss += 0.1 * (
                        lambda_a * positive_gap
                        + 0.5 * c_a * positive_gap * positive_gap
                    )

                # compute h(A)
                h_a = _h_a(origin_a, data_variable_size)
                loss += (
                    lambda_a * h_a
                    + 0.5 * c_a * h_a * h_a
                    + 100.0 * torch.trace(origin_a * origin_a)
                    + sparse_loss
                )  # +  0.01 * torch.sum(variance * variance)

                # print(loss)
                loss.backward()
                loss = optimizer.step()

                my_a.data = stau(my_a.data, self.CONFIG.tau_a * lr)

                if torch.sum(origin_a != origin_a):
                    print("nan error\n")

                # compute metrics
                graph = origin_a.data.clone().cpu().numpy()
                graph[np.abs(graph) < self.CONFIG.graph_threshold] = 0

                mse_train.append(f.mse_loss(preds, target).item())
                nll_train.append(loss_nll.item())
                kl_train.append(loss_kl.item())

            return (
                np.mean(np.mean(kl_train) + np.mean(nll_train)),
                np.mean(nll_train),
                np.mean(mse_train),
                graph,
                origin_a,
            )

        # ===================================
        # main
        # ===================================

        # gamma = 0.5
        gamma = 0.25
        eta = 10

        best_elbo_loss = np.inf
        best_nll_loss = np.inf
        best_mse_loss = np.inf
        # optimizer step on hyparameters
        c_a = self.CONFIG.c_a
        lambda_a = self.CONFIG.lambda_a
        h_a_new = torch.tensor(1.0)
        h_tol = self.CONFIG.h_tol
        k_max_iter = int(self.CONFIG.k_max_iter)
        h_a_old = np.inf

        e_loss = []
        n_loss = []
        m_loss = []
        time.time()
        try:
            for _step_k in range(k_max_iter):
                # print(step_k)
                while c_a < 1e20:
                    for epoch in range(self.CONFIG.epochs):
                        # print(epoch)
                        elbo_loss, nll_loss, mse_loss, graph, origin_a = train(
                            epoch, best_elbo_loss, lambda_a, c_a, optimizer
                        )
                        # print(f"{elbo_loss=} {NLL_loss=} {MSE_loss=}")
                        e_loss.append(elbo_loss)
                        n_loss.append(nll_loss)
                        m_loss.append(mse_loss)
                        if elbo_loss < best_elbo_loss:
                            best_elbo_loss = elbo_loss

                        if nll_loss < best_nll_loss:
                            best_nll_loss = nll_loss

                        if mse_loss < best_mse_loss:
                            best_mse_loss = mse_loss

                    # print("Optimization Finished!")
                    # print("Best Epoch: {:04d}".format(best_epoch))
                    if elbo_loss > 2 * best_elbo_loss:
                        break

                    # update parameters
                    a_new = origin_a.data.clone()
                    h_a_new = _h_a(a_new, data_variable_size)
                    if h_a_new.item() > gamma * h_a_old:
                        c_a *= eta
                    else:
                        break

                # update parameters
                # h_A, adj_A are computed in loss anyway, so no need to store
                h_a_old = h_a_new.item()
                lambda_a += c_a * h_a_new.item()

                if h_a_new.item() <= h_tol:
                    break

            graph = origin_a.data.clone().cpu().numpy()
            graph[np.abs(graph) < 0.1] = 0
            graph[np.abs(graph) < 0.2] = 0
            graph[np.abs(graph) < 0.3] = 0

        except KeyboardInterrupt:
            print("Done!")

        adj = graph
        adj = np.abs(adj.T)
        # n = np.count_nonzero(adj)
        # print(f"There are {n} edges in the graph")

        # PageRank
        try:
            pagerank = PageRank()
            scores = pagerank.fit_transform(np.abs(adj.T))
        except Exception:  # empty graph
            # print("empty graph")
            # Return all nodes with equal scores if graph is empty
            equal_score = 1.0 / len(node_names) if node_names else 0.0
            return [(node, equal_score) for node in node_names[:top_k]]

        # merge scores and node names, sort by scores
        ranks = list(zip(node_names, scores, strict=False))
        ranks.sort(key=lambda x: x[1], reverse=True)

        # Convert to the expected return format (list of tuples with scores)
        result = []
        for _, (node, score) in enumerate(ranks[:top_k]):
            result.append((node, score))

        return result

    def _create_config(self):
        """Create and return a CONFIG-like object with app parameters."""

        class Config:
            def __init__(self):
                pass

            # Epochs
            epochs = 500

            # Batch size (note: should be divisible by sample size, otherwise throw an error)
            batch_size = 50

            # Learning rate (baseline rate = 1e-3)
            lr = 1e-3

            x_dims = 1
            z_dims = 1
            # data_variable_size = 12
            optimizer = "Adam"
            graph_threshold = 0.3
            tau_a = 0.0
            lambda_a = 0.0
            c_a = 1
            use_a_connect_loss = 0
            use_a_positiver_loss = 0
            # no_cuda = True
            seed = 42
            encoder_hidden = 64
            decoder_hidden = 64
            temp = 0.5
            k_max_iter = 1e2
            encoder = "mlp"
            decoder = "mlp"
            no_factor = False
            encoder_dropout = 0.0
            decoder_dropout = (0.0,)
            h_tol = 1e-8
            lr_decay = 200
            gamma = 1.0
            prior = False

        config = Config()
        config.cuda = torch.cuda.is_available()
        config.factor = not config.no_factor
        return config

    # ========================================
    # VAE utility functions (as methods)
    # ========================================
    def get_triu_indices(self, num_nodes):  # NOTE
        """Linear triu (upper triangular) indices."""
        ones = torch.ones(num_nodes, num_nodes)
        eye = torch.eye(num_nodes, num_nodes)
        triu_indices = (ones.triu() - eye).nonzero().t()
        triu_indices = triu_indices[0] * num_nodes + triu_indices[1]
        return triu_indices

    def get_tril_indices(self, num_nodes):  # NOTE
        """Linear tril (lower triangular) indices."""
        ones = torch.ones(num_nodes, num_nodes)
        eye = torch.eye(num_nodes, num_nodes)
        tril_indices = (ones.tril() - eye).nonzero().t()
        tril_indices = tril_indices[0] * num_nodes + tril_indices[1]
        return tril_indices

    def get_offdiag_indices(self, num_nodes):  # NOTE
        """Linear off-diagonal indices."""
        ones = torch.ones(num_nodes, num_nodes)
        eye = torch.eye(num_nodes, num_nodes)
        offdiag_indices = (ones - eye).nonzero().t()
        offdiag_indices = offdiag_indices[0] * num_nodes + offdiag_indices[1]
        return offdiag_indices

    def get_triu_offdiag_indices(self, num_nodes):  # NOTE
        """Linear triu (upper) indices w.r.t. vector of off-diagonal elements."""
        triu_idx = torch.zeros(num_nodes * num_nodes)
        triu_idx[self.get_triu_indices(num_nodes)] = 1.0
        triu_idx = triu_idx[self.get_offdiag_indices(num_nodes)]
        return triu_idx.nonzero()

    def get_tril_offdiag_indices(self, num_nodes):  # NOTE
        """Linear tril (lower) indices w.r.t. vector of off-diagonal elements."""
        tril_idx = torch.zeros(num_nodes * num_nodes)
        tril_idx[self.get_tril_indices(num_nodes)] = 1.0
        tril_idx = tril_idx[self.get_offdiag_indices(num_nodes)]
        return tril_idx.nonzero()

    def kl_gaussian_sem(self, preds):  # NOTE
        mu = preds
        kl_div = mu * mu
        kl_sum = kl_div.sum()
        return (kl_sum / (preds.size(0))) * 0.5

    def nll_gaussian(self, preds, target, variance, add_const=False):  # NOTE
        mean1 = preds
        mean2 = target
        neg_log_p = variance + torch.div(
            torch.pow(mean1 - mean2, 2), 2.0 * np.exp(2.0 * variance)
        )
        if add_const:
            const = 0.5 * torch.log(2 * torch.from_numpy(np.pi) * variance)
            neg_log_p += const
        return neg_log_p.sum() / (target.size(0))

    def preprocess_adj_new(self, adj):  # NOTE
        if self.CONFIG.cuda:
            adj_normalized = torch.eye(adj.shape[0]).double().cuda() - (
                adj.transpose(0, 1)
            )
        else:
            adj_normalized = torch.eye(adj.shape[0]).double() - (adj.transpose(0, 1))
        return adj_normalized

    def preprocess_adj_new1(self, adj):  # NOTE
        if self.CONFIG.cuda:
            adj_normalized = torch.inverse(
                torch.eye(adj.shape[0]).double().cuda() - adj.transpose(0, 1)
            )
        else:
            adj_normalized = torch.inverse(
                torch.eye(adj.shape[0]).double() - adj.transpose(0, 1)
            )
        return adj_normalized

    def isnan(self, x):  # NOTE
        return x != x

    def matrix_poly(self, matrix, d):  # NOTE
        if self.CONFIG.cuda:
            x = torch.eye(d).double().cuda() + torch.div(matrix, d)
        else:
            x = torch.eye(d).double() + torch.div(matrix, d)
        return torch.matrix_power(x, d)

    # matrix loss: makes sure at least A connected to another parents for child
    def a_connect_loss(self, a, tol, z):  # NOTE
        d = a.size()[0]
        loss = 0
        for i in range(d):
            loss += (
                2 * tol
                - torch.sum(torch.abs(a[:, i]))
                - torch.sum(torch.abs(a[i, :]))
                + z * z
            )
        return loss

    # element loss: make sure each A_ij > 0
    def a_positive_loss(self, a, z_positive):  # NOTE
        result = -a + z_positive * z_positive
        loss = torch.sum(result)

        return loss
