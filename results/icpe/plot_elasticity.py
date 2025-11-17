import matplotlib.pyplot as plt

elastic_vals = ["CPU 50%", "CPU 70%", "CPU 50%\n+ Memory"]

line_styles = ["-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 1))]

coarse = {
    "CPU": {
        "BARO": [1.0, 0.958, 0.917],
        "CausalAI": [0.875, 0.694, 0.819],
        "CausalRCA": [1.0, 1.0, 1.0],
        "Circa": [0.244, 0.44, 0.201],
        "CloudRanger": [0.44, 0.7, 0.544],
    },
    "MEM": {
        "BARO": [0.958, 0.875, 1.0],
        "CausalAI": [0.892, 0.667, 0.847],
        "CausalRCA": [1.0, 1.0, 1.0],
        "Circa": [0.243, 0.5, 0.299],
        "CloudRanger": [0.306, 0.179, 0.424],
    },
    "DELAY": {
        "BARO": [0.958, 1.0, 0.909],
        "CausalAI": [0.778, 0.694, 0.932],
        "CausalRCA": [1.0, 1.0, 1.0],
        "Circa": [0.385, 0.183, 0.339],
        "CloudRanger": [0.381, 0.406, 0.614],
    },
}

fine = {
    "CPU": {
        "BARO": [0.764, 0.736, 0.708],
        "CausalAI": [0.083, 0.042, 0.0],
        "CausalRCA": [0.508, 0.508, 0.508],
        "Circa": [0.0, 0.0, 0.0],
        "CloudRanger": [0.44, 0.6, 0.431],
    },
    "MEM": {
        "BARO": [0.958, 0.812, 0.792],
        "CausalAI": [0.167, 0.086, 0.167],
        "CausalRCA": [0.0, 0.0, 0.0],
        "Circa": [0.0, 0.0, 0.0],
        "CloudRanger": [0.128, 0.037, 0.271],
    },
    "DELAY": {
        "BARO": [0.958, 0.819, 0.864],
        "CausalAI": [0.042, 0.028, 0.045],
        "CausalRCA": [0.0, 0.0, 0.0],
        "Circa": [0.385, 0.183, 0.339],
        "CloudRanger": [0.274, 0.11, 0.218],
    },
}

plt.rcParams.update(
    {
        "font.size": 10,
        "axes.labelsize": 14,
        "axes.titlesize": 14,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 8,
        "lines.linewidth": 1.5,
        "lines.markersize": 5,
    }
)

fig, axes = plt.subplots(2, 3, figsize=(7, 5), sharex=True, sharey=True)
metrics = ["CPU", "MEM", "DELAY"]

for i, metric in enumerate(metrics):
    for idx, (method, vals) in enumerate(coarse[metric].items()):
        axes[0, i].plot(
            elastic_vals, vals, marker="o", linestyle=line_styles[idx], label=method
        )
    axes[0, i].set_title(f"Coarse - {metric}")
    axes[0, i].set_xticks(elastic_vals)

    for idx, (method, vals) in enumerate(fine[metric].items()):
        axes[1, i].plot(
            elastic_vals, vals, marker="o", linestyle=line_styles[idx], label=method
        )
    axes[1, i].set_title(f"Fine - {metric}")
    axes[1, i].set_xticks(elastic_vals)

axes[1, 1].set_xlabel("Elasticity")
axes[1, 0].set_ylabel("MRR")
axes[0, 0].set_ylabel("MRR")
axes[1, 1].legend(loc="center")
plt.tight_layout()
plt.savefig("elasticity_effect_mrr.pdf")
