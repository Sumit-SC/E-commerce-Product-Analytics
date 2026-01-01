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
    ├── 03_cohorts.sql          # Cohort base table
    ├── 04_cohort_retention_query.sql   # Retention counts (query only)
    ├── 05_cohort_retention_rates.sql   # Retention percentages (query only)
    └── 06_powerbi_views.sql    # BI-ready views for Power BI
```

---

## Script Execution Order

Scripts must be executed in order due to table dependencies:

```
events_raw ──▶ 01_sessionization ──▶ user_sessions
                                            │
                                            ▼
                                     02_funnel ──▶ funnel_sessions
                                                         │
                                                         ▼
                                                  06_powerbi_views ──▶ v_funnel_metrics
                                                                   ──▶ v_ab_test_summary

orders_raw + users_raw ──▶ 03_cohorts ──▶ purchase_cohorts
                                                │
                                                ▼
                                         04/05_retention ──▶ (queries)
                                                │
                                                ▼
                                         06_powerbi_views ──▶ v_cohort_retention
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

### 03_cohorts.sql

**Input:** `orders_raw`, `users_raw`  
**Output:** `purchase_cohorts` (table)

Creates cohort base table for retention analysis:
- **Cohort week**: Week of user signup (`DATE_TRUNC('week', signup_date)`)
- **Activity week**: Week of purchase (`DATE_TRUNC('week', ts)`)
- One row per (user_id, activity_week)

**Use case:** Cohort retention analysis, repeat purchase curves

---

### 04_cohort_retention_query.sql

**Input:** `purchase_cohorts`  
**Output:** Query results (no table created)

Calculates retention counts:
- **Cohort index**: Weeks since signup (0 = signup week)
- **Users active**: Distinct users active in each period

**Use case:** Intermediate step for retention rate calculation

---

### 05_cohort_retention_rates.sql

**Input:** `purchase_cohorts`  
**Output:** Query results (no table created)

Calculates retention rates:
- **Cohort size**: Users in signup week (cohort_index = 0)
- **Retention rate**: users_active / cohort_size

**Use case:** Retention heatmaps, cohort comparison

---

### 06_powerbi_views.sql

**Input:** `funnel_sessions`, `purchase_cohorts`  
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

This script executes 01-03 SQL files and creates tables.

### Option 2: Manually in DuckDB CLI

```bash
# Open DuckDB
duckdb analytics.duckdb

# Execute scripts
.read sql/analytics/01_sessionization.sql
.read sql/analytics/02_funnel.sql
.read sql/analytics/03_cohorts.sql
.read sql/analytics/06_powerbi_views.sql
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

## Validation Queries

Each SQL file contains commented validation queries at the bottom. Uncomment and run to verify:

```sql
-- Example: Funnel conversion rates
SELECT
    COUNT(*) AS total_sessions,
    SUM(has_purchase) AS purchases,
    ROUND(SUM(has_purchase)::DOUBLE / COUNT(*) * 100, 2) AS purchase_rate_pct
FROM funnel_sessions;
```
