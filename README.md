# Data Analyst Assignment — Submission

## Contents
- `EXECUTIVE_MEMO.docx` — 2-page memo for leadership (what happened / why / confidence / recommendation)
- `EXECUTIVE_DASHBOARD.html` — open in a browser; one-screen executive view
- `ANALYSIS_NOTEBOOK.md` — full reasoning, Parts 1-6 of the assignment brief
- `DATA_QUALITY_REPORT.md` — Part 1 data-quality findings and cleaning log
- `ARCHITECTURE.svg` — Part 5 production pipeline design
- `sql/` — reproducible SQL repository (run against a SQLite mirror of the raw CSVs;
  01=golden payments, 02=golden accounts/calls, 03=monthly recovery + 11% test, 04=data forensics A-G)
- `analysis/` — pandas scripts that independently reproduce every number in the notebook
- `golden/` — final golden dataset (golden_payments.csv, golden_accounts.csv, golden_calls.csv,
  golden_monthly_recovery_metrics.csv, agents_identity_dq_flag.csv, data_quality_summary.json)

## Reproduce
```
python3 analysis/12_build_golden.py      # pandas pipeline -> golden/
python3 analysis/13_build_sqlite.py      # loads dataset/*.csv into collections.db
python3 run_sql.py sql/01_golden_payments.sql
python3 run_sql.py sql/02_golden_accounts_calls.sql
python3 run_sql.py sql/03_monthly_recovery_and_11pct_test.sql
```

## Headline finding
The reported "11% MoM improvement" is one volatile month (Feb→Mar, +11.03%) inside an otherwise
flat, statistically insignificant 7-month series (trend test p=0.89). Full reasoning in
ANALYSIS_NOTEBOOK.md.
