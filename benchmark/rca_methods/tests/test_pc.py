import sys

import numpy
from causallearn.search.ConstraintBased.PC import pc
from causallearn.utils.PCUtils.BackgroundKnowledge import BackgroundKnowledge
from rca_methods.utility import read_data

numpy.set_printoptions(threshold=sys.maxsize)
df = read_data("./data.csv")

# print(df.columns)
#

df = df.drop(columns=["time"])

# df = df.drop(columns=df.columns[df.columns.str.contains("node|pod")])


node_names = df.columns.to_list()
background_knowledge = BackgroundKnowledge()
cg = pc(
    df.to_numpy().astype(float),
    node_names=node_names,
    show_progress=True,
    verbose=True,
    background_knowledge=background_knowledge,
)
print(cg.G.graph)
