# Scripts Directory

This directory contains executable pipeline scripts for data processing and export.

## Files

```
scripts/
├── materialize_tables.py      # Creates analytics tables in DuckDB
└── export_powerbi_data.py     # Exports views to CSV for Power BI
```

---

## materialize_tables.py

**Purpose:** Execute SQL transformation scripts and materialize analytics tables in DuckDB

**Executes (in order):**
1. `sql/analytics/01_sessionization.sql` → creates `user_sessions`
2. `sql/analytics/02_funnel.sql` → creates `funnel_sessions`
3. `sql/analytics/03_cohorts.sql` → creates `purchase_cohorts`

**Prerequisites:**
- Raw tables must exist (`users_raw`, `events_raw`, `orders_raw`)
- Run `src/load_to_db.py` first

**Usage:**

```bash
# Using uv (recommended)
uv run python scripts/materialize_tables.py

# Using pip
python scripts/materialize_tables.py
```

**Output:**
```
============================================================
MATERIALIZING ANALYTICS TABLES
============================================================
Database: analytics.duckdb

Executing: sql/analytics/01_sessionization.sql
[OK] user_sessions created: 394,521 rows

Executing: sql/analytics/02_funnel.sql
[OK] funnel_sessions created: 394,521 rows

Executing: sql/analytics/03_cohorts.sql
[OK] purchase_cohorts created: 85,432 rows

============================================================
MATERIALIZATION COMPLETE
============================================================
```

---

## export_powerbi_data.py

**Purpose:** Export Power BI-ready views from DuckDB to CSV files

**Prerequisites:**
- Analytics tables must exist (run `materialize_tables.py` first)
- Views must be created (run `sql/analytics/06_powerbi_views.sql`)

**Exports:**

| View | Output File | Rows |
|------|-------------|------|
| `v_funnel_metrics` | `data/powerbi/funnel_metrics.csv` | ~8,000 |
| `v_cohort_retention` | `data/powerbi/cohort_retention.csv` | ~2,000 |
| `v_ab_test_summary` | `data/powerbi/ab_test_summary.csv` | 3-4 |

**Usage:**

```bash
# Using uv (recommended)
uv run python scripts/export_powerbi_data.py

# Using pip
python scripts/export_powerbi_data.py
```

**Output:**
```
============================================================
EXPORT POWER BI DATA
============================================================
Database: analytics.duckdb
Output directory: data/powerbi

[OK] Output directory ready
[OK] Connected to database

------------------------------------------------------------
Exporting views...
------------------------------------------------------------
[OK] v_funnel_metrics -> funnel_metrics.csv (8,243 rows)
[OK] v_cohort_retention -> cohort_retention.csv (2,013 rows)
[OK] v_ab_test_summary -> ab_test_summary.csv (3 rows)

============================================================
EXPORT COMPLETE
============================================================
Files saved to: data/powerbi
```

---

## Full Pipeline Execution

Run the complete pipeline from raw data to Power BI export:

### Using uv

```bash
# Step 1: Generate raw data
uv run python src/data_generator.py

# Step 2: Load to DuckDB
uv run python src/load_to_db.py

# Step 3: Create analytics tables
uv run python scripts/materialize_tables.py

# Step 4: Create Power BI views (one-time)
uv run python -c "import duckdb; conn = duckdb.connect('analytics.duckdb'); conn.execute(open('sql/analytics/06_powerbi_views.sql').read()); conn.close(); print('Views created')"

# Step 5: Export to CSV
uv run python scripts/export_powerbi_data.py
```

### Using pip

```bash
# Activate virtual environment first
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Step 1: Generate raw data
python src/data_generator.py

# Step 2: Load to DuckDB
python src/load_to_db.py

# Step 3: Create analytics tables
python scripts/materialize_tables.py

# Step 4: Create Power BI views (one-time)
python -c "import duckdb; conn = duckdb.connect('analytics.duckdb'); conn.execute(open('sql/analytics/06_powerbi_views.sql').read()); conn.close(); print('Views created')"

# Step 5: Export to CSV
python scripts/export_powerbi_data.py
```

---

## Troubleshooting

### ModuleNotFoundError: No module named 'duckdb'

**Cause:** Running Python outside of the virtual environment

**Fix:** Use `uv run` or activate the virtual environment:
```bash
# Using uv
uv run python scripts/materialize_tables.py

# Using pip (activate first)
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
python scripts/materialize_tables.py
```

### Table does not exist

**Cause:** Running scripts out of order

**Fix:** Follow the pipeline order:
1. `src/data_generator.py` (creates CSVs)
2. `src/load_to_db.py` (creates raw tables)
3. `scripts/materialize_tables.py` (creates analytics tables)
4. `scripts/export_powerbi_data.py` (exports views)

### View does not exist

**Cause:** Power BI views not created

**Fix:** Run the views SQL file:
```bash
uv run python -c "import duckdb; conn = duckdb.connect('analytics.duckdb'); conn.execute(open('sql/analytics/06_powerbi_views.sql').read()); conn.close()"
```

