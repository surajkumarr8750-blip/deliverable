# Data Quality Report — Collections Analytics

## 1. Summary of findings

| # | Issue | Table | Scale | Business impact |
|---|---|---|---|---|
| 1 | Exact-duplicate payment rows (retry/ingestion artifact) | payments | 500 duplicate `payment_id` occurrences (346 SUCCESS-status) out of 25,500 rows | Overstates recovered revenue by **₹2.59 Cr (~2.0% of SUCCESS amount)** if not removed |
| 2 | `payment_reference` is not a safe join/attribution key | payments | 3,408 of 25,500 rows share a reference value with a **different** account_id/amount | Any campaign/channel "attribution" logic built on `payment_reference` will misattribute revenue |
| 3 | Exact-duplicate call rows | calls | 1,271 of 91,350 rows | Inflates call-volume/contact-rate denominators by ~1.4% |
| 4 | Agent identity cannot be resolved from the `agents` dimension | agents | 30,000 rows but only 1,000 unique `agent_id` / 1,099 unique `employee_code`; **100% of `agent_id`s** are linked to 6-10 conflicting names/vendors/teams, and **100% of `employee_code`s** map to multiple `agent_id`s | Agent-level or employee-level performance reporting from this table is not trustworthy at all; must use `agent_id` as an anonymous operational key from event tables only |
| 5 | Conflicting timestamps | account_status_history | 50.3% of 60,000 rows have `recorded_at` **before** `event_at` (a physically impossible ordering) | Any "time-to-status-change" or SLA metric built on `recorded_at` is unreliable; must use `event_at` |
| 6 | Mixed timezones, single column | calls, accounts | 3 timezones (UTC / Asia/Kolkata / Asia/Dubai), ~33% each | Hour-of-day / calling-window compliance metrics are meaningless unless normalized. After normalizing to IST, the % of calls outside the 7am–9pm window barely moves (41.8% → 41.7%), so the timezone bug does **not** materially change the compliance conclusion — but it must still be corrected for correctness. |
| 7 | Disposition code versions coexist, not sequential | call_dispositions | `legacy` / `v1` / `v2` all span the full Jan–Aug window | Filtering by version does not isolate an era; requires a canonical code map, not a time cut |
| 8 | Borrower table holds multiple snapshot rows per person | borrowers | 30,600 rows / 11,015 unique `borrower_id` (avg 2.8 rows each, up to 5); only 1 phone number shared across ids | Not a duplicate-identity problem — looks like uncollapsed history (name/city/state changed over time). Golden borrower record = latest `updated_at` per `borrower_id`. |
| 9 | Observation window is shorter than stated | all event tables | Actual usable event data spans **Jan 1 – Aug 8, 2026** (~7.3 months), not 12 months | Any "12-month" trend claim in existing reporting is itself built on less data than assumed |
| 10 | No cost data anywhere in the dataset | all tables | — | ROI / cost-per-₹-recovered / break-even calculations for the ₹10 Cr decision cannot be computed from this data alone; must use external/assumed unit costs (flagged explicitly in the memo) |

## 2. Detection methodology
All checks were run twice — once in pandas (`analysis/02_identity.py`–`analysis/11_agent_and_tz.py`) and once as standalone, reproducible SQL against a SQLite mirror of the raw CSVs (`sql/04_data_forensics.sql`) — and the two independent implementations agree on every number above.

## 3. Cleaning decisions (Raw → Golden)

| Table | Raw rows | Rule applied | Golden rows |
|---|---|---|---|
| payments | 25,500 | Drop exact-duplicate `payment_id` rows, keep first occurrence | 25,000 |
| calls | 91,350 | `DISTINCT` on full row (removes ingestion retries); timestamp normalized to IST | 90,079 |
| accounts | 30,000 | No dedup needed (1 row per `account_id` confirmed); added `dpd_bucket` | 30,000 |
| agents | 30,000 | **Not used as an identity dimension.** Operational `agent_id` list extracted directly from calls/dispositions instead (1,000 ids) | n/a — flagged for source-system fix |
| account_status_history | 60,000 | Kept as-is; `event_at` used as the authoritative time field, `recorded_at` used only to measure ingestion lag, never for sequencing | 60,000 |

## 4. What was *not* found (equally important)
- **No material portfolio mix shift**: risk-segment share of recovered amount stays within a 23–27% band every month; loan-type mix is similarly flat.
- **No detectable targeting-strategy change point**: campaign channel mix, `target_definition` mix, and average targeting priority are statistically flat across Jan–Jul (all within ~1–2 percentage points month to month).
- **No denominator manipulation**: the number of distinct accounts contacted per month is stable (9,532–10,417), with no declining-population pattern that would artificially inflate a rate metric.
- **No statistically significant channel-conversion difference**: PTP-kept rate by channel (CALL 25.7%, SMS 25.6%, FIELD 24.5%, WHATSAPP 23.9%) — chi-square p = 0.126, not significant at typical sample sizes (~1,100–1,200 per channel).

These negative findings matter as much as the positive ones: they rule out several of the most common causes of a false "improvement" (mix effects, cohort effects, shrinking denominators) — which is why the analysis in the executive memo concludes the reported 11% is a **measurement artifact**, not a hidden real driver.
