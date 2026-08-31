import pandas as pd
D='dataset/'
payments = pd.read_csv(D+'payments.csv')

pid_counts = payments.payment_id.value_counts()
dup_pid = pid_counts[pid_counts>1]
dup_rows = payments[payments.payment_id.isin(dup_pid.index)]
grp = dup_rows.groupby('payment_id')
identical = grp.apply(lambda g: g.iloc[:, 1:].nunique().eq(1).all())
print("Exact-duplicate payment_id groups (all fields identical):", identical.sum(), "of", len(identical))

succ_dupe_amount = dup_rows[dup_rows.payment_status=='SUCCESS'].drop_duplicates('payment_id').amount.sum()
print(f"Extra (double-counted) SUCCESS amount from exact-duplicate payment_id rows: {succ_dupe_amount:,.0f}")

succ = payments[payments.payment_status=='SUCCESS'].copy()
succ['event_at'] = pd.to_datetime(succ.event_at)
succ_sorted = succ.sort_values(['account_id','amount','event_at'])
succ_sorted['prev_time'] = succ_sorted.groupby(['account_id','amount'])['event_at'].shift(1)
succ_sorted['gap_min'] = (succ_sorted.event_at - succ_sorted.prev_time).dt.total_seconds()/60
near_dupe = succ_sorted[succ_sorted.gap_min.notna() & (succ_sorted.gap_min <= 60)]
print(f"\nNear-duplicate SUCCESS payments (same account+amount within 60min, excl exact payment_id dupes counted above): {len(near_dupe)}")
print(f"Amount at risk: {near_dupe.amount.sum():,.0f} of total SUCCESS {succ.drop_duplicates('payment_id').amount.sum():,.0f} "
      f"({near_dupe.amount.sum()/succ.drop_duplicates('payment_id').amount.sum()*100:.2f}%)")

print("\npayment_status x event month (raw, unclean):")
payments['event_at']=pd.to_datetime(payments.event_at)
payments['month']=payments.event_at.dt.to_period('M')
print(payments.pivot_table(index='month', columns='payment_status', values='payment_id', aggfunc='count', fill_value=0))
