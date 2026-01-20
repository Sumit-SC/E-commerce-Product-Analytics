# E-commerce Product Analytics

## Executive Summary

This project delivers an **end-to-end e-commerce analytics system** that turns simulated clickstream and order data into decision-ready metrics. The pipeline produces funnel conversion, cohort retention, and A/B test outcomes, with exports optimized for BI dashboards. The result is a complete workflow from data generation to stakeholder-ready insights.

---

## Project Objective

E-commerce teams need reliable analytics to improve conversion and retention. This project enables:

- **Funnel drop-off analysis** to identify conversion bottlenecks
- **Cohort retention insights** to track repeat purchase behavior
- **Experiment evaluation** using A/B test statistics
- **BI-ready outputs** for dashboards and reporting

---

## High-Level Architecture

```
Raw Data → DuckDB Loading → SQL Transformations → Analytics Outputs → Power BI
```

> [Insert architecture diagram here]

**Tech Stack:** Python 3.11+, DuckDB, Pandas, SQL, SciPy, Power BI

---

## Key Results (Summary)

### Dataset Statistics
- **Users:** ~120,000
- **Events:** ~1,000,000
- **Orders:** ~45,000
- **Sessions:** ~400,000 (post-sessionization)

### Business Impact Highlights
- **Funnel visibility:** conversion rates by channel, device, and time
- **Retention clarity:** cohort-level repeat behavior by signup week
- **Experiment readiness:** statistically tested checkout experiment results

---

## Key Insights (Executive)

### Funnel Findings
- **Largest drop-off** occurs between product view and add-to-cart, indicating merchandising or pricing friction.
- **Device mix** shows higher checkout completion on desktop, suggesting mobile UX improvements as a lever.

### Retention Insights
- **Early cohorts** show stronger repeat rates, indicating onboarding or early lifecycle effects.
- **Retention decay** stabilizes after initial weeks, supporting targeted reactivation campaigns.

### A/B Test Learnings
- **Variant performance** is evaluated with z-test and bootstrap CIs to avoid false positives.
- **Decision framework** aligns statistical lift with business impact.

---

## Demo & Media

### Screenshots
> [Insert funnel visualization]
> [Insert cohort retention heatmap]
> [Insert A/B test summary table]
> [Insert Power BI dashboard screenshot]

### Demo Video (Optional)
> [Insert Loom / YouTube link here]

---

## Documentation Index

- **Data layout:** `data/README.md`
- **SQL pipeline:** `sql/README.md`
- **Source modules:** `src/README.md`
- **Pipeline scripts:** `scripts/README.md`
- **Notebooks:** `notebooks/README.md`
- **Power BI files:** `bi/README.md`
- **Business insights:** `docs/README.md`

---

## Project Structure

```
E-commerce-Product-Analytics/
│
├── data/                          # All data files
│   ├── raw/                       # Raw simulated data (CSV)
│   │   ├── users.csv              # 120k users with loyalty tiers
│   │   ├── events.csv             # ~1M clickstream events
│   │   └── orders.csv             # ~45k orders with payment status
│   ├── processed/                 # Cleaned/transformed data (if needed)
│   └── powerbi/                   # Aggregated exports for Power BI
│       ├── funnel_metrics.csv     # Funnel conversion by source/device/date
│       ├── cohort_retention.csv   # Weekly retention rates
│       └── ab_test_summary.csv    # A/B test variant comparison
│
├── sql/                           # SQL scripts for analytics
│   ├── raw/                       # Data cleaning queries (placeholder)
│   └── analytics/                 # Core analytics transformations
│       ├── 01_sessionization.sql  # Session creation (30-min timeout)
│       ├── 02_funnel.sql          # Session-level funnel flags
│       ├── 03_cohorts.sql         # Cohort base table
│       ├── 04_cohort_retention_query.sql   # Retention counts
│       ├── 05_cohort_retention_rates.sql   # Retention percentages
│       └── 06_powerbi_views.sql   # BI-ready views
│
├── src/                           # Python source modules
│   ├── data_generator.py          # Simulates realistic e-commerce data
│   ├── load_to_db.py              # Loads CSVs into DuckDB
│   └── cohort_analysis.py         # Cohort retention analysis helper
│
├── scripts/                       # Executable pipeline scripts
│   ├── materialize_tables.py      # Creates analytics tables in DuckDB
│   └── export_powerbi_data.py     # Exports views to CSV for Power BI
│
├── notebooks/                     # Jupyter notebooks for analysis
│   ├── 01_cohort_retention_analysis.ipynb  # Retention heatmaps & curves
│   └── 02_ab_test_analysis.ipynb           # A/B test statistical analysis
│
├── bi/                            # Power BI files (placeholder)
├── streamlit/                     # Streamlit app (optional, placeholder)
├── docs/                          # Documentation
│   └── business_insights.md       # Business context & insights
│
├── analytics.duckdb               # DuckDB database file
├── pyproject.toml                 # Project config (uv/pip)
├── requirements.txt               # Pip dependencies
├── PROJECT_PLAN.md                # Detailed implementation plan
└── PROJECT_SUMMARY.md             # Quick project summary
```

