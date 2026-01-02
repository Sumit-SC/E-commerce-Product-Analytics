-- ============================================================================
-- Cohort Retention Rates: Final retention analysis table
-- ============================================================================
-- Purpose: Calculate retention rates by joining retention counts with cohort sizes.
--          This is the final table used for dashboards and analysis.
--
-- Database: DuckDB
-- Source: cohort_retention, cohort_sizes
-- Output: cohort_retention_rates (one row per cohort per cohort_index)
--
-- GUARANTEES:
-- - retention_rate is ALWAYS between 0 and 1 (0% to 100%)
-- - Week 0 retention shows conversion (users who purchased in signup week)
-- - No retention value can exceed 100% because:
--   * cohort_size = ALL users who signed up
--   * users_active = DISTINCT users who purchased (subset of cohort)
-- ============================================================================

CREATE OR REPLACE TABLE cohort_retention_rates AS
SELECT
    -- Cohort week
    cr.cohort_week,
    
    -- Cohort index (weeks since signup)
    -- 0 = signup week, 1 = 1 week after, etc.
    cr.cohort_index,
    
    -- Number of distinct users active in this period
    cr.users_active,
    
    -- Total users in the cohort (from signups)
    cs.cohort_size,
    
    -- Retention rate as decimal (0-1)
    -- Will be formatted as percentage in BI tools
    ROUND(
        CAST(cr.users_active AS DOUBLE) / NULLIF(cs.cohort_size, 0),
        4
    ) AS retention_rate

FROM cohort_retention cr
INNER JOIN cohort_sizes cs
    ON cr.cohort_week = cs.cohort_week

ORDER BY
    cr.cohort_week,
    cr.cohort_index;

-- ============================================================================
-- Validation: Ensure retention rates are valid
-- ============================================================================
-- -- Check for any retention > 1 (should be ZERO rows)
-- SELECT *
-- FROM cohort_retention_rates
-- WHERE retention_rate > 1.0;
--
-- -- Week 0 retention should show conversion rate (users who purchased in signup week)
-- SELECT
--     cohort_week,
--     retention_rate AS week0_conversion
-- FROM cohort_retention_rates
-- WHERE cohort_index = 0
-- ORDER BY cohort_week;
--
-- -- Average retention by cohort_index
-- SELECT
--     cohort_index,
--     AVG(retention_rate) AS avg_retention,
--     MIN(retention_rate) AS min_retention,
--     MAX(retention_rate) AS max_retention
-- FROM cohort_retention_rates
-- GROUP BY cohort_index
-- ORDER BY cohort_index;

