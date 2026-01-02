# SQL Directory

This directory contains all SQL scripts for data transformation and analytics.

## Directory Structure

```
sql/
├── raw/                        # Data cleaning queries (placeholder)
│   └── (empty)                 # Reserved for future cleaning scripts
│
└── analytics/                  # Core analytics transformations
    ├── 01_sessionization.sql   # Session creation with 30-min timeout
    ├── 02_funnel.sql           # Session-level funnel flags
    ├── 03_cohort_users.sql     # User cohorts by signup week
    ├── 04_cohort_activity.sql  # Weekly purchase activity (deduplicated)
    ├── 05_cohort_retention.sql # Retention counts by cohort and period
    ├── 06_cohort_sizes.sql     # Total users per cohort
    ├── 07_cohort_retention_rates.sql  # Final retention rates
    └── 08_powerbi_views.sql    # BI-ready views for Power BI
```

---

## Script Execution Order

Scripts must be executed in order due to table dependencies:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SESSION & FUNNEL                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  events_raw ──▶ 01_sessionization ──▶ user_sessions                 │
│                                             │                       │
│                                             ▼                       │
│                                      02_funnel ──▶ funnel_sessions  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   COHORT RETENTION (User-Based)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  users_raw ──▶ 03_cohort_users ──▶ cohort_users                     │
│                                         │                           │
│  orders_raw ──▶ 04_cohort_activity ──▶ cohort_activity              │
│                                         │                           │
│                    ┌────────────────────┴────────────────────┐      │
│                    │                                         │      │
│                    ▼                                         ▼      │
│          05_cohort_retention                     06_cohort_sizes    │
│              (cohort_retention)                   (cohort_sizes)    │
│                    │                                         │      │
│                    └────────────────────┬────────────────────┘      │
│                                         ▼                           │
│                              07_cohort_retention_rates              │
│                              (cohort_retention_rates)               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         POWER BI VIEWS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  funnel_sessions ──────────────┐                                    │
│                                ├──▶ 08_powerbi_views ──▶ v_funnel_metrics
│  cohort_retention_rates ───────┤                      ──▶ v_cohort_retention
│                                │                      ──▶ v_ab_test_summary
│                                │                      ──▶ v_ab_test_detailed
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Script Descriptions

### 01_sessionization.sql

**Input:** `events_raw`  
**Output:** `user_sessions` (table)

Groups raw clickstream events into user sessions using:
- **30-minute inactivity timeout**: New session if gap > 30 min
- **Fallback session_id**: For missing session_ids, uses `user_id || '_' || hour(ts)`
- **Session index**: Running count of sessions per user

**Key columns added:**
- `session_index`: Session number for the user (1, 2, 3, ...)
- `session_id`: Consistent session identifier

**Use case:** Foundation for all session-based analytics

---

### 02_funnel.sql

**Input:** `user_sessions`  
**Output:** `funnel_sessions` (table)

Aggregates events to session level and creates binary funnel flags:

| Flag | Meaning |
|------|---------|
| `has_visit` | Session has a visit event |
| `has_product_view` | Session has a product view |
| `has_add_to_cart` | Session has add to cart |
| `has_checkout` | Session has checkout |
| `has_purchase` | Session has purchase |

**Additional columns:**
- Session metadata (start/end timestamps, duration)
- Traffic attributes (source, device)
- A/B test fields (ab_test_id, variant)

**Use case:** Funnel analysis, A/B testing, conversion optimization

---

### 03_cohort_users.sql

**Input:** `users_raw`  
**Output:** `cohort_users` (table)

Creates base cohort table from ALL users (not just purchasers):
- **Cohort week**: Week of user signup (`DATE_TRUNC('week', signup_date)`)
- One row per user

**Critical for correct retention:** Cohort size is based on signups, ensuring retention rates never exceed 100%.

---

### 04_cohort_activity.sql

**Input:** `orders_raw`  
**Output:** `cohort_activity` (table)

Creates deduplicated purchase activity:
- **Activity week**: Week of purchase (`DATE_TRUNC('week', ts)`)
- Only successful orders (payment_status = 'success')
- One row per (user_id, activity_week) — deduplicated

**Purpose:** Tracks which weeks each user made at least one purchase.

---

### 05_cohort_retention.sql

**Input:** `cohort_users`, `cohort_activity`  
**Output:** `cohort_retention` (table)

Calculates retention counts by cohort and period:
- **Cohort index**: Weeks since signup (0 = signup week)
- **Users active**: Distinct users who purchased in that period

