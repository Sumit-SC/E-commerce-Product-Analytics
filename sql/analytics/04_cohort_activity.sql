-- ============================================================================
-- Cohort Activity: Weekly purchase activity (deduplicated)
-- ============================================================================
-- Purpose: Track which users had successful purchases in each week.
--          Each (user_id, activity_week) pair appears exactly ONCE.
--
-- Database: DuckDB
-- Source: orders_raw
-- Output: cohort_activity (one row per user per active week)
--
-- IMPORTANT: This table is deduplicated - if a user purchases multiple
--            times in the same week, they get ONE row for that week.
-- ============================================================================

CREATE OR REPLACE TABLE cohort_activity AS
SELECT DISTINCT
    -- User identifier
    user_id,
    
    -- Activity: Week when user made a successful purchase
    DATE_TRUNC('week', ts) AS activity_week

FROM orders_raw

-- Only include successful orders (exclude failed payments)
WHERE payment_status = 'success'

ORDER BY
    user_id,
    activity_week;

-- ============================================================================
-- Validation: Check activity distribution
-- ============================================================================
-- -- Users with most active weeks
-- SELECT
--     user_id,
--     COUNT(*) AS weeks_active
-- FROM cohort_activity
-- GROUP BY user_id
-- ORDER BY weeks_active DESC
-- LIMIT 20;
--
-- -- Activity by week
-- SELECT
--     activity_week,
--     COUNT(DISTINCT user_id) AS active_users
-- FROM cohort_activity
-- GROUP BY activity_week
-- ORDER BY activity_week;

