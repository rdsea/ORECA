import pandas as pd

df = pd.read_csv("./cpu_3x_rqs.csv")
# print(df.columns)
df.fillna(0, inplace=True)
print(df["efficientnetb0-7c8ddf759c-nbwsz_pod:cpu_usage"].head())
