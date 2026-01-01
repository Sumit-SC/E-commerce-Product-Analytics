# Source Modules (`src/`)

This directory contains Python source modules for data generation, loading, and analysis.

## Files

```
src/
├── data_generator.py      # Simulates realistic e-commerce data
├── load_to_db.py          # Loads CSVs into DuckDB
└── cohort_analysis.py     # Cohort retention analysis helper
```

---

## data_generator.py

**Purpose:** Generate realistic e-commerce simulation data (users, events, orders)

**Output:**
- `data/raw/users.csv` (~120,000 rows)
- `data/raw/events.csv` (~1,000,000 rows)
- `data/raw/orders.csv` (~45,000 rows)

**Key Features:**
- **Deterministic output**: Uses random seed for reproducibility
- **Session-first funnel logic**: Events follow realistic funnel progression
- **A/B test assignment**: Users split 50/50 into control/variant
- **Noise injection**: Missing session_ids, bot traffic, duplicate sessions
- **Realistic distributions**: Lognormal prices, device/country skew

**Usage:**

```bash
# Using uv
uv run python src/data_generator.py

# Using pip
python src/data_generator.py
```

**Funnel Probabilities:**
| Step | Probability |
|------|-------------|
| visit → product_view | 75-85% |
| product_view → add_to_cart | 30-40% |
| add_to_cart → checkout | 45-55% |
| checkout → purchase (control) | ~85% |
| checkout → purchase (variant) | ~92% |

---

## load_to_db.py

**Purpose:** Load raw CSV files into DuckDB with proper schema

**Input:** `data/raw/users.csv`, `events.csv`, `orders.csv`

**Output:** DuckDB tables in `analytics.duckdb`
- `users_raw`
- `events_raw`
- `orders_raw`

**Key Features:**
- Explicit type casting (INTEGER, TIMESTAMP, VARCHAR, DOUBLE)
- Creates indexes for query performance
- Overwrites existing tables (idempotent)
- Validates row counts and distributions

**Usage:**

```bash
# Using uv
uv run python src/load_to_db.py

# Using pip
python src/load_to_db.py
```

**Schema:**

```sql
-- users_raw
user_id INTEGER, signup_date DATE, device VARCHAR, 
country VARCHAR, loyalty_tier VARCHAR

-- events_raw  
event_id VARCHAR, user_id INTEGER, session_id VARCHAR,
event_type VARCHAR, page VARCHAR, product_id INTEGER,
product_category VARCHAR, ts TIMESTAMP, source VARCHAR,
device VARCHAR, ab_test_id VARCHAR, variant VARCHAR

-- orders_raw
order_id VARCHAR, user_id INTEGER, product_id INTEGER,
product_category VARCHAR, price DOUBLE, quantity INTEGER,
discount_amount DOUBLE, ts TIMESTAMP, payment_status VARCHAR
```

---

## cohort_analysis.py

**Purpose:** Helper module for loading and preparing cohort retention data

**Input:** Executes `sql/analytics/05_cohort_retention_rates.sql` against DuckDB

**Output:** Pandas DataFrame with retention matrix

**Key Features:**
- Connects to DuckDB and executes retention query
- Pivots data into retention matrix format
- Sorts cohorts chronologically

**Usage:**

```python
# Import and use in notebooks
from cohort_analysis import load_retention_data

retention_matrix = load_retention_data()
print(retention_matrix.head())
```

**Or run directly:**

```bash
# Using uv
uv run python src/cohort_analysis.py

# Using pip
python src/cohort_analysis.py
```

---

## Dependencies

All modules require:
- `pandas`
- `numpy`
- `duckdb`

Install via:

```bash
# Using uv
uv sync

# Using pip
pip install -r requirements.txt
```

---

## Module Relationships

```
data_generator.py
        │
        │ generates
        ▼
   data/raw/*.csv
        │
        │ loaded by
        ▼
   load_to_db.py
        │
        │ creates
        ▼
   analytics.duckdb (users_raw, events_raw, orders_raw)
        │
        │ queried by
        ▼
   cohort_analysis.py ──▶ retention DataFrame for notebooks
```

---

## Adding New Modules

When adding new source modules:

1. Place in `src/` directory
2. Use relative imports sparingly (prefer absolute paths)
3. Add `if __name__ == "__main__":` block for standalone execution
4. Update this README with module description
