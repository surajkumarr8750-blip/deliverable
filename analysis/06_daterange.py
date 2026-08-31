import pandas as pd
D='dataset/'
for f,col in [('calls','event_at'),('payments','event_at'),('call_attempts','event_at'),
              ('daily_targeting','target_date'),('campaigns','start_at'),('accounts','opened_at'),
              ('account_status_history','event_at'),('promises_to_pay','event_at')]:
    df = pd.read_csv(D+f+'.csv', usecols=[col])
    s = pd.to_datetime(df[col])
    print(f"{f:25s} {col:12s} min={s.min()} max={s.max()}")
