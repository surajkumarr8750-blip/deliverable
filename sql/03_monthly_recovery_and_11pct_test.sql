-- ============================================================
-- 03_monthly_recovery_and_11pct_test.sql
-- Reconstructs monthly recovery performance from the golden
-- (de-duplicated) payments table and tests the leadership claim
-- "recovery has improved by 11% month-on-month".
-- ============================================================

DROP TABLE IF EXISTS monthly_recovery;
CREATE TABLE monthly_recovery AS
WITH contacted AS (
    SELECT DISTINCT account_id, event_month
    FROM golden_calls
),
denom AS (
    SELECT c.event_month,
           SUM(a.outstanding_amount) AS outstanding_denom,
           COUNT(DISTINCT c.account_id) AS accounts_contacted
    FROM contacted c
    JOIN golden_accounts a ON a.account_id = c.account_id
    GROUP BY c.event_month
),
collected AS (
    SELECT event_month,
           SUM(amount) AS recovered_amount,
           COUNT(*)    AS recovered_txns
    FROM golden_payments
    WHERE payment_status = 'SUCCESS'
    GROUP BY event_month
)
SELECT
    d.event_month,
    co.recovered_amount,
    co.recovered_txns,
    d.accounts_contacted,
    d.outstanding_denom,
    ROUND(100.0 * co.recovered_amount / d.outstanding_denom, 3) AS recovery_rate_pct
FROM denom d
JOIN collected co ON co.event_month = d.event_month
ORDER BY d.event_month;

-- Month-on-month % change in recovered amount (golden / de-duplicated)
DROP TABLE IF EXISTS mom_change;
CREATE TABLE mom_change AS
SELECT
    event_month,
    recovered_amount,
    ROUND(
      100.0 * (recovered_amount - LAG(recovered_amount) OVER (ORDER BY event_month))
      / LAG(recovered_amount) OVER (ORDER BY event_month)
    , 2) AS mom_pct_change
FROM monthly_recovery
WHERE event_month BETWEEN '2026-01' AND '2026-07';   -- exclude partial Aug month

-- RESULT (see /golden/golden_monthly_recovery_metrics.csv for the executed output):
-- MoM % changes across Jan-Jul 2026: -9.13, +11.03, -7.29, +5.20, -4.72, +6.65
-- The single Feb->Mar jump of +11.03% matches the reported "11% MoM
-- improvement" almost exactly. Every other month moves in the opposite
-- direction by a similar magnitude. A 7-point linear regression of
-- recovered_amount on month index gives r^2 = 0.004, p = 0.89 -- i.e.
-- statistically indistinguishable from a flat, noisy series.
-- Conclusion: the "11% improvement" is one volatile month picked out of
-- a flat trend, not a sustained business improvement.
