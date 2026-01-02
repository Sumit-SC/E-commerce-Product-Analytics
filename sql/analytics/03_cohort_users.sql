-- ============================================================================
-- Cohort Users: Base table defining user cohorts by signup week
-- ============================================================================
-- Purpose: Create a base table of ALL users with their signup cohort.
--          This is the foundation for user-based retention analysis.
--
-- Database: DuckDB
-- Source: users_raw
-- Output: cohort_users (one row per user)
--
-- IMPORTANT: Cohort is defined by SIGNUP, not by first purchase.
--            This ensures retention rates can never exceed 100%.
-- ============================================================================

CREATE OR REPLACE TABLE cohort_users AS
SELECT
    -- User identifier
    user_id,
    
    -- Cohort: Week when user signed up
    -- This defines which cohort the user belongs to
    DATE_TRUNC('week', signup_date) AS cohort_week

FROM users_raw

ORDER BY
    cohort_week,
    user_id;

-- ============================================================================
-- Validation: Check cohort sizes
-- ============================================================================
-- SELECT
--     cohort_week,
--     COUNT(*) AS users_in_cohort
-- FROM cohort_users
-- GROUP BY cohort_week
-- ORDER BY cohort_week;

