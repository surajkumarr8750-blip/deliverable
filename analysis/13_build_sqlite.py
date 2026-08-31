import pandas as pd, sqlite3, os
D='dataset/'
con = sqlite3.connect('collections.db')
for f in os.listdir(D):
    if f.endswith('.csv') and f!='data_dictionary.csv':
        name = f.replace('.csv','')
        df = pd.read_csv(D+f)
        df.to_sql(name, con, if_exists='replace', index=False)
        print(name, len(df))
con.close()
