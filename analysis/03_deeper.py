import pandas as pd
D='dataset/'
borrowers = pd.read_csv(D+'borrowers.csv')
payments = pd.read_csv(D+'payments.csv')
agents = pd.read_csv(D+'agents.csv')

bid = 'BRW0001072'
print("Sample borrower_id rows for one id:")
print(borrowers[borrowers.borrower_id==bid])

print("\nRows-per-borrower_id distribution:")
print(borrowers.groupby('borrower_id').size().value_counts().head())

print("\n--- payment_reference duplicate pattern ---")
ref = payments.payment_reference.value_counts()
multi_ref = ref[ref>1].index
sample = payments[payments.payment_reference.isin(multi_ref[:5])].sort_values(['payment_reference','event_at'])
print(sample[['payment_id','account_id','event_at','payment_reference','amount','payment_status']].to_string())

# status combos for duplicated refs
dupe_payments = payments[payments.payment_reference.isin(multi_ref)]
combo = dupe_payments.groupby('payment_reference')['payment_status'].apply(lambda s: tuple(sorted(s))).value_counts()
print("\nStatus-combo patterns among duplicated payment_reference groups:")
print(combo.head(15))

print("\n--- agents: rows per agent_id / employee_code ---")
print("rows per agent_id:\n", agents.groupby('agent_id').size().value_counts().head())
print("status values:", agents.status.unique())
print(agents[agents.employee_code=='EMP00001'][['agent_id','employee_code','agent_name','vendor_id','team','status','joined_at','updated_at']].sort_values('updated_at').to_string())
