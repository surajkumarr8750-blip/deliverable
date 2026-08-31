import pandas as pd
D='dataset/'
calls = pd.read_csv(D+'calls.csv')
accounts = pd.read_csv(D+'accounts.csv')
campaigns = pd.read_csv(D+'campaigns.csv')
disp = pd.read_csv(D+'call_dispositions.csv')
targeting = pd.read_csv(D+'daily_targeting.csv')

print("calls.timezone distribution:\n", calls.timezone.value_counts())
print("\naccounts.timezone distribution:\n", accounts.timezone.value_counts())
print("\naccounts.schema_version:\n", accounts.schema_version.value_counts())

print("\ncampaigns.strategy_version:\n", campaigns.strategy_version.value_counts())
campaigns['start_at']=pd.to_datetime(campaigns.start_at)
print(campaigns.groupby('strategy_version').start_at.agg(['min','max','count']))
print("\ncampaigns.target_definition unique values:\n", campaigns.target_definition.value_counts())
print("\ncampaigns.channel:\n", campaigns.channel.value_counts())

print("\ndisposition_version:\n", disp.disposition_version.value_counts())
disp['event_at']=pd.to_datetime(disp.event_at)
print(disp.groupby('disposition_version').event_at.agg(['min','max','count']))
print("\ndisposition_code by version (top):")
print(disp.groupby(['disposition_version','disposition_code']).size().unstack(fill_value=0))

print("\ntargeting.status:\n", targeting.status.value_counts())
print("targeting.recommended_channel:\n", targeting.recommended_channel.value_counts())
