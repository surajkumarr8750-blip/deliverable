# Data Analyst Assignment — Analysis Notebook

*Companion code: `/analysis/*.py` (pandas, executed) and `/sql/*.sql` (SQLite, executed independently — both agree on every number below). Raw output logs are reproducible by re-running the scripts against `/dataset`.*

---

## Headline finding

**The reported "11% month-on-month recovery improvement" is a single noisy month, not a trend.**

De-duplicated monthly recovered amount (Jan–Jul 2026):

| Month | Recovered (₹) | MoM % change |
|---|---:|---:|
| Jan-26 | 18.72 Cr | — |
| Feb-26 | 17.01 Cr | **-9.13%** |
| Mar-26 | 18.89 Cr | **+11.03%** |
| Apr-26 | 17.51 Cr | -7.29% |
| May-26 | 18.43 Cr | +5.20% |
| Jun-26 | 17.56 Cr | -4.72% |
| Jul-26 | 18.72 Cr | +6.65% |

The Feb→Mar jump of **+11.03%** matches the reported "11% improvement" almost to the decimal. Every other month swings by a similar magnitude in *both* directions. A linear regression of recovered amount on month index gives **r² = 0.004, p = 0.89** — statistically indistinguishable from flat, random noise. Mean MoM change across the 6 transitions is +0.29% with a standard deviation of 8.4 points. Someone (or some dashboard) picked the one month that supported a growth narrative.

This finding reframes every subsequent question: not "why did performance improve" but "is there any real signal at all, and if not, what should leadership actually do."

---

## Part 1 — Golden Dataset (Raw → Rejected/Corrected → Golden)

Full detail in `DATA_QUALITY_REPORT.md`. Summary:

- **payments**: 25,500 raw → 500 exact-duplicate `payment_id` rows removed → **25,000 golden rows**. These duplicates overstate SUCCESS revenue by ₹2.59 Cr (~2.0%) if left in — this alone would *understate* rather than explain the reported improvement, since dedup barely changes the MoM pattern (compare naive vs. golden MoM% in `analysis/08_recovery_trend.py` output — they differ by <0.3pp every month).
- **calls**: 91,350 raw → 1,271 exact-duplicate rows removed → **90,079 golden rows**; timestamps normalized to IST from 3 mixed source timezones.
- **accounts**: 30,000 raw, already unique per `account_id` — used as-is, with a `dpd_bucket` derived column added.
- **agents**: the 30,000-row dimension table is **not usable for identity resolution** — every `agent_id` and every `employee_code` maps to multiple conflicting names/vendors/teams. Golden approach: treat `agent_id` as an anonymous operational key sourced directly from event tables (calls, dispositions, sessions), and exclude person-level ("who is the best agent") reporting until the source system is fixed. This is flagged as a data-governance gap in the executive memo, not silently patched.
- **account_status_history**: kept at 60,000 rows; `event_at` is the authoritative time field (50.3% of rows have `recorded_at` earlier than `event_at`, which is impossible and unusable for sequencing).

Quantified cleaning impact: dedup removes **1.9%** of payment rows and **1.4%** of call rows — small in volume, but the specific duplicated rows would have compounded with a cherry-picked-month narrative to further overstate "improvement," so removing them was necessary before touching the 11% question at all.

---

## Part 2 — Data Forensics (A–G)

Executable checks: `sql/04_data_forensics.sql`.

