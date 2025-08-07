from copy import deepcopy

import numpy as np
import pandas as pd
import torch
import torch.nn as nn


def activation_helper(activation: str | None, dim: int | None = None):
    """Helper function to get an activation function.

    Args:
        activation (str | None): Name of the activation function (e.g., "sigmoid", "tanh", "relu", "leakyrelu"). If None, returns an identity function.
        dim (int | None, optional): Dimension for some activations (not used here). Defaults to None.

    Returns:
        torch.nn.Module: The activation function.

    Raises:
        ValueError: If an unsupported activation is provided.
    """
    if activation == "sigmoid":
        act = nn.Sigmoid()
    elif activation == "tanh":
        act = nn.Tanh()
    elif activation == "relu":
        act = nn.ReLU()
    elif activation == "leakyrelu":
        act = nn.LeakyReLU()
    elif activation is None:

        def act(x):
            return x

    else:
        raise ValueError(f"unsupported activation: {activation}")
    return act


class MLP(nn.Module):
    """A Multi-Layer Perceptron (MLP) module."""

    def __init__(self, num_series: int, lag: int, hidden: list[int], activation: str):
        """Initialize the MLP.

        Args:
            num_series (int): Number of time series.
            lag (int): Number of previous time points to use in prediction.
            hidden (list[int]): List of number of hidden units per layer.
            activation (str): Nonlinearity at each layer.
        """
        super().__init__()
        self.activation = activation_helper(activation)

        # Set up network.
        layer = nn.Conv1d(num_series, hidden[0], lag)
        modules = [layer]

        for d_in, d_out in zip(hidden, [*hidden[1:], 1], strict=False):
            layer = nn.Conv1d(d_in, d_out, 1)
            modules.append(layer)

        # Register parameters.
        self.layers = nn.ModuleList(modules)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform forward pass.

        Args:
            x (torch.Tensor): Torch tensor of shape (batch, T, p).

        Returns:
            torch.Tensor: Output tensor of shape (batch, T - lag + 1, 1).
        """
        x = x.transpose(2, 1)
        for i, fc in enumerate(self.layers):
            if i != 0:
                x = self.activation(x)
            x = fc(x)

        return x.transpose(2, 1)


class CMlp(nn.Module):
    """CMLP model with one MLP per time series."""

    def __init__(
        self, num_series: int, lag: int, hidden: list[int], activation: str = "relu"
    ):
        """Initialize the CMlp model.

        Args:
            num_series (int): Dimensionality of multivariate time series.
            lag (int): Number of previous time points to use in prediction.
            hidden (list[int]): List of number of hidden units per layer.
            activation (str, optional): Nonlinearity at each layer. Defaults to "relu".
        """
        super().__init__()
        self.p = num_series
        self.lag = lag
        self.activation = activation_helper(activation)

        # Set up networks.
        self.networks = nn.ModuleList(
            [MLP(num_series, lag, hidden, activation) for _ in range(num_series)]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform forward pass.

        Args:
            x (torch.Tensor): Torch tensor of shape (batch, T, p).

        Returns:
            torch.Tensor: Output tensor of shape (batch, T - lag + 1, p).
        """
        return torch.cat([network(x) for network in self.networks], dim=2)

    def gc(self, threshold: bool = True, ignore_lag: bool = True) -> torch.Tensor:
        """Extract learned Granger causality.

        Args:
            threshold (bool, optional): If True, returns whether norm is nonzero. Otherwise, returns norm of weights. Defaults to True.
            ignore_lag (bool, optional): If True, calculates norm of weights jointly for all lags. Defaults to True.

        Returns:
            torch.Tensor: (p x p) or (p x p x lag) matrix. In first case, entry (i, j)
                indicates whether variable j is Granger causal of variable i. In
                second case, entry (i, j, k) indicates whether it's Granger causal
                at lag k.
        """
        if ignore_lag:
            return_gc = [
                torch.norm(net.layers[0].weight, dim=(0, 2)) for net in self.networks
            ]
        else:
            return_gc = [
                torch.norm(net.layers[0].weight, dim=0) for net in self.networks
            ]
        return_gc = torch.stack(return_gc)
        if threshold:
            return (return_gc > 0).int()
        else:
            return return_gc