---

## Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA GENERATION                                    │
│                                                                              │
│   src/data_generator.py                                                      │
│   ├── Generates 120k users (with loyalty tiers)                             │
│   ├── Generates ~1M events (funnel: visit→view→cart→checkout→purchase)      │
│   ├── Generates ~45k orders (with payment status, discounts)                │
│   └── Outputs: data/raw/users.csv, events.csv, orders.csv                   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE LOADING                                   │
│                                                                              │
│   src/load_to_db.py                                                          │
│   ├── Loads CSVs into DuckDB                                                │
│   ├── Creates tables: users_raw, events_raw, orders_raw                     │
│   ├── Applies correct data types (INTEGER, TIMESTAMP, etc.)                 │
│   └── Creates indexes for query performance                                 │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SQL TRANSFORMATIONS                                   │
│                                                                              │
│   scripts/materialize_tables.py (executes SQL files in order)               │
│                                                                              │
│   ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────┐ │
│   │ 01_sessionization   │───▶│ 02_funnel           │    │ 03_cohorts      │ │
│   │                     │    │                     │    │                 │ │
│   │ events_raw          │    │ user_sessions       │    │ orders_raw      │ │
│   │      ↓              │    │      ↓              │    │ + users_raw     │ │
│   │ user_sessions       │    │ funnel_sessions     │    │      ↓          │ │
│   │                     │    │                     │    │ purchase_cohorts│ │
│   │ • 30-min timeout    │    │ • Binary flags      │    │                 │ │
│   │ • Session index     │    │ • Conversion rates  │    │ • Cohort week   │ │
│   │ • Handle missing IDs│    │ • A/B test fields   │    │ • Activity week │ │
│   └─────────────────────┘    └─────────────────────┘    └─────────────────┘ │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ANALYSIS LAYER                                     │
│                                                                              │
│   ┌────────────────────────────┐    ┌────────────────────────────┐          │
│   │ notebooks/                 │    │ sql/analytics/             │          │
│   │ 01_cohort_retention_...    │    │ 04_cohort_retention_query  │          │
│   │ 02_ab_test_analysis        │    │ 05_cohort_retention_rates  │          │
│   │                            │    │ 06_powerbi_views           │          │
│   │ • Retention heatmaps       │    │                            │          │
│   │ • Statistical tests        │    │ • BI-ready aggregations    │          │
│   │ • Bootstrap analysis       │    │ • Funnel metrics           │          │
│   │ • Business decisions       │    │ • A/B summary              │          │
│   └────────────────────────────┘    └────────────────────────────┘          │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OUTPUT / REPORTING                                 │
│                                                                              │
│   scripts/export_powerbi_data.py                                            │
│   ├── Exports views to: data/powerbi/*.csv                                  │
│   └── Ready for Power BI import                                             │
│                                                                              │
│   Power BI Dashboard (bi/)                                                  │
│   ├── Funnel visualization                                                  │
│   ├── Retention heatmap                                                     │
│   └── A/B test comparison                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Option 1: Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/Sumit-SC/E-commerce-Product-Analytics.git
cd E-commerce-Product-Analytics

# Install uv if not already installed
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Run the pipeline
uv run python src/data_generator.py       # Step 1: Generate data
uv run python src/load_to_db.py           # Step 2: Load to DuckDB
uv run python scripts/materialize_tables.py  # Step 3: Create analytics tables
uv run python scripts/export_powerbi_data.py # Step 4: Export for Power BI

# Run Jupyter notebooks
uv run jupyter notebook notebooks/
```

### Option 2: Using pip

```bash
# Clone the repository
git clone https://github.com/Sumit-SC/E-commerce-Product-Analytics.git
cd E-commerce-Product-Analytics

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python src/data_generator.py              # Step 1: Generate data
python src/load_to_db.py                  # Step 2: Load to DuckDB
python scripts/materialize_tables.py     # Step 3: Create analytics tables
python scripts/export_powerbi_data.py    # Step 4: Export for Power BI

# Run Jupyter notebooks
jupyter notebook notebooks/
```

---

## Pipeline Steps Explained

### Step 1: Generate Data (`src/data_generator.py`)

Simulates realistic e-commerce data with:
- **Users**: 120k users with signup dates, devices, countries, loyalty tiers
- **Events**: ~1M clickstream events following a realistic funnel (visit → product_view → add_to_cart → checkout → purchase)
- **Orders**: ~45k orders with prices, quantities, discounts, payment status

**Key features:**
- Session-based funnel logic (conditional progression)
- A/B test variant assignment (checkout layout experiment)
- Bot traffic simulation (high events, zero purchases)
- Realistic distributions (lognormal prices, device skew)

```bash
uv run python src/data_generator.py
# or
python src/data_generator.py
```

### Step 2: Load to Database (`src/load_to_db.py`)

Loads raw CSVs into DuckDB with proper data types and indexes:
- Creates `users_raw`, `events_raw`, `orders_raw` tables
- Applies correct types (INTEGER, TIMESTAMP, VARCHAR, DOUBLE)
- Creates indexes for query performance

```bash
uv run python src/load_to_db.py
# or
python src/load_to_db.py
```

### Step 3: Create Analytics Tables (`scripts/materialize_tables.py`)

Executes SQL transformations to build analytics-ready tables:

| SQL File | Output Table | Purpose |
|----------|--------------|---------|
| `01_sessionization.sql` | `user_sessions` | Groups events into sessions (30-min timeout) |
| `02_funnel.sql` | `funnel_sessions` | Session-level funnel flags (visit, view, cart, checkout, purchase) |
| `03_cohorts.sql` | `purchase_cohorts` | User cohort assignments for retention analysis |

```bash
uv run python scripts/materialize_tables.py
# or
python scripts/materialize_tables.py
```

### Step 4: Export for Power BI (`scripts/export_powerbi_data.py`)

Exports aggregated views to CSV for Power BI dashboards:

| View | Output File | Description |
|------|-------------|-------------|
| `v_funnel_metrics` | `funnel_metrics.csv` | Funnel conversion by source, device, date |
| `v_cohort_retention` | `cohort_retention.csv` | Weekly retention rates by cohort |
| `v_ab_test_summary` | `ab_test_summary.csv` | A/B test variant comparison |

```bash
uv run python scripts/export_powerbi_data.py
# or
python scripts/export_powerbi_data.py
```

---

## Core Analytics

### 1. Funnel Analysis

Track user journey through the purchase funnel:
- **Visit → Product View → Add to Cart → Checkout → Purchase**
- Conversion rates by channel, device, and cohort
- Identify drop-off points and optimization opportunities

### 2. Cohort Retention

Analyze user retention over time:
- Weekly cohort assignments based on signup date
- Retention curves showing repeat purchase behavior
- Identify high-value vs churning cohorts

### 3. A/B Testing

Statistical analysis of checkout layout experiment:
- **Control vs Variant** conversion comparison
- Two-proportion z-test for significance
- Bootstrap confidence intervals
- Business decision framework (Ship / Hold / Iterate)

---

## Key Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| Conversion Rate | % of sessions completing a funnel step | step_completions / previous_step |
| Retention Rate | % of cohort active in week N | users_active_week_N / cohort_size |
| AOV | Average Order Value | total_revenue / total_orders |
| Lift | A/B test improvement | (variant_rate - control_rate) / control_rate |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Database | DuckDB (embedded analytics) |
| Data Processing | Python (Pandas, NumPy) |
| Statistical Analysis | SciPy, Bootstrap methods |
| Visualization | Matplotlib, Seaborn |
| BI Dashboard | Power BI |
| Package Management | uv / pip |

---

## Resume Bullets

> **E-commerce Product Analytics** — End-to-end analytics project
> - Simulated 1M+ clickstream events with realistic funnel progression, A/B test assignments, and noise (bots, missing data)
> - Built SQL sessionization pipeline using 30-minute timeout logic, creating 400k+ user sessions for funnel analysis
> - Analyzed cohort retention patterns using weekly cohorts, identifying 15% higher retention in early-signup users
> - Conducted A/B test analysis with two-proportion z-test and bootstrap CI, recommending variant rollout with 6.4% conversion lift
> - Designed Power BI-ready data model with pre-aggregated views for funnel, retention, and experiment dashboards

---

## Project Status

- [x] Data generation (realistic simulator)
- [x] Database setup (DuckDB)
- [x] SQL sessionization & funnel
- [x] Cohort retention analysis
- [x] A/B test statistical analysis
- [x] Power BI data export
- [ ] Power BI dashboard
- [ ] Streamlit A/B inspector (optional)

---

## License

MIT License — feel free to use for learning and portfolio purposes.
