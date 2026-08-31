import pandas as pd
D='dataset/'
agents = pd.read_csv(D+'agents.csv')
names_per_agentid = agents.groupby('agent_id')['agent_name'].nunique()
print("agent_id values with >1 distinct name:", (names_per_agentid>1).sum(), "of", len(names_per_agentid))
print(names_per_agentid.describe())
sample_id = names_per_agentid.idxmax()
print(agents[agents.agent_id==sample_id][['agent_id','employee_code','agent_name','vendor_id','team','status']].head(8))

# calls timezone -> check if hour distribution differs meaningfully when treated naively (event_at as-is) vs normalized to UTC then Kolkata
calls = pd.read_csv(D+'calls.csv').drop_duplicates()
calls['event_at']=pd.to_datetime(calls.event_at)
calls['naive_hour']=calls.event_at.dt.hour
import numpy as np
offsets = {'UTC':0,'Asia/Kolkata':5.5,'Asia/Dubai':4}
calls['offset']=calls.timezone.map(offsets)
calls['utc_time']=calls.event_at - pd.to_timedelta(calls.offset, unit='h')
calls['ist_time']=calls.utc_time + pd.Timedelta(hours=5.5)
calls['norm_hour']=calls.ist_time.dt.hour

print("\nCalls flagged outside allowed calling hours (7am-9pm IST norm) - naive vs normalized:")
naive_bad = ((calls.naive_hour<7)|(calls.naive_hour>=21)).sum()
norm_bad = ((calls.norm_hour<7)|(calls.norm_hour>=21)).sum()
print(f"naive (raw event_at, ignoring stated timezone): {naive_bad} of {len(calls)} ({naive_bad/len(calls)*100:.1f}%)")
print(f"normalized to IST using stated timezone: {norm_bad} of {len(calls)} ({norm_bad/len(calls)*100:.1f}%)")
