# E-commerce Product Analytics - Project Plan

## 🎯 Project Overview

**Goal:** Build a realistic, end-to-end product analytics project focused on user behavior, funnel drop-offs, cohort retention, and experimentation insights — optimized for Data Analyst / Product Analyst / Analytics Engineer roles.

**Timeline:** 1.5-2 days  
**Tech Stack:** SQL + Python + Power BI + Streamlit (optional)

---

## 📊 Dataset Requirements

### Scale & Quality
- **500k-1M clickstream + order events** (realistic, messy data)
- **Noise injection:** Missing events, duplicate sessions, bot traffic, abandoned carts
- **NOT clean Kaggle toy data** — industry-like complexity

### Data Schema

#### 1. `users` Table
```
- user_id (PK)
- signup_date
- device (mobile/desktop/tablet)
- country
```

#### 2. `events` Table
```
- event_id (PK)
- user_id (FK)
- session_id
- event_type (visit, product_view, add_to_cart, checkout_start, purchase)
- page (URL/page name)
- product_id
- ts (timestamp)
- source (organic, paid_search, social, email, direct)
- device
```

#### 3. `orders` Table
```
- order_id (PK)
- user_id (FK)
- product_id
- price
- ts (timestamp)
- payment_status (completed, failed, refunded)
```

---

## 🏗️ Project Structure

```
E-commerce-Product-Analytics/
├── data/
│   ├── raw/                    # Generated raw data
│   └── processed/              # SQL-processed tables
├── sql/
│   ├── raw/                    # Raw data processing scripts
│   │   ├── 01_sessionization.sql   # Session creation logic
│   │   └── 02_data_cleaning.sql    # Handle missing events, duplicates
│   └── analytics/              # Analytics queries
│       ├── 01_funnel_analysis.sql  # Funnel conversion queries
│       ├── 02_cohort_retention.sql # Cohort & retention tables
│       └── 03_ab_test_analysis.sql # A/B test queries
├── src/
│   ├── data_generator.py       # Event simulator (500k-1M rows)
│   ├── cohort_analysis.py      # Cohort pivot & retention curves
│   ├── ab_test_analysis.py     # Statistical significance testing
│   └── utils.py                # Helper functions
├── notebooks/
│   └── exploratory_analysis.ipynb  # Data exploration
├── streamlit/
│   └── ab_test_inspector.py    # Mini A/B test explorer app
├── bi/
│   ├── data_model.pbix         # Power BI dashboard
│   └── README.md               # Dashboard guide
├── docs/
│   └── business_insights.md    # Key findings & recommendations
├── README.md                   # Project summary & resume bullets
├── pyproject.toml              # uv dependencies
└── requirements.txt           # pip compatibility (uses uv)
```

---

## 🔍 Core Analytics Components

### 1. Funnel Analysis
**Goal:** Track user journey from Visit → Purchase

**Metrics:**
- Conversion % at each stage
- Drop-off analysis by:
  - Channel (organic, paid_search, social, email, direct)
  - Device (mobile, desktop, tablet)
  - User cohort (signup week/month)
  - Product category

**SQL Approach:**
- Sessionization: Group events by user + session
- Funnel stages: Identify event sequence per session
- Window functions: Calculate conversion rates
- CTEs: Build multi-stage funnel logic

**Visualization:** Power BI funnel chart with drill-downs

---

### 2. Cohort Retention
**Goal:** Measure user engagement over time

**Metrics:**
- Weekly & monthly retention tables
- Repeat purchase curves
- Cohort size trends
- Retention by acquisition channel

**SQL Approach:**
- Cohort assignment: Group users by signup period
- Period calculation: Weeks/months since signup
- Retention calculation: % active in period N
- Window functions: Lag/lead for period comparisons

**Python Processing:**
- Pivot tables: Cohort × Period matrix
- Heatmap visualization prep
- Retention curve plotting

**Visualization:** Power BI retention heatmap

---

### 3. Growth Metrics
**Goal:** Track business KPIs

**Metrics:**
- Conversion Rate (Visits → Purchases)
- Average Order Value (AOV)
- Proxy Lifetime Value (LTV) — based on repeat purchase patterns
- Revenue per User (RPU)
- Daily/Monthly Active Users (DAU/MAU)

**SQL Approach:**
- Aggregations: SUM, AVG, COUNT
- Date truncation: Daily/weekly/monthly grouping
- User-level aggregations: Calculate per-user metrics

**Visualization:** Power BI KPI cards + time series

---

### 4. A/B Testing
**Goal:** Compare variant vs control performance

**Test Design:**
- Variant: New checkout flow / product page / pricing
- Control: Original experience
- Metric: Conversion rate, AOV, checkout completion

**Analysis:**
- Basic significance testing:
  - Z-test for proportions (conversion rate)
  - Bootstrap resampling (for non-normal distributions)
  - Confidence intervals
- Effect size calculation
- Sample size considerations

**Python Processing:**
- Statistical tests (scipy.stats)
- Bootstrap simulation
- Visualization: Distribution comparisons

**Visualization:** Streamlit app + Power BI comparison charts

---

## 🛠️ Technical Implementation Plan

### Phase 1: Data Generation
**Tool:** Python (`data_generator.py`)

**Features:**
- Realistic user behavior simulation:
  - Session patterns (bounce, multi-page, purchase)
  - Product browsing patterns
  - Cart abandonment rates (~70%)
  - Purchase conversion (~2-5%)
- Noise injection:
  - Missing events (5-10% random)
  - Duplicate sessions (1-2%)
  - Bot traffic (3-5% of sessions)
  - Failed payments (5% of orders)
