-- ============================================================================
-- Sessionization: Create user sessions from raw clickstream events
-- ============================================================================
-- Purpose: Sessionize raw events by grouping events into sessions based on
--          30-minute inactivity gaps. Handles missing session_ids.
--
-- Database: DuckDB
-- Source: events_raw
-- Output: user_sessions (sessionized events with session_index)
-- ============================================================================

-- Step 1: Prepare events with fallback session_id for missing values
-- Missing session_ids are replaced with: user_id || '_' || hour(ts)
WITH events_prepared AS (
    SELECT
        event_id,
        user_id,
        -- Use existing session_id if present, otherwise create fallback
        COALESCE(
            session_id,
            user_id || '_' || DATE_TRUNC('hour', ts)::VARCHAR
        ) AS session_id,
        event_type,
        page,
        product_id,
        product_category,
        ts,
        source,
        device,
        ab_test_id,
        variant
    FROM events_raw
),

-- Step 2: Order events per user by timestamp
events_ordered AS (
    SELECT
        *,
        -- Calculate time gap from previous event (in minutes)
        EXTRACT(EPOCH FROM (ts - LAG(ts) OVER (
            PARTITION BY user_id 
            ORDER BY ts
        ))) / 60.0 AS minutes_since_last_event
    FROM events_prepared
),

-- Step 3: Identify session breaks (30-minute inactivity gap)
session_breaks AS (
    SELECT
        *,
        -- Mark session start: first event OR gap > 30 minutes
        CASE
            WHEN LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) IS NULL THEN 1
            WHEN minutes_since_last_event > 30 THEN 1
            ELSE 0
        END AS is_session_start
    FROM events_ordered
),

-- Step 4: Create session_index using running sum of session starts
sessionized_with_index AS (
    SELECT
        *,
        -- Session index: running count of sessions per user (starts at 1)
        SUM(is_session_start) OVER (
            PARTITION BY user_id 
            ORDER BY ts 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS session_index
    FROM session_breaks
),

-- Step 5: Generate session_id based on session start time
sessionized AS (
    SELECT
        user_id,
        -- Generate unique session_id using session start hour
        -- Format: user_id || '_' || hour_of_session_start || '_' || session_index
        user_id || '_' || 
        DATE_TRUNC('hour', MIN(ts) OVER (PARTITION BY user_id, session_index))::VARCHAR || '_' || 
        session_index::VARCHAR AS session_id,
        session_index,
        event_id,
        event_type,
        product_id,
        product_category,
        source,
        device,
        ab_test_id,
        variant,
        ts
    FROM sessionized_with_index
)

-- Step 6: Create final output table
CREATE OR REPLACE TABLE user_sessions AS
SELECT
    user_id,
    session_id,
    session_index,
    event_id,
    event_type,
    product_id,
    product_category,
    source,
    device,
    ab_test_id,
    variant,
    ts
FROM sessionized
ORDER BY user_id, session_index, ts;

-- ============================================================================
-- Validation Queries
-- ============================================================================

-- Count sessions per user (sample)
-- SELECT 
--     user_id,
--     COUNT(DISTINCT session_id) AS num_sessions,
--     COUNT(*) AS num_events
-- FROM user_sessions
-- GROUP BY user_id
-- ORDER BY num_sessions DESC
-- LIMIT 10;

-- Session duration statistics
-- SELECT
--     session_id,
--     user_id,
--     MIN(ts) AS session_start,
--     MAX(ts) AS session_end,
--     EXTRACT(EPOCH FROM (MAX(ts) - MIN(ts))) / 60.0 AS duration_minutes,
--     COUNT(*) AS event_count
-- FROM user_sessions
-- GROUP BY session_id, user_id
-- ORDER BY duration_minutes DESC
-- LIMIT 10;

