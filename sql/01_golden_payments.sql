-- ============================================================
-- 01_golden_payments.sql
-- Purpose: Build a de-duplicated, trustworthy payments table.
--
-- Finding: 500 payment_id values appear as EXACT full-row
-- duplicates (identical account_id, amount, timestamp, status) —
-- an ingestion/retry artifact. These are NOT genuine repayments
-- and double-count ~INR 2.59 Cr (~2% of monthly SUCCESS revenue)
-- if left in.
--
-- Note: payment_reference is UNSAFE as a de-dup or attribution
-- key — the same reference value appears against different
-- account_id / amount combinations (3,407 of 20,821 references),
-- i.e. reference values collide across unrelated transactions.
-- payment_id is the only field with clean identity semantics, so
-- de-dup is done on payment_id only.
-- ============================================================

DROP TABLE IF EXISTS golden_payments;

CREATE TABLE golden_payments AS
SELECT
    payment_id,
    account_id,
    borrower_id,
    event_at,
    strftime('%Y-%m', event_at)               AS event_month,
    payment_reference,
    amount,
    payment_status,
    payment_method,
    provider_id
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY payment_id
               ORDER BY event_at
           ) AS rn
    FROM payments
)
WHERE rn = 1;                       -- keep first occurrence of each payment_id

-- Sanity check: rows removed by de-dup
-- SELECT (SELECT COUNT(*) FROM payments) - (SELECT COUNT(*) FROM golden_payments) AS rows_removed;
