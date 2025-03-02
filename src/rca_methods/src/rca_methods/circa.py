from rca_methods.e2e import rca
from rca_methods.graph_construction.pc import pc_default
from rca_methods.graph_heads.rht import rht
from rca_methods.io.time_series import (
    preprocess,
)


@rca
def circa(data, inject_time=None, dataset=None, **kwargs):
    time_col = data["time"]

    data = preprocess(
        data=data,
        dataset=dataset,
        dk_select_useful=kwargs.get("dk_select_useful", False),
    )

    # add time again
    data["time"] = time_col

    # graph construction
    pc_input = data.drop(columns=["time"])
    pc_input.columns.to_list()

    adj = pc_default(pc_input, dataset="ob")
    ranks = rht(adj, inject_time, data)
    ranks = sorted(ranks, key=lambda x: x[1], reverse=True)
    ranks = [x[0] for x in ranks]
    return {
        "adj": adj,
        "node_names": data.columns.to_list(),
        "ranks": ranks,
    }
