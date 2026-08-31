import pandas as pd, numpy as np
D='dataset/'; OUT='golden/'

# ---- Payments: dedupe exact duplicate rows (ingestion retries), keep canonical status ----
payments = pd.read_csv(D+'payments.csv')
raw_n = len(payments)
golden_payments = payments.drop_duplicates(subset=['payment_id']).copy()
dedup_removed = raw_n - len(golden_payments)
golden_payments['event_at'] = pd.to_datetime(golden_payments.event_at)
golden_payments['month'] = golden_payments.event_at.dt.to_period('M').astype(str)
golden_payments.to_csv(OUT+'golden_payments.csv', index=False)

# ---- Accounts: already 1 row per account_id; keep as golden dimension, add dpd_bucket ----
accounts = pd.read_csv(D+'accounts.csv')
def dpd_bucket(d):
    if d==0: return '0_CURRENT'
    if d<=30: return '1_30_DPD'
    if d<=60: return '31_60_DPD'
    if d<=90: return '61_90_DPD'
    return '90PLUS_DPD'
accounts['dpd_bucket'] = accounts.dpd.apply(dpd_bucket)
accounts.to_csv(OUT+'golden_accounts.csv', index=False)

# ---- Calls: dedupe exact-row duplicates, normalize timestamp to IST ----
calls = pd.read_csv(D+'calls.csv')
raw_calls = len(calls)
golden_calls = calls.drop_duplicates().copy()
calls_dedup_removed = raw_calls - len(golden_calls)
offsets = {'UTC':0,'Asia/Kolkata':5.5,'Asia/Dubai':4}
golden_calls['event_at']=pd.to_datetime(golden_calls.event_at)
golden_calls['event_at_ist'] = golden_calls.event_at - pd.to_timedelta(golden_calls.timezone.map(offsets),unit='h') + pd.Timedelta(hours=5.5)
golden_calls['hour_ist'] = golden_calls.event_at_ist.dt.hour
golden_calls['month'] = golden_calls.event_at_ist.dt.to_period('M').astype(str)
golden_calls.to_csv(OUT+'golden_calls.csv', index=False)

# ---- Agents: flag as UNRELIABLE dimension; produce operational agent list from event tables instead ----
agents = pd.read_csv(D+'agents.csv')
name_conflicts = agents.groupby('agent_id')['agent_name'].nunique()
agent_dq_flag = pd.DataFrame({'agent_id':name_conflicts.index,
                               'distinct_names_seen':name_conflicts.values})
agent_dq_flag.to_csv(OUT+'agents_identity_dq_flag.csv', index=False)
# operational agent roster = distinct agent_id actually used in event tables (safe to use as anonymous key)
disp = pd.read_csv(D+'call_dispositions.csv')
ops_agents = pd.Index(calls.agent_id.dropna().unique()).union(disp.agent_id.dropna().unique())
pd.DataFrame({'agent_id': sorted(ops_agents)}).to_csv(OUT+'golden_agent_operational_ids.csv', index=False)

# ---- Monthly recovery metrics (golden) ----
succ = golden_payments[golden_payments.payment_status=='SUCCESS']
monthly_amount = succ.groupby('month').amount.sum()
monthly_count = succ.groupby('month').amount.count()

calls_c = golden_calls[['account_id','month']].drop_duplicates().merge(
    accounts[['account_id','outstanding_amount']], on='account_id', how='left')
denom = calls_c.groupby('month').outstanding_amount.sum()
n_contacted = calls_c.groupby('month').account_id.nunique()

monthly = pd.DataFrame({
    'recovered_amount': monthly_amount,
    'recovered_txns': monthly_count,
    'accounts_contacted': n_contacted,
    'outstanding_denom': denom,
})
monthly['recovery_rate_pct'] = monthly.recovered_amount/monthly.outstanding_denom*100
monthly['recovered_amount_mom_pct'] = monthly.recovered_amount.pct_change()*100
monthly = monthly.loc['2026-01':'2026-08']
monthly.to_csv(OUT+'golden_monthly_recovery_metrics.csv')

# ---- Data quality summary ----
dq = {
 'payments_raw_rows': raw_n,
 'payments_exact_duplicate_rows_removed': dedup_removed,
 'payments_duplicate_amount_double_counted': float(payments[payments.duplicated(subset=['payment_id'],keep='first') & (payments.payment_status=='SUCCESS')].amount.sum()),
 'calls_raw_rows': raw_calls,
 'calls_exact_duplicate_rows_removed': calls_dedup_removed,
 'agents_dimension_rows': len(agents),
 'agents_unique_agent_id': agents.agent_id.nunique(),
 'agents_unique_employee_code': agents.employee_code.nunique(),
 'agents_agent_id_with_name_conflicts': int((name_conflicts>1).sum()),
 'account_status_history_rows': None,
}
import json
hist = pd.read_csv(D+'account_status_history.csv')
hist['event_at']=pd.to_datetime(hist.event_at); hist['recorded_at']=pd.to_datetime(hist.recorded_at)
dq['account_status_history_rows']=len(hist)
dq['status_history_recorded_before_event_pct'] = round(float((hist.recorded_at<hist.event_at).mean()*100),2)
with open(OUT+'data_quality_summary.json','w') as f:
    json.dump(dq, f, indent=2, default=str)

print(json.dumps(dq, indent=2, default=str))
print("\nMonthly golden metrics:\n", monthly.round(2))
