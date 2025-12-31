-- ============================================================================
-- Cohort Base Table: Purchase cohorts for retention analysis
-- ============================================================================
-- Purpose: Create a base table mapping users to their signup cohort (week)
--          and tracking their purchase activity by week.
--
-- Database: DuckDB
-- Source: users_raw, orders_raw
-- Output: purchase_cohorts (one row per user per activity week)
-- ============================================================================

-- This table serves as the foundation for retention analysis:
-- - cohort_week: Week when user signed up (defines the cohort)
-- - activity_week: Week when user made a purchase (activity period)
-- - One row per (user_id, activity_week) means if a user purchases multiple
--   times in the same week, they still get one row for that week

CREATE OR REPLACE TABLE purchase_cohorts AS
SELECT DISTINCT
    -- User identifier
    o.user_id,
    
    -- Cohort: Week when user signed up
    -- This defines which cohort the user belongs to
    DATE_TRUNC('week', u.signup_date) AS cohort_week,
    
    -- Activity: Week when user made a purchase
    -- This tracks when the user was active (made a purchase)
    DATE_TRUNC('week', o.ts) AS activity_week

FROM orders_raw o
INNER JOIN users_raw u
    ON o.user_id = u.user_id

-- Only include successful orders (exclude failed payments)
WHERE o.payment_status = 'success'

ORDER BY
    cohort_week,
    o.user_id,
    activity_week;

-- ============================================================================
-- Validation Queries
-- ============================================================================

-- Count users per cohort
-- SELECT
--     cohort_week,
--     COUNT(DISTINCT user_id) AS users_in_cohort
-- FROM purchase_cohorts
-- GROUP BY cohort_week
-- ORDER BY cohort_week
-- LIMIT 20;

-- Count activity weeks per user (sample)
-- SELECT
--     user_id,
--     cohort_week,
--     COUNT(DISTINCT activity_week) AS weeks_with_purchases,
--     MIN(activity_week) AS first_purchase_week,
--     MAX(activity_week) AS last_purchase_week
-- FROM purchase_cohorts
-- GROUP BY user_id, cohort_week
-- ORDER BY weeks_with_purchases DESC
-- LIMIT 20;

-- Check for users with purchases before signup (data quality check)
-- SELECT
--     u.user_id,
--     u.signup_date,
--     DATE_TRUNC('week', u.signup_date) AS cohort_week,
--     MIN(o.ts) AS first_order_ts,
--     DATE_TRUNC('week', MIN(o.ts)) AS first_order_week
-- FROM users_raw u
-- INNER JOIN orders_raw o ON u.user_id = o.user_id
-- WHERE o.payment_status = 'success'
--   AND DATE_TRUNC('week', o.ts) < DATE_TRUNC('week', u.signup_date)
-- LIMIT 10;

