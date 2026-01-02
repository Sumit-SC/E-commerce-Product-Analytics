-- ============================================================================
-- Cohort Retention: User retention counts by cohort and period
-- ============================================================================
-- Purpose: Calculate how many users from each cohort made purchases
--          in each period (week) after signup.
--
-- Database: DuckDB
-- Source: cohort_users, cohort_activity
-- Output: cohort_retention (one row per cohort per cohort_index)
--
-- KEY CONCEPT:
-- - cohort_index = 0: User was active in their signup week
-- - cohort_index = 1: User was active 1 week after signup
-- - cohort_index = N: User was active N weeks after signup
-- ============================================================================

CREATE OR REPLACE TABLE cohort_retention AS
SELECT
    -- Cohort week (from user signup)
    cu.cohort_week,
    
    -- Calculate cohort_index: number of weeks between activity and signup
    -- cohort_index = 0 means activity happened in the signup week
    DATEDIFF('week', cu.cohort_week, ca.activity_week) AS cohort_index,
    
    -- Count distinct users active in this cohort and period
    COUNT(DISTINCT cu.user_id) AS users_active

FROM cohort_users cu
INNER JOIN cohort_activity ca
    ON cu.user_id = ca.user_id

-- Data quality: Exclude negative cohort_index (activity before signup)
-- This filters out any edge cases where order timestamp is before signup
WHERE DATEDIFF('week', cu.cohort_week, ca.activity_week) >= 0

GROUP BY
    cu.cohort_week,
    cohort_index

ORDER BY
    cu.cohort_week,
    cohort_index;

-- ============================================================================
-- Validation: Check retention data
-- ============================================================================
-- -- Sample retention data
-- SELECT * FROM cohort_retention LIMIT 50;
--
-- -- Check that users_active is reasonable
-- SELECT
--     cohort_index,
--     AVG(users_active) AS avg_active,
--     MAX(users_active) AS max_active
-- FROM cohort_retention
-- GROUP BY cohort_index
-- ORDER BY cohort_index;

