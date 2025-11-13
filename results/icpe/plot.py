import matplotlib.pyplot as plt

msi = [1, 3, 5, 15, 30]

coarse = {
    "CPU": {
        "BARO": [0.958, 1.0, 1.0, 0.917, 1.0],
        "CausalAI": [0.806, 0.75, 0.792, 0.778, 0.694],
        "CausalRCA": [1, 1, 1, 1, 1],
        "Circa": [0.444, 0.326, 0.297, 0.489, 0.294],
        "CloudRanger": [0.472, 0.569, 0.486, 0.576, 0.621],
    },
    "MEM": {
        "BARO": [0.958, 0.958, 1.0, 0.875, 0.875],
        "CausalAI": [0.771, 0.764, 0.681, 0.778, 0.764],
        "CausalRCA": [1, 1, 1, 1, 1],
        "Circa": [0.431, 0.278, 0.276, 0.267, 0.221],
        "CloudRanger": [0.361, 0.408, 0.263, 0.383, 0.3],
    },
    "DELAY": {
        "BARO": [0.958, 0.958, 1.0, 1.0, 0.875],
        "CausalAI": [0.611, 0.708, 0.625, 0.681, 0.729],
        "CausalRCA": [1, 1, 1, 1, 1],
        "Circa": [0.442, 0.346, 0.311, 0.29, 0.339],
        "CloudRanger": [0.485, 0.639, 0.572, 0.451, 0.669],
    },
}

fine = {
    "CPU": {
        "BARO": [0.792, 0.775, 0.75, 0.708, 0.819],
        "CausalAI": [0.0, 0.111, 0.0, 0.0, 0.0],
        "CausalRCA": [0.508, 0.508, 0.508, 0.508, 0.508],
        "Circa": [0.0, 0.0, 0.0, 0.0, 0.0],
        "CloudRanger": [0.406, 0.486, 0.403, 0.524, 0.392],
    },
    "MEM": {
        "BARO": [0.778, 0.819, 0.819, 0.778, 0.792],
        "CausalAI": [0.229, 0.125, 0.153, 0.194, 0.194],
        "CausalRCA": [0.0, 0.0, 0.0, 0.0, 0.0],
        "Circa": [0.0, 0.0, 0.0, 0.0, 0.0],
        "CloudRanger": [0.049, 0.017, 0.054, 0.037, 0.021],
    },
    "DELAY": {
        "BARO": [0.833, 0.917, 0.875, 0.854, 0.875],
        "CausalAI": [0.061, 0.069, 0.042, 0.0, 0.0],
        "CausalRCA": [0.0, 0.0, 0.0, 0.0, 0.0],
        "Circa": [0.442, 0.346, 0.311, 0.29, 0.339],
        "CloudRanger": [0.163, 0.111, 0.278, 0.083, 0.137],
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

fig, axes = plt.subplots(2, 3, figsize=(6.5, 5), sharex=True, sharey=True)
metrics = ["CPU", "MEM", "DELAY"]

for i, metric in enumerate(metrics):
    for method, vals in coarse[metric].items():
        axes[0, i].plot(msi, vals, marker=".", label=method)
    axes[0, i].set_title(f"Coarse - {metric}")
    # axes[0, i].set_xlabel("Metric scraping interval (s)")
    # axes[0, i].set_ylabel("MRR")

    axes[0, i].set_xticks([1, 3, 5, 15, 30])
    axes[1, i].set_xticks([1, 3, 5, 15, 30])
    # axes[0, i].legend()

for i, metric in enumerate(metrics):
    for method, vals in fine[metric].items():
        axes[1, i].plot(msi, vals, marker=".", label=method)
    axes[1, i].set_title(f"Fine - {metric}")
    # axes[1, i].set_xlabel("Metric scraping interval (s)")
    # axes[1, i].set_ylabel("MRR")

    axes[0, i].set_xticks([1, 3, 5, 15, 30])
    axes[1, i].set_xticks([1, 3, 5, 15, 30])

axes[1, 1].set_xlabel("Metric scraping interval (s)")
axes[1, 0].set_ylabel("MRR")
axes[0, 0].set_ylabel("MRR")
plt.tight_layout()
plt.savefig("cadence_mrr_effect_line.pdf")
