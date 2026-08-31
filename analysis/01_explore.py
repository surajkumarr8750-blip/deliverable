import pandas as pd, numpy as np, glob, os
pd.set_option('display.width', 160)
pd.set_option('display.max_columns', 30)

D = 'dataset/'
files = [f for f in os.listdir(D) if f.endswith('.csv') and f not in ('data_dictionary.csv',)]
dfs = {}
for f in files:
    name = f.replace('.csv','')
    df = pd.read_csv(D+f)
    dfs[name] = df
    print(f"{name:28s} rows={len(df):7d} cols={list(df.columns)}")

print("\n--- Duplicate row checks (full-row dupes) ---")
for name, df in dfs.items():
    dup = df.duplicated().sum()
    print(f"{name:28s} full-row dupes: {dup}")
