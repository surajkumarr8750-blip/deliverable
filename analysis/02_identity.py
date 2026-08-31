import pandas as pd
D='dataset/'
agents = pd.read_csv(D+'agents.csv')
borrowers = pd.read_csv(D+'borrowers.csv')
payments = pd.read_csv(D+'payments.csv')

print("AGENTS: total rows", len(agents), "unique agent_id", agents.agent_id.nunique(), "unique employee_code", agents.employee_code.nunique())
dupe_emp = agents.groupby('employee_code')['agent_id'].nunique()
print("employee_codes with >1 agent_id:", (dupe_emp>1).sum(), "of", len(dupe_emp))
print(agents[agents.employee_code.isin(dupe_emp[dupe_emp>1].index[:3])].sort_values('employee_code').head(10))

print("\nBORROWERS: rows", len(borrowers), "unique borrower_id", borrowers.borrower_id.nunique(), "unique phone", borrowers.phone.nunique())
dupe_phone = borrowers.groupby('phone')['borrower_id'].nunique()
print("phones with >1 borrower_id:", (dupe_phone>1).sum())

print("\nPAYMENTS: rows", len(payments), "unique payment_id", payments.payment_id.nunique(), "unique payment_reference", payments.payment_reference.nunique())
dupe_ref = payments.groupby('payment_reference')['payment_id'].nunique()
print("payment_reference with >1 payment_id:", (dupe_ref>1).sum())
print(payments[payments.payment_reference.isin(dupe_ref[dupe_ref>1].index[:2])].sort_values('payment_reference'))
print("\npayment_status distribution:\n", payments.payment_status.value_counts())
