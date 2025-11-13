import matplotlib.pyplot as plt
import numpy as np

elastic_vals = ["CPU 50%", "CPU 70%", "CPU 50%\n+ Memory"]

coarse = {
    "CPU": {
        "BARO": [1.0, 0.917, 0.833],
        "CausalAI": [0.833, 0.417, 0.667],
        "CausalRCA": [1.0, np.nan, 1.0],
        "Circa": [0.083, 0.333, 0.083],
        "CloudRanger": [0.25, 0.583, 0.417],
    },
    "MEM": {
        "BARO": [0.917, 0.75, 1.0],
        "CausalAI": [0.833, 0.417, 0.75],
        "CausalRCA": [1.0, np.nan, 1.0],
        "Circa": [0.083, 0.5, 0.167],
        "CloudRanger": [0.083, 0.179, 0.25],
    },
    "DELAY": {
        "BARO": [0.917, 1.0, 0.818],
        "CausalAI": [0.667, 0.417, 0.909],
        "CausalRCA": [1.0, np.nan, 1.0],
        "Circa": [0.167, 0.083, 0.091],
        "CloudRanger": [0.0, 0.25, 0.364],
    },
}

fine = {
    "CPU": {
        "BARO": [0.583, 0.5, 0.417],
        "CausalAI": [0.083, 0.0, 0.0],
        "CausalRCA": [0.25, np.nan, 0.25],
        "Circa": [0.0, 0.0, 0.0],
        "CloudRanger": [0.25, 0.5, 0.333],
    },
    "MEM": {
        "BARO": [0.917, 0.667, 0.667],
        "CausalAI": [0.083, 0.0, 0.167],
        "CausalRCA": [0.0, np.nan, 0.0],
        "Circa": [0.0, 0.0, 0.0],
        "CloudRanger": [0.0, 0.037, 0.083],
    },
    "DELAY": {
        "BARO": [0.917, 0.667, 0.727],
        "CausalAI": [0.0, 0.0, 0.0],
        "CausalRCA": [0.0, np.nan, 0.0],
        "Circa": [0.167, 0.083, 0.091],
        "CloudRanger": [0.0, 0.0, 0.091],
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
    for method, vals in coarse[metric].items():
        axes[0, i].plot(elastic_vals, vals, marker="o", label=method)
    axes[0, i].set_title(f"Coarse - {metric}")
    axes[0, i].set_xticks(elastic_vals)

    for method, vals in fine[metric].items():
        axes[1, i].plot(elastic_vals, vals, marker="o", label=method)
    axes[1, i].set_title(f"Fine - {metric}")
    axes[1, i].set_xticks(elastic_vals)

axes[1, 1].set_xlabel("Elasticity")
axes[1, 0].set_ylabel("MRR")
axes[0, 0].set_ylabel("MRR")
plt.tight_layout()
plt.savefig("elasticity_effect_mrr.pdf")