| Check | Finding | Verdict |
|---|---|---|
| A. Duplicate payments | 346 SUCCESS-status `payment_id`s duplicated exactly; ₹2.59 Cr overstatement | **Fact** — confirmed, corrected in golden dataset |
| B. Attribution errors | `payment_reference` reused across unrelated accounts/amounts in 3,408 cases; payments carry no `campaign_id` at all | **Fact** — the field is unsafe for attribution; any existing "recovery by campaign" report built on it is unreliable |
| C. Timezone problems | 3 timezones present (~33% each); normalizing to IST changes the "off-hours calling" rate by only 0.1pp (41.8%→41.7%) | **Fact** (issue exists) but **Correlation-only impact** (doesn't change the headline conclusion) |
| D. Vendor/disposition code changes | `legacy`/`v1`/`v2` disposition versions all coexist across the *entire* window (not sequential) | **Fact** — requires a canonical code map, not a time-based split |
| E. Agent identity | 100% of `agent_id`s (1,000/1,000) and 100% of `employee_code`s (1,099/1,099) show conflicting attributes | **Fact** — severe; agent dimension is unusable as-is |
| F. Portfolio mix changes | Risk-segment share of monthly recovered amount stays in a 23–27% band every month; loan-type mix similarly flat | **No evidence found** — ruled out as a driver |
| G. Denominator manipulation | Accounts contacted per month stable at 9,532–10,417, no declining pattern | **No evidence found** — ruled out |

---

## Part 3 — Statistical Investigation

- **Time-series / trend effect**: see headline — no significant linear trend (p=0.89). The series behaves like noise around a flat mean of ~₹18.1 Cr/month.
- **Mix effects / Simpson's paradox**: checked by risk_segment and loan_type monthly share of recovered amount — both flat (Part 2, F). No hidden composition shift that would make an aggregate trend misleading; conversely, there is also no composition shift *masking* a real underlying improvement. Ruled out both directions.
- **Cohort effects**: account `opened_at` predates the observation window (Jan 2024–Nov 2025), so cohort vintage is static across the 8 observed months — not a plausible driver of a within-2026 MoM swing.
- **Survivorship / selection bias**: contacted-account count per month is stable (Part 2, G); no shrinking, easier-to-collect subset being substituted in.
- **Attribution-window bias**: because payments carry no channel/campaign key, any "channel X drove the improvement" claim depends entirely on an arbitrarily chosen last-touch window (e.g., call-within-24h vs. within-7-days before payment) and will produce different channel splits for the same underlying total — this is a **Hypothesis-grade**, not Fact-grade, form of attribution and should not be used to justify the ₹10 Cr decision.
- **Channel-level conversion (PTP kept-rate)**: CALL 25.7%, SMS 25.6%, FIELD 24.5%, WHATSAPP 23.9% (n≈1,100–1,200 each). Chi-square test: χ²=5.73, **p=0.126 — not statistically significant**. Classified as **Correlation, weak / likely noise**, not Fact.

**Classification summary of "why did it happen":** there is no statistically supported "why" for a genuine MoM improvement, because Part 3's own trend test shows there was no genuine sustained improvement to explain. The one fact-grade driver of the *reported number specifically* is measurement methodology (cherry-picked comparison month).

---

## Part 4 — Is the 11% real?

**No.** Independent recovery-rate definition (recovered amount ÷ outstanding balance of accounts contacted that month, i.e., normalized for both dedup and workload size) tells the same story:

| Month | Recovery rate |
|---|---:|
| Jan-26 | 5.20% |
| Feb-26 | 5.12% |
| Mar-26 | 5.23% |
| Apr-26 | 4.97% |
| May-26 | 5.09% |
| Jun-26 | 5.03% |
| Jul-26 | 5.21% |

Range: 4.97%–5.23% — a band of 0.26 percentage points around a flat ~5.1% average, with no directional trend. Whether you look at absolute ₹ recovered, dedup-corrected ₹ recovered, or workload-normalized recovery rate, the answer is the same: **performance has been flat, not improving, over the observed 7.3 months.** The 11% figure is real arithmetic (Feb→Mar did rise 11.03%) but is not evidence of a business improvement — it is one data point from a noisy, mean-reverting series, reported without the surrounding context that would have shown it was not a trend.

*(Contact rate, RPC, and PTP rate were also checked channel-by-channel in Part 3 and show the same flat/no-significant-difference pattern — full breakdowns in `analysis/` output logs.)*

---

## Part 5 — Counterfactual: "What if targeting strategy hadn't changed?"

The assignment instructs us to **assume** a mid-year targeting change. We checked the data directly for a real change point first (campaign `target_definition` mix, `recommended_channel` mix, average targeting priority, disposition/strategy version by month) and found **no detectable structural break** — every one of these series is flat within 1–2 points across Jan–Jul. So there is nothing to counterfactually reconstruct from this dataset as-is; what follows is the **methodology** leadership would need if/when a real targeting change is made, demonstrated on an illustrative split date (April 1, 2026).

**Design — Difference-in-Differences (DiD):**
- **Treatment group**: accounts whose `recommended_channel`/targeting priority actually changed after the cutover (would require a *targeting-decision log*, which does not exist in this dataset — see gap below).
- **Control group**: accounts with materially identical `risk_segment` × `dpd_bucket` × `loan_type` whose targeting did *not* change, to net out seasonality and macro effects common to both groups.
- **Identification strategy**: parallel-trends assumption — pre-period (Jan–Mar) recovery-rate trends for treatment and control must track each other before assuming any post-period gap is caused by the targeting change, not by pre-existing divergence.
- **Confounders**: DPD drift (accounts naturally age into worse buckets over the year), macro/seasonal repayment capacity (bonus cycles, festival months), and campaign-level effects independent of targeting.
- **Limitations**: no true targeting-decision log exists in the current data (only a static `recommended_channel` per targeting record, not a "before/after strategy" flag), so treatment/control assignment would itself require better source data. A regression-adjusted DiD (controlling for `risk_segment`, `dpd_bucket`, `loan_type` as covariates) is preferred over simple matching or propensity scoring here, given the moderate sample size (~30K accounts) and the transparency requirement in the brief ("a simple, transparent method is preferred over a complex model that cannot be explained").

**What would be needed to actually run this**: a timestamped log of *which accounts had their targeting strategy changed and when* (not currently captured anywhere in the 17 tables provided).

---

## Part 6 — Where should the ₹10 Cr go?

Given the findings above, this section is intentionally more conservative than a typical recommendation memo — see the executive memo for the full reasoning, financial sketch, and explicit statement of what data is missing to firm it up. In short: current data shows **no statistically significant conversion difference between channels**, **no cost data anywhere in the dataset**, and only a modest, flat overall contact/answer rate (19.9% of all calls are answered) — which points toward "raise the number of successful contact attempts" as the more defensible lever than "pick a channel because it appears to convert better," since the apparent channel differences are not statistically real.

---

## Part 7 — Production Analytics Design

See `ARCHITECTURE.svg` / `EXECUTIVE_MEMO.docx` appendix for the full Raw → Staging → Clean → Golden → Feature → Metrics → Dashboard design, including: data contracts per source table, `payment_id`/`account_id`/`agent_id` as primary keys (agent identity flagged for a source-system fix before it can anchor any key), lineage from this notebook's cleaning rules, incremental/backfill handling for late-arriving events (using `event_at` never `recorded_at`), and automated data-quality checks that would have caught issues 1–10 in the Data Quality Report before they reached a leadership dashboard (e.g., a nightly assertion that MoM recovered-amount swings beyond ±2 standard deviations of the trailing 6-month distribution are flagged for review before being reported — which alone would have caught the Feb→Mar anomaly being over-interpreted).
