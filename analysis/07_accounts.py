import pandas as pd
D='dataset/'
accounts = pd.read_csv(D+'accounts.csv')
hist = pd.read_csv(D+'account_status_history.csv')

print("accounts rows", len(accounts), "unique account_id", accounts.account_id.nunique())
print(accounts.status.value_counts())
print(accounts.risk_segment.value_counts())
print(accounts.loan_type.value_counts())
print(accounts.dpd.describe())

print("\naccount_status_history rows", len(hist), "unique account_id", hist.account_id.nunique())
print("rows per account_id distribution:\n", hist.groupby('account_id').size().value_counts().head())
print("status values in history:", hist.status.value_counts())
print("source values:", hist.source.value_counts())

# check recorded_at vs event_at ordering issues (late arriving / out of order)
hist['event_at']=pd.to_datetime(hist.event_at); hist['recorded_at']=pd.to_datetime(hist.recorded_at)
hist['lag_hours'] = (hist.recorded_at - hist.event_at).dt.total_seconds()/3600
print("\nrecorded_at - event_at lag (hours) describe:\n", hist.lag_hours.describe())
print("Rows recorded BEFORE event happened (data integrity issue):", (hist.lag_hours<0).sum())
print("Rows recorded >24h after event (late-arriving):", (hist.lag_hours>24).sum())

# check accounts opened after account_status_history events (impossible)
merged = hist.merge(accounts[['account_id','opened_at']], on='account_id', how='left')
merged['opened_at']=pd.to_datetime(merged.opened_at)
print("\nHistory events before account opened_at:", (merged.event_at < merged.opened_at).sum())
