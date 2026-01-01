-- ============================================================================
-- Power BI Views: Clean, BI-friendly views for dashboarding
-- ============================================================================
-- Purpose: Create optimized views for Power BI dashboards
--          - Funnel metrics (aggregated)
--          - Cohort retention rates
--          - A/B test summary
--
-- Database: DuckDB
-- Source: funnel_sessions, purchase_cohorts
-- Output: Views (not tables) for Power BI consumption
-- ============================================================================

-- ============================================================================
-- View 1: Funnel Metrics
-- ============================================================================
-- Purpose: Aggregate funnel metrics at overall and segmented levels
--          Provides total sessions, sessions per step, and conversion rates
--
-- Usage in Power BI:
--   - Funnel visualization
--   - Conversion rate trends
--   - Segmentation by device, source, etc.
-- ============================================================================

CREATE OR REPLACE VIEW v_funnel_metrics AS
SELECT
    -- Dimensions (for filtering/grouping in Power BI)
    COALESCE(source, 'unknown') AS source,
    COALESCE(device, 'unknown') AS device,
    DATE_TRUNC('day', session_start_ts) AS session_date,
    
    -- Funnel metrics
    COUNT(*) AS total_sessions,
    
    -- Sessions reaching each funnel step
    SUM(has_visit) AS sessions_with_visit,
    SUM(has_product_view) AS sessions_with_product_view,
    SUM(has_add_to_cart) AS sessions_with_add_to_cart,
    SUM(has_checkout) AS sessions_with_checkout,
    SUM(has_purchase) AS sessions_with_purchase,
    
    -- Conversion rates (as ratios 0-1, let Power BI format as %)
    -- Visit → Product View
    ROUND(
        CAST(SUM(has_product_view) AS DOUBLE) / NULLIF(SUM(has_visit), 0),
        4
    ) AS visit_to_product_view_rate,
    
    -- Product View → Add to Cart
    ROUND(
        CAST(SUM(has_add_to_cart) AS DOUBLE) / NULLIF(SUM(has_product_view), 0),
        4
    ) AS product_view_to_cart_rate,
    
    -- Add to Cart → Checkout
    ROUND(
        CAST(SUM(has_checkout) AS DOUBLE) / NULLIF(SUM(has_add_to_cart), 0),
        4
    ) AS cart_to_checkout_rate,
    
    -- Checkout → Purchase
    ROUND(
        CAST(SUM(has_purchase) AS DOUBLE) / NULLIF(SUM(has_checkout), 0),
        4
    ) AS checkout_to_purchase_rate,
    
    -- Overall conversion: Visit → Purchase
    ROUND(
        CAST(SUM(has_purchase) AS DOUBLE) / NULLIF(SUM(has_visit), 0),
        4
    ) AS visit_to_purchase_rate

FROM funnel_sessions
GROUP BY
    source,
    device,
    session_date
ORDER BY
    session_date DESC,
    source,
    device;

-- ============================================================================
-- View 2: Cohort Retention Rates
-- ============================================================================
-- Purpose: Provide cohort retention data for heatmaps and retention curves
--          Uses the same logic as 05_cohort_retention_rates.sql
--
-- Usage in Power BI:
--   - Retention heatmap (cohort_week vs cohort_index)
--   - Retention curves over time
--   - Cohort size analysis
-- ============================================================================

CREATE OR REPLACE VIEW v_cohort_retention AS
WITH retention_counts AS (
    -- Calculate retention counts (users active per cohort and period)
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
    -- Calculate cohort size (users in signup week, cohort_index = 0)
    SELECT
        cohort_week,
        COUNT(DISTINCT user_id) AS cohort_size
    FROM purchase_cohorts
    WHERE DATEDIFF('week', cohort_week, activity_week) = 0
    GROUP BY
        cohort_week
)

SELECT
    rc.cohort_week,
    rc.cohort_index,
    rc.users_active,
    cs.cohort_size,
    
    -- Retention rate as ratio (0.0 to 1.0, let Power BI format as %)
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
-- View 3: A/B Test Summary
-- ============================================================================
-- Purpose: Provide variant-wise conversion metrics for A/B test analysis
--          Focuses on checkout → purchase conversion (primary metric)
--
-- Usage in Power BI:
--   - A/B test comparison charts
--   - Statistical significance indicators
--   - Sample size validation
-- ============================================================================

CREATE OR REPLACE VIEW v_ab_test_summary AS
SELECT
    -- Test identification
    COALESCE(ab_test_id, 'unknown') AS ab_test_id,
    variant,
    
    -- Sample sizes
    COUNT(*) AS total_sessions,
    SUM(has_checkout) AS sessions_with_checkout,
    SUM(has_purchase) AS sessions_with_purchase,
    
    -- Conversion rates (as ratios 0-1, let Power BI format as %)
    -- Overall: Visit → Purchase
    ROUND(
        CAST(SUM(has_purchase) AS DOUBLE) / NULLIF(COUNT(*), 0),
        4
    ) AS visit_to_purchase_rate,
    
    -- Primary metric: Checkout → Purchase
    ROUND(
        CAST(SUM(has_purchase) AS DOUBLE) / NULLIF(SUM(has_checkout), 0),
        4
    ) AS checkout_to_purchase_rate,
    
    -- Other funnel steps for context
    ROUND(
        CAST(SUM(has_checkout) AS DOUBLE) / NULLIF(COUNT(*), 0),
        4
    ) AS visit_to_checkout_rate,
    
    ROUND(
        CAST(SUM(has_add_to_cart) AS DOUBLE) / NULLIF(COUNT(*), 0),
        4
    ) AS visit_to_cart_rate

FROM funnel_sessions
WHERE variant IS NOT NULL
GROUP BY
    ab_test_id,
    variant
ORDER BY
    ab_test_id,
    variant;

-- ============================================================================
-- View 4: A/B Test Detailed (Optional - for drill-down analysis)
-- ============================================================================
-- Purpose: Session-level A/B test data for detailed analysis
--          Includes all session attributes for segmentation
--
-- Usage in Power BI:
--   - Detailed A/B test analysis
--   - Segmentation by device, source, etc.
--   - Time-series analysis of A/B test performance
-- ============================================================================

CREATE OR REPLACE VIEW v_ab_test_detailed AS
SELECT
    -- Session identifiers
    user_id,
    session_id,
    session_index,
    
    -- A/B test attributes
    ab_test_id,
    variant,
    
    -- Funnel flags
    has_visit,
    has_product_view,
    has_add_to_cart,
    has_checkout,
    has_purchase,
    
    -- Session metadata
    session_start_ts,
    session_end_ts,
    session_duration_minutes,
    source,
    device,
    
    -- Date dimension for time-series
    DATE_TRUNC('day', session_start_ts) AS session_date,
    DATE_TRUNC('week', session_start_ts) AS session_week,
    DATE_TRUNC('month', session_start_ts) AS session_month

FROM funnel_sessions
WHERE variant IS NOT NULL
ORDER BY
    session_start_ts DESC,
    user_id,
    session_index;

-- ============================================================================
-- Validation Queries (for testing views)
-- ============================================================================

-- Test funnel metrics view
-- SELECT * FROM v_funnel_metrics LIMIT 10;

-- Test cohort retention view
-- SELECT * FROM v_cohort_retention WHERE cohort_index <= 4 LIMIT 20;

-- Test A/B test summary view
-- SELECT * FROM v_ab_test_summary;

-- Test A/B test detailed view
-- SELECT * FROM v_ab_test_detailed LIMIT 100;

