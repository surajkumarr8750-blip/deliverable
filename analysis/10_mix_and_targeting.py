import pandas as pd, numpy as np
D='dataset/'
payments = pd.read_csv(D+'payments.csv').drop_duplicates('payment_id')
accounts = pd.read_csv(D+'accounts.csv')
payments['event_at']=pd.to_datetime(payments.event_at)
payments['month']=payments.event_at.dt.to_period('M').astype(str)
succ = payments[payments.payment_status=='SUCCESS'].merge(accounts[['account_id','risk_segment','loan_type']], on='account_id', how='left')

print("Monthly SUCCESS amount share by risk_segment:")
pt = succ.pivot_table(index='month', columns='risk_segment', values='amount', aggfunc='sum', fill_value=0)
share = pt.div(pt.sum(axis=1), axis=0)*100
print(share.loc['2026-01':'2026-07'].round(1))

print("\nMonthly SUCCESS amount share by loan_type:")
pt2 = succ.pivot_table(index='month', columns='loan_type', values='amount', aggfunc='sum', fill_value=0)
share2 = pt2.div(pt2.sum(axis=1), axis=0)*100
print(share2.loc['2026-01':'2026-07'].round(1))

# daily_targeting channel mix over time
tgt = pd.read_csv(D+'daily_targeting.csv')
tgt['target_date']=pd.to_datetime(tgt.target_date)
tgt['month']=tgt.target_date.dt.to_period('M').astype(str)
chmix = tgt.pivot_table(index='month', columns='recommended_channel', values='target_id', aggfunc='count', fill_value=0)
chshare = chmix.div(chmix.sum(axis=1),axis=0)*100
print("\nDaily targeting recommended_channel share by month:")
print(chshare.loc['2026-01':'2026-07'].round(1))

# priority mix
pr = tgt.groupby('month').priority.mean()
print("\nAvg targeting priority by month:\n", pr.loc['2026-01':'2026-07'])

# campaign channel mix used in calls by month (which channel campaigns were live)
campaigns = pd.read_csv(D+'campaigns.csv')
calls = pd.read_csv(D+'calls.csv').drop_duplicates()
calls = calls.merge(campaigns[['campaign_id','channel','target_definition']], on='campaign_id', how='left')
calls['event_at']=pd.to_datetime(calls.event_at); calls['month']=calls.event_at.dt.to_period('M').astype(str)
cc = calls.pivot_table(index='month', columns='target_definition', values='call_id', aggfunc='count', fill_value=0)
ccshare = cc.div(cc.sum(axis=1),axis=0)*100
print("\nCalls by campaign target_definition, share by month:")
print(ccshare.loc['2026-01':'2026-07'].round(1))
