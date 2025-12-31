-- ============================================================================
-- Funnel Analysis: Build session-level funnel table
-- ============================================================================
-- Purpose: Aggregate events to session level and create binary funnel flags
--          for each stage (visit, product_view, add_to_cart, checkout, purchase)
--
-- Database: DuckDB
-- Source: sessions_enriched (or user_sessions if sessions_enriched doesn't exist)
-- Output: funnel_sessions (one row per session with funnel flags)
-- ============================================================================

-- Note: If sessions_enriched doesn't exist, replace with user_sessions
--       from the sessionization script output

CREATE OR REPLACE TABLE funnel_sessions AS
SELECT
    -- Session identifiers
    user_id,
    -- session_id is derived from user_id + session_index + session start hour
    -- Keeping for reference but not grouping by it (redundant with session_index)
    user_id || '_' || DATE_TRUNC('hour', MIN(ts))::VARCHAR || '_' || session_index::VARCHAR AS session_id,
    session_index,
    
    -- Funnel flags (binary: 1 if event occurred, 0 otherwise)
    -- Visit: Always 1 if session exists (every session starts with visit)
    MAX(CASE WHEN event_type = 'visit' THEN 1 ELSE 0 END) AS has_visit,
    
    -- Product View: Did user view any products?
    MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END) AS has_product_view,
    
    -- Add to Cart: Did user add any products to cart?
    MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS has_add_to_cart,
    
    -- Checkout: Did user reach checkout?
    MAX(CASE WHEN event_type = 'checkout' THEN 1 ELSE 0 END) AS has_checkout,
    
    -- Purchase: Did user complete purchase?
    MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS has_purchase,
    
    -- Session metadata
    MIN(ts) AS session_start_ts,
    MAX(ts) AS session_end_ts,
    
    -- Session duration in minutes
    EXTRACT(EPOCH FROM (MAX(ts) - MIN(ts))) / 60.0 AS session_duration_minutes,
    
    -- Event counts per funnel stage
    COUNT(CASE WHEN event_type = 'visit' THEN 1 END) AS visit_count,
    COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) AS product_view_count,
    COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) AS add_to_cart_count,
    COUNT(CASE WHEN event_type = 'checkout' THEN 1 END) AS checkout_count,
    COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS purchase_count,
    COUNT(*) AS total_events,
    
    -- Session attributes (take first non-null value)
    -- Source: Traffic source for the session
    MAX(CASE WHEN source IS NOT NULL THEN source END) AS source,
    
    -- Device: Device type for the session
    MAX(CASE WHEN device IS NOT NULL THEN device END) AS device,
    
    -- A/B Test fields (from checkout/purchase events)
    MAX(CASE WHEN ab_test_id IS NOT NULL THEN ab_test_id END) AS ab_test_id,
    MAX(CASE WHEN variant IS NOT NULL THEN variant END) AS variant,
    
    -- Product categories viewed in session (array for reference)
    LIST(DISTINCT product_category) AS product_categories_viewed,
    
    -- Distinct products viewed
    COUNT(DISTINCT CASE WHEN product_id IS NOT NULL THEN product_id END) AS distinct_products_viewed

FROM sessions_enriched
GROUP BY
    user_id,
    session_index
ORDER BY
    user_id,
    session_index;

-- ============================================================================
-- Validation Queries
-- ============================================================================

-- Funnel conversion rates (session-level)
-- SELECT
--     COUNT(*) AS total_sessions,
--     SUM(has_visit) AS sessions_with_visit,
--     SUM(has_product_view) AS sessions_with_product_view,
--     SUM(has_add_to_cart) AS sessions_with_add_to_cart,
--     SUM(has_checkout) AS sessions_with_checkout,
--     SUM(has_purchase) AS sessions_with_purchase,
--     -- Conversion rates
--     ROUND(SUM(has_product_view)::DOUBLE / NULLIF(SUM(has_visit), 0) * 100, 2) AS visit_to_product_view_pct,
--     ROUND(SUM(has_add_to_cart)::DOUBLE / NULLIF(SUM(has_product_view), 0) * 100, 2) AS product_view_to_cart_pct,
--     ROUND(SUM(has_checkout)::DOUBLE / NULLIF(SUM(has_add_to_cart), 0) * 100, 2) AS cart_to_checkout_pct,
--     ROUND(SUM(has_purchase)::DOUBLE / NULLIF(SUM(has_checkout), 0) * 100, 2) AS checkout_to_purchase_pct
-- FROM funnel_sessions;

-- Funnel by device
-- SELECT
--     device,
--     COUNT(*) AS total_sessions,
--     SUM(has_product_view) AS with_product_view,
--     SUM(has_add_to_cart) AS with_add_to_cart,
--     SUM(has_checkout) AS with_checkout,
--     SUM(has_purchase) AS with_purchase,
--     ROUND(SUM(has_purchase)::DOUBLE / NULLIF(COUNT(*), 0) * 100, 2) AS purchase_rate_pct
-- FROM funnel_sessions
-- WHERE device IS NOT NULL
-- GROUP BY device
-- ORDER BY purchase_rate_pct DESC;

-- Funnel by source
-- SELECT
--     source,
--     COUNT(*) AS total_sessions,
--     SUM(has_product_view) AS with_product_view,
--     SUM(has_add_to_cart) AS with_add_to_cart,
--     SUM(has_checkout) AS with_checkout,
--     SUM(has_purchase) AS with_purchase,
--     ROUND(SUM(has_purchase)::DOUBLE / NULLIF(COUNT(*), 0) * 100, 2) AS purchase_rate_pct
-- FROM funnel_sessions
-- WHERE source IS NOT NULL
-- GROUP BY source
-- ORDER BY purchase_rate_pct DESC;

-- A/B Test comparison
-- SELECT
--     variant,
--     COUNT(*) AS total_sessions,
--     SUM(has_checkout) AS sessions_with_checkout,
--     SUM(has_purchase) AS sessions_with_purchase,
--     ROUND(SUM(has_checkout)::DOUBLE / NULLIF(COUNT(*), 0) * 100, 2) AS checkout_rate_pct,
--     ROUND(SUM(has_purchase)::DOUBLE / NULLIF(SUM(has_checkout), 0) * 100, 2) AS purchase_conversion_pct
-- FROM funnel_sessions
-- WHERE variant IS NOT NULL
-- GROUP BY variant
-- ORDER BY variant;