**Join logic:** Inner join cohort_users to cohort_activity on user_id.

---

### 06_cohort_sizes.sql

**Input:** `cohort_users`  
**Output:** `cohort_sizes` (table)

Calculates cohort size (denominator for retention):
- **Cohort size**: Total users who signed up in each cohort week
- Based on ALL signups, not just purchasers

---

### 07_cohort_retention_rates.sql

**Input:** `cohort_retention`, `cohort_sizes`  
**Output:** `cohort_retention_rates` (table)

Calculates final retention rates:
- **Retention rate**: users_active / cohort_size
- Guaranteed to be 0-1 range (never exceeds 100%)

**Key insight:** Week 0 retention shows the **conversion rate** (% of users who purchased in their signup week), not 100%.

---

### 08_powerbi_views.sql

**Input:** `funnel_sessions`, `cohort_retention_rates`  
**Output:** Views (not tables)

Creates BI-ready views for Power BI:

| View | Description |
|------|-------------|
| `v_funnel_metrics` | Funnel rates by source, device, date |
| `v_cohort_retention` | Retention rates by cohort and period |
| `v_ab_test_summary` | A/B test variant comparison |
| `v_ab_test_detailed` | Session-level A/B test data |

**Note:** All rates are 0-1 ratios (not percentages) — Power BI handles formatting.

---

## Running SQL Scripts

### Option 1: Using the materialize script (Recommended)

```bash
# Using uv
uv run python scripts/materialize_tables.py

# Using pip
python scripts/materialize_tables.py
```

This script executes all SQL files (01-07) and creates all tables with validation.

### Option 2: Manually in DuckDB CLI

```bash
# Open DuckDB
duckdb analytics.duckdb

# Execute scripts in order
.read sql/analytics/01_sessionization.sql
.read sql/analytics/02_funnel.sql
.read sql/analytics/03_cohort_users.sql
.read sql/analytics/04_cohort_activity.sql
.read sql/analytics/05_cohort_retention.sql
.read sql/analytics/06_cohort_sizes.sql
.read sql/analytics/07_cohort_retention_rates.sql
.read sql/analytics/08_powerbi_views.sql
```

### Option 3: Using Python

```python
import duckdb

conn = duckdb.connect('analytics.duckdb')

# Execute a SQL file
with open('sql/analytics/01_sessionization.sql', 'r') as f:
    conn.execute(f.read())

conn.close()
```

---

## DuckDB-Specific Notes

- Uses `DATE_TRUNC()` for date manipulation
- Uses `DATEDIFF()` for week calculations
- Uses `EXTRACT(EPOCH FROM ...)` for duration
- Window functions: `LAG()`, `SUM() OVER()`, `MIN() OVER()`
- `COALESCE()` for null handling

---

## Cohort Retention: Why User-Based Matters

### The Problem with Purchase-Based Cohorts

❌ **Wrong approach:**
```sql
-- Cohort size = users who purchased in signup week
cohort_size = COUNT(DISTINCT user_id) WHERE cohort_index = 0
```
This causes retention > 100% because later weeks can have MORE active users than signup week.

✅ **Correct approach (this project):**
```sql
-- Cohort size = ALL users who signed up
cohort_size = COUNT(DISTINCT user_id) FROM cohort_users
```
Retention can never exceed 100% because it's always `(subset) / (total signups)`.

### Example Interpretation

| cohort_week | cohort_index | users_active | cohort_size | retention_rate |
|-------------|--------------|--------------|-------------|----------------|
| 2024-01-01  | 0            | 450          | 2,500       | 0.18 (18%)     |
| 2024-01-01  | 1            | 320          | 2,500       | 0.13 (13%)     |
| 2024-01-01  | 4            | 180          | 2,500       | 0.07 (7%)      |

**Week 0 = 18%** means 18% of users who signed up that week made a purchase in their signup week. This is the **conversion rate**, not "100% retention."

---

## Validation Queries

Each SQL file contains commented validation queries at the bottom. To verify cohort retention:

```sql
-- Check no retention exceeds 100%
SELECT * FROM cohort_retention_rates WHERE retention_rate > 1.0;
-- Should return 0 rows

-- Verify week 0 is conversion rate (not 100%)
SELECT 
    AVG(retention_rate) AS avg_week0_conversion,
    MIN(retention_rate) AS min_conversion,
    MAX(retention_rate) AS max_conversion
FROM cohort_retention_rates 
WHERE cohort_index = 0;
```
