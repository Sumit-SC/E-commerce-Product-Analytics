-- ============================================================================
-- Cohort Sizes: Total users who signed up in each cohort week
-- ============================================================================
-- Purpose: Calculate the size of each cohort (total users who signed up).
--          This is the denominator for retention rate calculations.
--
-- Database: DuckDB
-- Source: cohort_users
-- Output: cohort_sizes (one row per cohort week)
--
-- CRITICAL: Cohort size is based on SIGNUPS, not purchases.
--           This ensures retention rates are bounded 0-1 (0%-100%).
-- ============================================================================

CREATE OR REPLACE TABLE cohort_sizes AS
SELECT
    -- Cohort week
    cohort_week,
    
    -- Total users who signed up in this cohort week
    -- This is ALL users, regardless of whether they ever purchased
    COUNT(DISTINCT user_id) AS cohort_size

FROM cohort_users

GROUP BY
    cohort_week

ORDER BY
    cohort_week;

-- ============================================================================
-- Validation: Check cohort sizes
-- ============================================================================
-- SELECT * FROM cohort_sizes ORDER BY cohort_week;
--
-- -- Total users across all cohorts
-- SELECT SUM(cohort_size) AS total_users FROM cohort_sizes;

