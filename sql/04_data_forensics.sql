-- ============================================================
-- 04_data_forensics.sql
-- Checks A-G required by the assignment brief.
-- ============================================================

-- A. Duplicate payments -----------------------------------------------
-- Exact full-row duplicate payment_id values (retry/ingestion artifact)
SELECT 'A_duplicate_payment_rows' AS check_name,
       COUNT(*) AS n_duplicate_payment_ids,
       SUM(amount) AS overstated_amount
FROM (
    SELECT payment_id, amount,
           ROW_NUMBER() OVER (PARTITION BY payment_id ORDER BY event_at) rn
    FROM payments WHERE payment_status='SUCCESS'
) WHERE rn > 1;

-- B. Attribution errors --------------------------------------------------
-- payment_reference is reused across UNRELATED account/amount pairs,
-- proving it cannot be trusted as a transaction or campaign-attribution key.
SELECT 'B_unsafe_reference_key' AS check_name,
       COUNT(*) AS refs_reused_across_different_accounts
FROM (
    SELECT payment_reference
    FROM payments
    GROUP BY payment_reference
    HAVING COUNT(DISTINCT account_id) > 1
);
-- The payments table carries no campaign_id / channel_id at all, so any
-- "recovery attributed to campaign X" claim in existing reporting must be
-- reconstructed via last-touch-before-payment logic (see notebook, Part 2B)
-- and is inherently attribution-window-dependent -- treat single-channel
-- attribution claims as Hypothesis-grade, not Fact.

-- C. Timezone problems -----------------------------------------------
SELECT 'C_calls_timezone_mix' AS check_name, timezone, COUNT(*) AS n
FROM calls GROUP BY timezone;
-- 3 timezones roughly evenly represented (~33% each) in a single column
-- that is only reliable if normalized before any hour-of-day analysis.

-- D. Vendor / disposition-code versioning -----------------------------
SELECT 'D_disposition_versions_coexist' AS check_name,
       disposition_version, MIN(event_at) AS first_seen, MAX(event_at) AS last_seen, COUNT(*) n
FROM call_dispositions GROUP BY disposition_version;
-- legacy / v1 / v2 codes are NOT sequential in time -- all three coexist
-- across the entire observation window, so a naive "filter by version"
-- split does not isolate an era; a canonical code-mapping table is
-- required before cross-period comparison.

-- E. Agent identity problems ------------------------------------------
SELECT 'E_agent_id_multiple_names' AS check_name,
       COUNT(*) AS agent_ids_with_conflicting_names
FROM (
    SELECT agent_id, COUNT(DISTINCT agent_name) n
    FROM agents GROUP BY agent_id HAVING n > 1
);
SELECT 'E_employee_code_multiple_agent_ids' AS check_name,
       COUNT(*) AS employee_codes_with_multiple_agent_ids
FROM (
    SELECT employee_code, COUNT(DISTINCT agent_id) n
    FROM agents GROUP BY employee_code HAVING n > 1
);
-- Every single agent_id (1,000/1,000) is associated with multiple,
-- conflicting names/vendors/teams, and every employee_code maps to
-- multiple agent_ids. The agents.csv dimension table cannot be used
-- for person-level identity resolution in its current form. Recommended
-- treatment: use agent_id exactly as referenced in event tables
-- (calls/dispositions/attempts/sessions) as an anonymous operational
-- key only; do not report agent performance "by name".

-- F. Portfolio mix changes --------------------------------------------
SELECT 'F_portfolio_mix_by_month' AS check_name,
       strftime('%Y-%m', p.event_at) AS month, a.risk_segment,
       ROUND(100.0*SUM(p.amount)/SUM(SUM(p.amount)) OVER (PARTITION BY strftime('%Y-%m',p.event_at)),1) AS pct_of_month_recovery
FROM payments p JOIN accounts a ON a.account_id=p.account_id
WHERE p.payment_status='SUCCESS'
GROUP BY month, a.risk_segment ORDER BY month, a.risk_segment;
-- Result: risk_segment share of recovered amount stays within a 23-27%
-- band for every segment every month -- no material portfolio mix shift.

-- G. Denominator manipulation -----------------------------------------
SELECT 'G_accounts_contacted_per_month' AS check_name,
       strftime('%Y-%m', event_at) AS month, COUNT(DISTINCT account_id) AS accounts_contacted
FROM calls GROUP BY month ORDER BY month;
-- Result: contacted population is stable at ~9,500-10,400 accounts/month
-- with no declining-denominator pattern -- no evidence of accounts being
-- dropped from the base to inflate a rate metric.

-- Conflicting-timestamp integrity check (bonus finding) ----------------
SELECT 'BONUS_status_history_recorded_before_event' AS check_name,
       COUNT(*) AS bad_rows, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM account_status_history),2) AS pct
FROM account_status_history
WHERE recorded_at < event_at;
-- 50.3% of account_status_history rows show recorded_at BEFORE event_at,
-- a physically impossible ordering -- clock-skew / ingestion-lag defect
-- in the source system, not a business signal.
