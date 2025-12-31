-- ============================================================================
-- Cohort Retention Rates: Calculate retention percentages by cohort
-- ============================================================================
-- Purpose: Calculate retention rates (percentage of cohort active in each period)
--          by joining cohort sizes with retention counts.
--
-- Database: DuckDB
-- Source: purchase_cohorts
-- Output: Query results with retention rates (not a table)
-- ============================================================================

-- This query calculates:
-- - cohort_size: Total users in the cohort (from cohort_index = 0)
-- - users_active: Users active in each period (cohort_index)
-- - retention_rate: Percentage of cohort active = users_active / cohort_size
--
-- Example interpretation:
-- - cohort_week = '2023-01-02', cohort_index = 0, retention_rate = 1.0 (100%)
--   → All 150 users from Jan 2 cohort made purchases in signup week
-- - cohort_week = '2023-01-02', cohort_index = 4, retention_rate = 0.30 (30%)
--   → 30% of the cohort (45 out of 150) made purchases 4 weeks after signup

WITH retention_counts AS (
    -- Step 1: Calculate retention counts (users active per cohort and period)
    SELECT
        cohort_week,
        DATEDIFF('week', cohort_week, activity_week) AS cohort_index,
        COUNT(DISTINCT user_id) AS users_active
    FROM purchase_cohorts
    WHERE DATEDIFF('week', cohort_week, activity_week) >= 0
    GROUP BY
        cohort_week,
        cohort_index
),

cohort_sizes AS (
    -- Step 2: Calculate cohort size (users in signup week, cohort_index = 0)
    -- This represents the total number of users in each cohort
    SELECT
        cohort_week,
        COUNT(DISTINCT user_id) AS cohort_size
    FROM purchase_cohorts
    WHERE DATEDIFF('week', cohort_week, activity_week) = 0  -- Signup week only
    GROUP BY
        cohort_week
)

-- Step 3: Join retention counts with cohort sizes and calculate retention rate
SELECT
    rc.cohort_week,
    rc.cohort_index,
    rc.users_active,
    cs.cohort_size,
    
    -- Calculate retention rate as percentage
    -- Round to 4 decimal places for precision (e.g., 0.3000 = 30%)
    ROUND(
        CAST(rc.users_active AS DOUBLE) / NULLIF(cs.cohort_size, 0),
        4
    ) AS retention_rate

FROM retention_counts rc
INNER JOIN cohort_sizes cs
    ON rc.cohort_week = cs.cohort_week

ORDER BY
    rc.cohort_week,
    rc.cohort_index;

-- ============================================================================
-- Example Output Interpretation
-- ============================================================================
--
-- cohort_week  | cohort_index | users_active | cohort_size | retention_rate
-- -------------|--------------|--------------|-------------|----------------
-- 2023-01-02   | 0            | 150          | 150         | 1.0000 (100%)
-- 2023-01-02   | 1            | 120          | 150         | 0.8000 (80%)
-- 2023-01-02   | 2            | 95           | 150         | 0.6333 (63.3%)
-- 2023-01-02   | 4            | 45           | 150         | 0.3000 (30%)
-- 2023-01-09   | 0            | 180          | 180         | 1.0000 (100%)
-- 2023-01-09   | 1            | 140          | 180         | 0.7778 (77.8%)
--
-- This shows:
-- - Week of Jan 2 cohort (150 users):
--   * 100% active in signup week (cohort_index 0)
--   * 80% active 1 week later (cohort_index 1)
--   * 63.3% active 2 weeks later (cohort_index 2)
--   * 30% active 4 weeks later (cohort_index 4)
-- - Week of Jan 9 cohort (180 users):
--   * 100% active in signup week
--   * 77.8% active 1 week later

-- ============================================================================
-- Alternative: Calculate retention rate as percentage (0-100)
-- ============================================================================
-- If you prefer percentage format instead of decimal:
--
-- ROUND(
--     CAST(rc.users_active AS DOUBLE) / NULLIF(cs.cohort_size, 0) * 100,
--     2
-- ) AS retention_rate_pct
--
-- This would output: 100.00, 80.00, 63.33, 30.00 instead of 1.0000, 0.8000, etc.

