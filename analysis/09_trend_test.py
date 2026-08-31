import pandas as pd, numpy as np
from scipy import stats
D='dataset/'
payments = pd.read_csv(D+'payments.csv').drop_duplicates('payment_id')
payments['event_at']=pd.to_datetime(payments.event_at)
payments['month']=payments.event_at.dt.to_period('M').astype(str)
g = payments[payments.payment_status=='SUCCESS'].groupby('month').amount.sum()
full = g.loc['2026-01':'2026-07']
x = np.arange(len(full))
slope, intercept, r, p, se = stats.linregress(x, full.values)
print("Linear trend on golden monthly recovered amount (Jan-Jul):")
print(f"slope={slope:,.0f}/month  r^2={r**2:.4f}  p-value={p:.4f}")
print(f"Interpretation: {'statistically significant trend' if p<0.05 else 'NO statistically significant trend -- consistent with flat/random noise'}")

print("\nMonth pairwise % changes again:")
print((full.pct_change()*100).round(2))
print(f"\nFeb->Mar change: {(full['2026-03']/full['2026-02']-1)*100:.2f}%  <-- matches reported '11% MoM improvement'")
print(f"Mean of all MoM changes: {(full.pct_change().dropna()*100).mean():.2f}%   Std dev: {(full.pct_change().dropna()*100).std():.2f} pts")

# recovery rate = amount recovered / outstanding amount of accounts contacted that month
accounts = pd.read_csv(D+'accounts.csv')
calls = pd.read_csv(D+'calls.csv').drop_duplicates()
calls['event_at']=pd.to_datetime(calls.event_at)
calls['month']=calls.event_at.dt.to_period('M').astype(str)
contacted = calls[['account_id','month']].drop_duplicates()
contacted = contacted.merge(accounts[['account_id','outstanding_amount']], on='account_id', how='left')
denom = contacted.groupby('month').outstanding_amount.sum()
denom_n = contacted.groupby('month').account_id.nunique()
rate = (g/denom*100)
print("\nRecovery RATE (%) = collected / outstanding of contacted accounts, by month:")
print(pd.DataFrame({'collected':g, 'outstanding_denom':denom, 'n_accounts_contacted':denom_n, 'rate_pct':rate}).loc['2026-01':'2026-07'])