- Temporal patterns:
  - Daily/weekly seasonality
  - Growth trends
  - Event clustering

**Output:** CSV files → Load into database

---

### Phase 2: Database Setup
**Database:** DuckDB (lightweight) or PostgreSQL

**Tables:**
1. Raw tables: `users`, `events`, `orders`
2. Analytics tables:
   - `user_sessions` (sessionized events)
   - `funnel_stages` (funnel progression)
   - `cohorts` (user cohort assignments)
   - `retention_matrix` (cohort × period)
   - `ab_test_assignments` (variant assignments)

**SQL Scripts:**
- Sessionization logic (30-min timeout)
- Funnel stage identification
- Cohort calculation
- Retention aggregation

---

### Phase 3: SQL Analytics
**Scripts:** 
- Raw processing: `sql/raw/*.sql`
- Analytics: `sql/analytics/*.sql`

**Key SQL Patterns:**
- Window functions: `ROW_NUMBER()`, `LAG()`, `LEAD()`
- CTEs: Multi-step transformations
- Date functions: `DATE_TRUNC()`, `DATE_PART()`
- Aggregations: `COUNT(DISTINCT)`, `SUM()`, `AVG()`
- Joins: User → Events → Orders

---

### Phase 4: Python Analysis
**Scripts:** `src/cohort_analysis.py`, `ab_test_analysis.py`

**Libraries:**
- `pandas`: Data manipulation, pivots
- `numpy`: Statistical calculations
- `scipy`: Hypothesis testing
- `matplotlib/seaborn`: Visualizations

**Outputs:**
- Cohort retention matrices (CSV)
- A/B test results (JSON/CSV)
- Statistical summaries

---

### Phase 5: Power BI Dashboard
**Components:**
1. **Funnel Visualization**
   - Multi-stage funnel chart
   - Slicers: Channel, Device, Date Range
   - Tooltips: Conversion %, drop-off %

2. **Retention Heatmap**
   - Cohort × Period matrix
   - Color intensity = retention %
   - Filters: Cohort size, acquisition channel

3. **Conversion Analysis**
   - Bar charts: Conversion by channel/device
   - Time series: Conversion trends
   - Comparison: Period-over-period

4. **A/B Test Results**
   - Side-by-side comparison
   - Statistical significance indicators
   - Effect size visualization

**Data Model:**
- Star schema: Fact tables (events, orders) → Dim tables (users, products, dates)
- Relationships: User → Events, Events → Orders

---

### Phase 6: Streamlit App (Optional)
**File:** `streamlit/ab_test_inspector.py`

**Features:**
- Upload A/B test data
- Select metrics (conversion rate, AOV)
- Run statistical tests
- Visualize distributions
- Export results

**UI:**
- Sidebar: Filters & test selection
- Main area: Charts & tables
- Results panel: Significance, effect size

---

## 📦 Dependencies (uv)

```toml
[project]
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
    "duckdb>=0.9.0",  # or psycopg2-binary for PostgreSQL
    "streamlit>=1.28.0",
    "jupyter>=1.0.0",
]
```

---

## 📝 Deliverables Checklist

### Code & Scripts
- [ ] `data_generator.py` - Event simulator
- [ ] SQL scripts (4 files) - Sessionization, funnel, cohort, A/B
- [ ] Python analysis scripts - Cohort & A/B testing
- [ ] Streamlit app (optional) - A/B test inspector

### Data & Database
- [ ] Raw data files (CSV) - 500k-1M events
- [ ] Database schema & load scripts
- [ ] Processed analytics tables

### Visualizations
- [ ] Power BI dashboard (.pbix)
- [ ] Dashboard documentation
- [ ] Sample visualizations (screenshots)

### Documentation
- [ ] README.md - Project summary & resume bullets
- [ ] `docs/business_insights.md` - Key findings & recommendations
- [ ] Code comments & docstrings

---

## 🎯 Resume-Ready Project Summary

**Key Bullets (to be refined):**
- Built end-to-end product analytics pipeline processing 1M+ clickstream events
- Designed SQL-based funnel analysis identifying 67% drop-off at checkout stage
- Implemented cohort retention analysis revealing 35% 30-day retention for Q1 signups
- Created Power BI dashboard with interactive funnel, retention heatmap, and conversion analysis
- Developed A/B testing framework with statistical significance testing (z-test, bootstrap)
- Generated realistic e-commerce dataset with noise injection (missing events, bot traffic, abandoned carts)
- Optimized SQL queries using window functions and CTEs for sessionization and cohort calculations

---

## 🚀 Next Steps

1. **Review & Approve Plan** - Confirm approach and structure
2. **Phase 1: Data Generation** - Build event simulator
3. **Phase 2: Database Setup** - Create schema & load data
4. **Phase 3: SQL Analytics** - Write sessionization & funnel queries
5. **Phase 4: Python Analysis** - Cohort pivots & A/B testing
6. **Phase 5: Power BI** - Build dashboard
7. **Phase 6: Streamlit** - Optional A/B test app
8. **Documentation** - README & business insights

---

## 📌 Notes

- **Database Choice:** DuckDB recommended for simplicity (single file, fast analytics), but PostgreSQL more realistic for production
- **Data Quality:** Intentionally messy to demonstrate real-world data cleaning skills
- **ML-Lite:** Only basic statistical tests, no heavy ML models
- **Focus:** Analytics engineering & business insights over pure data science

---

**Status:** Planning Complete - Awaiting Approval to Proceed

