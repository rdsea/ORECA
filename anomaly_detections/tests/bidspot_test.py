import matplotlib.pyplot as plt
import numpy as np

from anomaly_detections.spot import BiDSPOT, SPOTBase

# physics.dat is a file in the original repository
with open("physics.dat", encoding="UTF-8") as obj:
    data = np.array(list(map(float, obj.read().split(","))))
init_data = 2000
proba = 1e-3
depth = 450

models: list[SPOTBase] = [
    # spot.SPOT(q=proba),
    # spot.dSPOT(q=proba, depth=depth),
    # spot.biSPOT(q=proba),
    # The original implementation of bidSPOT uses n_points=8 for _grimshaw by default
    BiDSPOT(q=proba, depth=depth, n_points=8),
]
for alg in models:
    alg.fit(init_data=init_data, data=data)
    alg.initialize()
    results = alg.run()
    # Plot
    figs = alg.plot(results)
    plt.show()
