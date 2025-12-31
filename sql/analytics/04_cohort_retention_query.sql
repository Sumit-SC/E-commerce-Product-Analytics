-- ============================================================================
-- Cohort Retention Query: Calculate retention counts by cohort and period
-- ============================================================================
-- Purpose: Calculate how many users from each cohort are active in each
--          period (week) after signup.
--
-- Database: DuckDB
-- Source: purchase_cohorts
-- Output: Query results (not a table)
-- ============================================================================

-- This query calculates:
-- - cohort_index: Weeks since signup (0 = signup week, 1 = 1 week after, etc.)
-- - users_active: Number of distinct users active in that period
--
-- Example interpretation:
-- - cohort_week = '2023-01-02', cohort_index = 0, users_active = 150
--   → 150 users from the week of Jan 2, 2023 made purchases in their signup week
-- - cohort_week = '2023-01-02', cohort_index = 4, users_active = 45
--   → 45 users from the week of Jan 2, 2023 made purchases 4 weeks after signup

SELECT
    cohort_week,
    
    -- Calculate cohort_index: number of weeks between activity and signup
    -- cohort_index = 0 means activity happened in the signup week
    -- cohort_index = 1 means activity happened 1 week after signup, etc.
    DATEDIFF('week', cohort_week, activity_week) AS cohort_index,
    
    -- Count distinct users active in this cohort and period
    COUNT(DISTINCT user_id) AS users_active

FROM purchase_cohorts

-- Data quality: Exclude negative cohort_index (activity before signup)
-- This shouldn't happen with proper data, but filters out any edge cases
WHERE DATEDIFF('week', cohort_week, activity_week) >= 0

GROUP BY
    cohort_week,
    cohort_index

ORDER BY
    cohort_week,
    cohort_index;

-- ============================================================================
-- Example Output Interpretation
-- ============================================================================
--
-- cohort_week  | cohort_index | users_active
-- -------------|--------------|--------------
-- 2023-01-02   | 0            | 150
-- 2023-01-02   | 1            | 120
-- 2023-01-02   | 2            | 95
-- 2023-01-02   | 4            | 45
-- 2023-01-09   | 0            | 180
-- 2023-01-09   | 1            | 140
--
-- This shows:
-- - Week of Jan 2 cohort: 150 users purchased in signup week (index 0)
-- - Week of Jan 2 cohort: 120 users purchased 1 week later (index 1)
-- - Week of Jan 2 cohort: 95 users purchased 2 weeks later (index 2)
-- - Week of Jan 2 cohort: 45 users purchased 4 weeks later (index 4)
-- - Week of Jan 9 cohort: 180 users purchased in signup week (index 0)
-- - Week of Jan 9 cohort: 140 users purchased 1 week later (index 1)

