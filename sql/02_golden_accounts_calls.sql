-- ============================================================
-- 02_golden_accounts_calls.sql
-- accounts: already 1 row per account_id (verified: 30,000 rows,
-- 30,000 unique account_id) -- used as-is, plus a DPD bucket.
--
-- calls: 91,350 raw rows contain 1,271 exact full-row duplicates
-- (same call_id/account/agent/timestamp repeated) -> removed.
-- Timestamps are recorded in 3 different timezones (UTC,
-- Asia/Kolkata, Asia/Dubai) roughly evenly split (~33% each).
-- Normalize all call timestamps to IST (business timezone) before
-- any hour-of-day / calling-window analysis, or every "wrong
-- calling hour" metric is meaningless.
-- ============================================================

DROP TABLE IF EXISTS golden_accounts;
CREATE TABLE golden_accounts AS
SELECT
    account_id, borrower_id, loan_type, principal_amount,
    outstanding_amount, dpd,
    CASE
        WHEN dpd = 0 THEN '0_CURRENT'
        WHEN dpd <= 30 THEN '1_30_DPD'
        WHEN dpd <= 60 THEN '31_60_DPD'
        WHEN dpd <= 90 THEN '61_90_DPD'
        ELSE '90PLUS_DPD'
    END AS dpd_bucket,
    risk_segment, status, opened_at, timezone, schema_version
FROM accounts;

DROP TABLE IF EXISTS golden_calls;
CREATE TABLE golden_calls AS
SELECT DISTINCT
    call_id, account_id, borrower_id,
    event_at,
    -- normalize to IST: shift raw local timestamp to UTC using its
    -- stated offset, then to IST (+5:30)
    datetime(
        event_at,
        CASE timezone
            WHEN 'UTC'          THEN '+5.5 hours'
            WHEN 'Asia/Kolkata'  THEN '+0 hours'
            WHEN 'Asia/Dubai'    THEN '+1.5 hours'
        END
    ) AS event_at_ist,
    strftime('%Y-%m', event_at) AS event_month,
    agent_id, campaign_id, direction, vendor_id, call_status,
    duration_sec, timezone AS source_timezone
FROM calls;
-- DISTINCT removes the 1,271 exact-duplicate rows.
