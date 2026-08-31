import pandas as pd, numpy as np
pd.set_option('display.width',160)
D='dataset/'
payments = pd.read_csv(D+'payments.csv')
accounts = pd.read_csv(D+'accounts.csv')

payments['event_at']=pd.to_datetime(payments.event_at)
payments['month']=payments.event_at.dt.to_period('M').astype(str)

# NAIVE (as a typical unclean report might do): all SUCCESS rows summed, no dedup
naive = payments[payments.payment_status=='SUCCESS'].groupby('month').amount.agg(['sum','count'])
naive.columns=['naive_amount','naive_count']

# GOLDEN: drop exact full-row duplicate payment_id rows
golden_pay = payments.drop_duplicates(subset=['payment_id']).copy()
golden = golden_pay[golden_pay.payment_status=='SUCCESS'].groupby('month').amount.agg(['sum','count'])
golden.columns=['golden_amount','golden_count']

cmp = naive.join(golden)
cmp['dupe_inflation_pct'] = (cmp.naive_amount-cmp.golden_amount)/cmp.golden_amount*100
print(cmp)

print("\n--- MoM % change, naive vs golden (restricting to full months Jan-Jul; Aug partial) ---")
full = cmp.loc['2026-01':'2026-07']
print("Naive: first month", full.naive_amount.iloc[0], "last month", full.naive_amount.iloc[-1],
      "-> change %", (full.naive_amount.iloc[-1]/full.naive_amount.iloc[0]-1)*100)
print("Golden: first month", full.golden_amount.iloc[0], "last month", full.golden_amount.iloc[-1],
      "-> change %", (full.golden_amount.iloc[-1]/full.golden_amount.iloc[0]-1)*100)
print("\nnaive MoM% :\n", full.naive_amount.pct_change()*100)
print("\ngolden MoM% :\n", full.golden_amount.pct_change()*100)
