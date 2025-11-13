import matplotlib.pyplot as plt

sev_cpu_vals = [10, 20, 30, 50, 100]
sev_delay_vals = [10, 20, 30, 50, 100]

sev_cpu_lbls = ["10", "20", "30", "50", "100"]
sev_delay_lbls = ["10", "20", "30", "50", "100"]

delay_coarse = {
    "BARO": [0.917, 1.0, 0.958, 0.958, 1.0],
    "CausalAI": [0.729, 0.736, 0.75, 0.688, 0.819],
    "CausalRCA": [1.0, 1.0, 1.0, 1.0, 1.0],
    "CIRCA": [0.444, 0.253, 0.429, 0.472, 0.369],
    "CloudRanger": [0.792, 0.51, 0.593, 0.757, 0.436],
}
delay_fine = {
    "BARO": [0.792, 0.75, 0.958, 0.958, 0.958],
    "CausalAI": [0.0, 0.125, 0.083, 0.215, 0.278],
    "CausalRCA": [0.0, 0.0, 0.0, 0.0, 0.0],
    "CIRCA": [0.344, 0.253, 0.429, 0.472, 0.369],
    "CloudRanger": [0.069, 0.093, 0.269, 0.243, 0.346],
}

# CPU rows are blank in LaTeX, so fill with None
cpu_coarse = {
    "BARO": [0.958, 0.958, 0.958, 0.958, 0.875],
    "CausalAI": [0.861, 0.764, 0.819, 0.917, 0.819],
    "CausalRCA": [1.0, 1.0, 1.0, 1.0, 1.0],
    "CIRCA": [0.315, 0.237, 0.315, 0.196, 0.283],
    "CloudRanger": [0.51, 0.525, 0.403, 0.656, 0.513],
}
cpu_fine = {
    "BARO": [0.729, 0.833, 0.792, 0.792, 0.75],
    "CausalAI": [0, 0.065, 0.021, 0, 0],
    "CausalRCA": [0.508, 0.508, 0.508, 0.508, 0.508],
    "CIRCA": [0, 0, 0, 0, 0],
    "CloudRanger": [0.361, 0.486, 0.403, 0.644, 0.438],
}
fig, axes = plt.subplots(2, 2, figsize=(7.5, 4.5), sharex=False, sharey=True)
metrics = ["CPU", "DELAY"]
data = {
    "CPU": (cpu_coarse, cpu_fine, sev_cpu_vals, sev_cpu_lbls),
    "DELAY": (delay_coarse, delay_fine, sev_delay_vals, sev_delay_lbls),
}

for i, metric in enumerate(metrics):
    coarse, fine, sev_vals, sev_lbls = data[metric]

    for m, v in coarse.items():
        axes[0, i].plot(sev_vals, v, marker=".", label=m)
    axes[0, i].set_title(f"Coarse - {metric}")
    axes[0, i].set_xticks(sev_vals)
    axes[0, i].set_xticklabels(sev_lbls)

    for m, v in fine.items():
        axes[1, i].plot(sev_vals, v, marker=".", label=m)
    axes[1, i].set_title(f"Fine - {metric}")
    axes[1, i].set_xticks(sev_vals)
    axes[1, i].set_xticklabels(sev_lbls)

axes[1, 0].set_xlabel("CPU severity (%)")
axes[1, 1].set_xlabel("Delay severity (ms)")
axes[0, 0].set_ylabel("MRR")
axes[1, 0].set_ylabel("MRR")
# axes[0, 1].legend(loc="best")

plt.tight_layout()
plt.savefig("severity_effect_mrr.pdf")