class CMlpSparse(nn.Module):
    """cMLP model that only uses specified interactions."""

    def __init__(
        self,
        num_series: int,
        sparsity: torch.Tensor,
        lag: int,
        hidden: list[int],
        activation: str = "relu",
    ):
        """Initialize the CMlpSparse model.

        Args:
            num_series (int): Dimensionality of multivariate time series.
            sparsity (torch.Tensor): Torch byte tensor indicating Granger causality, with size (num_series, num_series).
            lag (int): Number of previous time points to use in prediction.
            hidden (list[int]): List of number of hidden units per layer.
            activation (str, optional): Nonlinearity at each layer. Defaults to "relu".
        """
        super().__init__()
        self.p = num_series
        self.lag = lag
        self.activation = activation_helper(activation)
        self.sparsity = sparsity

        # Set up networks.
        self.networks = []
        for i in range(num_series):
            num_inputs = int(torch.sum(sparsity[i].int()))
            self.networks.append(MLP(num_inputs, lag, hidden, activation))

        # Register parameters.
        param_list = []
        for i in range(num_series):
            param_list += list(self.networks[i].parameters())
        self.param_list = nn.ParameterList(param_list)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Perform forward pass.

        Args:
            x (torch.Tensor): Torch tensor of shape (batch, T, p).

        Returns:
            torch.Tensor: Output tensor.
        """
        return torch.cat(
            [self.networks[i](x[:, :, self.sparsity[i]]) for i in range(self.p)], dim=2
        )


def prox_update(network: MLP, lam: float, lr: float, penalty: str):
    """Perform in place proximal update on first layer weight matrix.

    Args:
        network (MLP): MLP network.
        lam (float): Regularization parameter.
        lr (float): Learning rate.
        penalty (str): Type of nonsmooth regularization (e.g., "GL", "GSGL", "H").
    """
    w = network.layers[0].weight
    hidden, p, lag = w.shape
    if penalty == "GL":
        norm = torch.norm(w, dim=(0, 2), keepdim=True)
        w.data = (w / torch.clamp(norm, min=(lr * lam))) * torch.clamp(
            norm - (lr * lam), min=0.0
        )
    elif penalty == "GSGL":
        norm = torch.norm(w, dim=0, keepdim=True)
        w.data = (w / torch.clamp(norm, min=(lr * lam))) * torch.clamp(
            norm - (lr * lam), min=0.0
        )
        norm = torch.norm(w, dim=(0, 2), keepdim=True)
        w.data = (w / torch.clamp(norm, min=(lr * lam))) * torch.clamp(
            norm - (lr * lam), min=0.0
        )
    elif penalty == "H":
        # Lowest indices along third axis touch most lagged values.
        for i in range(lag):
            norm = torch.norm(w[:, :, : (i + 1)], dim=(0, 2), keepdim=True)
            w.data[:, :, : (i + 1)] = (
                w.data[:, :, : (i + 1)] / torch.clamp(norm, min=(lr * lam))
            ) * torch.clamp(norm - (lr * lam), min=0.0)
    else:
        raise ValueError(f"unsupported penalty: {penalty}")


def regularize(network: MLP, lam: float, penalty: str) -> torch.Tensor:
    """Calculate regularization term for first layer weight matrix.

    Args:
        network (MLP): MLP network.
        lam (float): Regularization parameter.
        penalty (str): Type of nonsmooth regularization (e.g., "GL", "GSGL", "H").

    Returns:
        torch.Tensor: The regularization term.
    """
    w = network.layers[0].weight
    hidden, p, lag = w.shape
    if penalty == "GL":
        return lam * torch.sum(torch.norm(w, dim=(0, 2)))
    elif penalty == "GSGL":
        return lam * (
            torch.sum(torch.norm(w, dim=(0, 2))) + torch.sum(torch.norm(w, dim=0))
        )
    elif penalty == "H":
        # Lowest indices along third axis touch most lagged values.
        return lam * sum(
            [torch.sum(torch.norm(w[:, :, : (i + 1)], dim=(0, 2))) for i in range(lag)]
        )
    else:
        raise ValueError(f"unsupported penalty: {penalty}")


def ridge_regularize(network: MLP, lam: float) -> torch.Tensor:
    """Apply ridge penalty at all subsequent layers."""
    return lam * sum([torch.sum(fc.weight**2) for fc in network.layers[1:]])


def restore_parameters(model: nn.Module, best_model: nn.Module):
    """Move parameter values from best_model to model."""
    for params, best_params in zip(
        model.parameters(), best_model.parameters(), strict=False
    ):
        params.data = best_params


def train_model_gista(
    cmlp: CMlp,
    x: torch.Tensor,
    lam: float,
    lam_ridge: float,
    lr: float,
    penalty: str,
    max_iter: int,
    check_every: int = 100,
    r: float = 0.8,
    lr_min: float = 1e-8,
    sigma: float = 0.5,
    monotone: bool = False,
    m: int = 10,
    lr_decay: float = 0.5,
    begin_line_search: bool = True,
    switch_tol: float = 1e-3,
    verbose: int = 1,
) -> tuple[list[torch.Tensor], list[torch.Tensor]]:
    """Train cMLP model with GISTA.

    Args:
        cmlp (CMlp): cmlp model.
        x (torch.Tensor): Tensor of data, shape (batch, T, p).
        lam (float): Parameter for nonsmooth regularization.
        lam_ridge (float): Parameter for ridge regularization on output layer.
        lr (float): Learning rate.
        penalty (str): Type of nonsmooth regularization.
        max_iter (int): Max number of GISTA iterations.
        check_every (int, optional): How frequently to record loss. Defaults to 100.
        r (float, optional): For line search. Defaults to 0.8.
        lr_min (float, optional): For line search. Defaults to 1e-8.
        sigma (float, optional): For line search. Defaults to 0.5.
        monotone (bool, optional): For line search. Defaults to False.
        m (int, optional): For line search. Defaults to 10.
        lr_decay (float, optional): For adjusting initial learning rate of line search. Defaults to 0.5.
        begin_line_search (bool, optional): Whether to begin with line search. Defaults to True.
        switch_tol (float, optional): Tolerance for switching to line search. Defaults to 1e-3.
        verbose (int, optional): Level of verbosity (0, 1, 2). Defaults to 1.

    Returns:
        tuple[list[torch.Tensor], list[torch.Tensor]]: A tuple containing lists of training loss and MSE.
    """
    p = cmlp.p
    lag = cmlp.lag
    cmlp_copy = deepcopy(cmlp)
    loss_fn = nn.MSELoss(reduction="mean")
    lr_list = [lr for _ in range(p)]

    # Calculate full loss.
    mse_list = []
    smooth_list = []
    loss_list = []
    for i in range(p):
        net = cmlp.networks[i]
        mse = loss_fn(net(x[:, :-1]), x[:, lag:, i : i + 1])
        ridge = ridge_regularize(net, lam_ridge)
        smooth = mse + ridge
        mse_list.append(mse)
        smooth_list.append(smooth)
        with torch.no_grad():
            nonsmooth = regularize(net, lam, penalty)
            loss = smooth + nonsmooth
            loss_list.append(loss)

    # Set up lists for loss and mse.
    with torch.no_grad():
        loss_mean = sum(loss_list) / p
        mse_mean = sum(mse_list) / p
    train_loss_list = [loss_mean]
    train_mse_list = [mse_mean]

    # For switching to line search.
    line_search = begin_line_search

    # For line search criterion.
    done = [False for _ in range(p)]
    assert 0 < sigma <= 1
    assert m > 0
    if not monotone:
        last_losses = [[loss_list[i]] for i in range(p)]

    for it in range(max_iter):
        # Backpropagate errors.
        sum([smooth_list[i] for i in range(p) if not done[i]]).backward()

        # For next iteration.
        new_mse_list = []
        new_smooth_list = []
        new_loss_list = []

        # Perform GISTA step for each network.
        for i in range(p):
            # Skip if network converged.
            if done[i]:
                new_mse_list.append(mse_list[i])
                new_smooth_list.append(smooth_list[i])
                new_loss_list.append(loss_list[i])
                continue

            # Prepare for line search.
            step = False
            lr_it = lr_list[i]
            net = cmlp.networks[i]
            net_copy = cmlp_copy.networks[i]

            while not step:
                # Perform tentative ISTA step.
                for param, temp_param in zip(
                    net.parameters(), net_copy.parameters(), strict=False
                ):
                    temp_param.data = param - lr_it * param.grad

                # Proximal update.
                prox_update(net_copy, lam, lr_it, penalty)

                # Check line search criterion.
                mse = loss_fn(net_copy(x[:, :-1]), x[:, lag:, i : i + 1])
                ridge = ridge_regularize(net_copy, lam_ridge)
                smooth = mse + ridge
                with torch.no_grad():
                    nonsmooth = regularize(net_copy, lam, penalty)
                    loss = smooth + nonsmooth
                    tol = (0.5 * sigma / lr_it) * sum(
                        [
                            torch.sum((param - temp_param) ** 2)
                            for param, temp_param in zip(
                                net.parameters(), net_copy.parameters(), strict=False
                            )
                        ]
                    )

                comp = loss_list[i] if monotone else max(last_losses[i])
                if not line_search or (comp - loss) > tol:
                    step = True
                    if verbose > 1:
                        print(f"Taking step, network i = {i}, lr = {lr_it}")
                        print(f"Gap = {comp - loss:f}, tol = {tol:f}")

                    # For next iteration.
                    new_mse_list.append(mse)
                    new_smooth_list.append(smooth)
                    new_loss_list.append(loss)

                    # Adjust initial learning rate.
                    lr_list[i] = (lr_list[i] ** (1 - lr_decay)) * (lr_it**lr_decay)

                    if not monotone:
                        if len(last_losses[i]) == m:
                            last_losses[i].pop(0)
                        last_losses[i].append(loss)
                else:
                    # Reduce learning rate.
                    lr_it *= r
                    if lr_it < lr_min:
                        done[i] = True
                        new_mse_list.append(mse_list[i])
                        new_smooth_list.append(smooth_list[i])
                        new_loss_list.append(loss_list[i])
                        if verbose > 0:
                            print(f"Network {i + 1} converged")
                        break

            # Clean up.
            net.zero_grad()

            if step:
                # Swap network parameters.
                cmlp.networks[i], cmlp_copy.networks[i] = net_copy, net

        # For next iteration.
        mse_list = new_mse_list
        smooth_list = new_smooth_list
        loss_list = new_loss_list

        # Check if all networks have converged.
        if sum(done) == p:
            if verbose > 0:
                print(f"Done at iteration = {it + 1}")
            break

        # Check progress.
        if (it + 1) % check_every == 0:
            with torch.no_grad():
                loss_mean = sum(loss_list) / p
                mse_mean = sum(mse_list) / p
                ridge_mean = (sum(smooth_list) - sum(mse_list)) / p
                nonsmooth_mean = (sum(loss_list) - sum(smooth_list)) / p

            train_loss_list.append(loss_mean)
            train_mse_list.append(mse_mean)

            if verbose > 0:
                print(("-" * 10 + "Iter = %d" + "-" * 10) % (it + 1))
                print(f"Total loss = {loss_mean:f}")
                print(
                    f"MSE = {mse_mean:f}, Ridge = {ridge_mean:f}, Nonsmooth = {nonsmooth_mean:f}"
                )
                print("Variable usage = %.2f%%" % (100 * torch.mean(cmlp.GC().float())))

            # Check whether loss has increased.
            if not line_search:
                if train_loss_list[-2] - train_loss_list[-1] < switch_tol:
                    line_search = True
                    if verbose > 0:
                        print("Switching to line search")

    return train_loss_list, train_mse_list


def train_model_adam(
    cmlp: CMlp,
    x: torch.Tensor,
    lr: float,
    max_iter: int,
    lam: float = 0,
    lam_ridge: float = 0,
    penalty: str = "H",
    lookback: int = 5,
    check_every: int = 100,
    verbose: int = 1,
) -> list[torch.Tensor]:
    """Train model with Adam optimizer.

    Args:
        cmlp (CMlp): cmlp model.
        x (torch.Tensor): Tensor of data, shape (batch, T, p).
        lr (float): Learning rate.
        max_iter (int): Max number of iterations.
        lam (float, optional): Parameter for nonsmooth regularization. Defaults to 0.
        lam_ridge (float, optional): Parameter for ridge regularization on output layer. Defaults to 0.
        penalty (str, optional): Type of nonsmooth regularization. Defaults to "H".
        lookback (int, optional): For early stopping. Defaults to 5.
        check_every (int, optional): How frequently to record loss. Defaults to 100.
        verbose (int, optional): Level of verbosity (0, 1, 2). Defaults to 1.

    Returns:
        list[torch.Tensor]: A list of training losses.
    """
    lag = cmlp.lag
    p = x.shape[-1]
    loss_fn = nn.MSELoss(reduction="mean")
    optimizer = torch.optim.Adam(cmlp.parameters(), lr=lr)
    train_loss_list = []

    # For early stopping.
    best_it = None
    best_loss = np.inf
    best_model = None

    for it in range(max_iter):
        # Calculate loss.
        loss = sum(
            [
                loss_fn(cmlp.networks[i](x[:, :-1]), x[:, lag:, i : i + 1])
                for i in range(p)
            ]
        )

        # Add penalty terms.
        if lam > 0:
            loss = loss + sum([regularize(net, lam, penalty) for net in cmlp.networks])
        if lam_ridge > 0:
            loss = loss + sum(
                [ridge_regularize(net, lam_ridge) for net in cmlp.networks]
            )

        # Take gradient step.
        loss.backward()
        optimizer.step()
        cmlp.zero_grad()

        # Check progress.
        if (it + 1) % check_every == 0:
            mean_loss = loss / p
            train_loss_list.append(mean_loss.detach())

            if verbose > 0:
                print(("-" * 10 + "Iter = %d" + "-" * 10) % (it + 1))
                print(f"Loss = {mean_loss:f}")

            # Check for early stopping.
            if mean_loss < best_loss:
                best_loss = mean_loss
                best_it = it
                best_model = deepcopy(cmlp)
            elif (it - best_it) == lookback * check_every:
                if verbose:
                    print("Stopping early")
                break

    # Restore best model.
    restore_parameters(cmlp, best_model)

    return train_loss_list


def train_model_ista(
    cmlp: CMlp,
    x: torch.Tensor,
    lr: float,
    max_iter: int,
    lam: float = 0,
    lam_ridge: float = 0,
    penalty: str = "H",
    lookback: int = 5,
    check_every: int = 100,
    verbose: int = 1,
) -> list[torch.Tensor]:
    """Train model with ISTA (Iterative Soft-Thresholding Algorithm).

    Args:
        cmlp (CMlp): cmlp model.
        x (torch.Tensor): Tensor of data, shape (batch, T, p).
        lr (float): Learning rate.
        max_iter (int): Max number of iterations.
        lam (float, optional): Parameter for nonsmooth regularization. Defaults to 0.
        lam_ridge (float, optional): Parameter for ridge regularization on output layer. Defaults to 0.
        penalty (str, optional): Type of nonsmooth regularization. Defaults to "H".
        lookback (int, optional): For early stopping. Defaults to 5.
        check_every (int, optional): How frequently to record loss. Defaults to 100.
        verbose (int, optional): Level of verbosity (0, 1, 2). Defaults to 1.

    Returns:
        list[torch.Tensor]: A list of training losses.
    """
    lag = cmlp.lag
    p = x.shape[-1]
    loss_fn = nn.MSELoss(reduction="mean")
    train_loss_list = []

    # For early stopping.
    best_it = None
    best_loss = np.inf
    best_model = None

    # Calculate smooth error.
    loss = sum(
        [loss_fn(cmlp.networks[i](x[:, :-1]), x[:, lag:, i : i + 1]) for i in range(p)]
    )
    ridge = sum([ridge_regularize(net, lam_ridge) for net in cmlp.networks])
    smooth = loss + ridge

    for it in range(max_iter):
        # Take gradient step.
        smooth.backward()
        for param in cmlp.parameters():
            param.data = param - lr * param.grad

        # Take prox step.
        if lam > 0:
            for net in cmlp.networks:
                prox_update(net, lam, lr, penalty)

        cmlp.zero_grad()

        # Calculate loss for next iteration.
        loss = sum(
            [
                loss_fn(cmlp.networks[i](x[:, :-1]), x[:, lag:, i : i + 1])
                for i in range(p)
            ]
        )
        ridge = sum([ridge_regularize(net, lam_ridge) for net in cmlp.networks])
        smooth = loss + ridge

        # Check progress.
        if (it + 1) % check_every == 0:
            # Add nonsmooth penalty.
            nonsmooth = sum([regularize(net, lam, penalty) for net in cmlp.networks])
            mean_loss = (smooth + nonsmooth) / p
            train_loss_list.append(mean_loss.detach())

            if verbose > 0:
                print(("-" * 10 + "Iter = %d" + "-" * 10) % (it + 1))
                print(f"Loss = {mean_loss:f}")
                print("Variable usage = %.2f%%" % (100 * torch.mean(cmlp.GC().float())))

            # Check for early stopping.
            if mean_loss < best_loss:
                best_loss = mean_loss
                best_it = it
                best_model = deepcopy(cmlp)
            elif (it - best_it) == lookback * check_every:
                if verbose:
                    print("Stopping early")
                break

    # Restore best model.
    restore_parameters(cmlp, best_model)

    return train_loss_list


def train_unregularized(
    cmlp: CMlp,
    x: torch.Tensor,
    lr: float,
    max_iter: int,
    lookback: int = 5,
    check_every: int = 100,
    verbose: int = 1,
) -> list[torch.Tensor]:
    """Train model with Adam and no regularization."""
    lag = cmlp.lag
    p = x.shape[-1]
    loss_fn = nn.MSELoss(reduction="mean")
    optimizer = torch.optim.Adam(cmlp.parameters(), lr=lr)
    train_loss_list = []

    # For early stopping.
    best_it = None
    best_loss = np.inf
    best_model = None

    for it in range(max_iter):
        # Calculate loss.
        pred = cmlp(x[:, :-1])
        loss = sum([loss_fn(pred[:, :, i], x[:, lag:, i]) for i in range(p)])

        # Take gradient step.
        loss.backward()
        optimizer.step()
        cmlp.zero_grad()

        # Check progress.
        if (it + 1) % check_every == 0:
            mean_loss = loss / p
            train_loss_list.append(mean_loss.detach())

            if verbose > 0:
                print(("-" * 10 + "Iter = %d" + "-" * 10) % (it + 1))
                print(f"Loss = {mean_loss:f}")

            # Check for early stopping.
            if mean_loss < best_loss:
                best_loss = mean_loss
                best_it = it
                best_model = deepcopy(cmlp)
            elif (it - best_it) == lookback * check_every:
                if verbose:
                    print("Stopping early")
                break

    # Restore best model.
    restore_parameters(cmlp, best_model)

    return train_loss_list


def cmlp(data: pd.DataFrame, max_iter: int | None = None) -> np.ndarray:
    """Runs the CMLP (Causal Multi-Layer Perceptron) model for causal discovery.

    Args:
        data (pd.DataFrame): The input time series data.
        max_iter (int | None, optional): Maximum number of iterations for training. Defaults to 50000.

    Returns:
        np.ndarray: The estimated Granger causality matrix (adjacency matrix).
    """
    if max_iter is None:
        max_iter = 50000

    data.columns.to_list()
    # fill nan by ffill
    data = data.fillna(method="ffill")
    data = data.to_numpy().astype(float)
    device = torch.device("cpu")

    # x = torch.tensor(data[np.newaxis], dtype=torch.float32, device=device).double()
    x = torch.tensor(data[np.newaxis], dtype=torch.float32, device=device)
    # cmlp = cMLP(x.shape[-1], lag=5, hidden=[100]).cuda(device=device)
    cmlp = CMlp(x.shape[-1], lag=5, hidden=[100]).to(device)

    train_model_ista(
        cmlp,
        x,
        lam=0.002,
        lam_ridge=1e-2,
        lr=5e-2,
        penalty="H",
        max_iter=max_iter,
        check_every=1000,
    )

    gc_est = cmlp.gc().cpu().data.numpy().astype(bool).astype(int)
    return gc_est
