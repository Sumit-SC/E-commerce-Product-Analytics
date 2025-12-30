# E-commerce Product Analytics

> **End-to-end product analytics project** focused on user behavior, funnel analysis, cohort retention, and A/B testing — optimized for Data Analyst / Product Analyst / Analytics Engineer roles.

## 🎯 Project Overview

This project demonstrates a complete analytics workflow from raw clickstream data to actionable business insights. It processes **500k-1M realistic e-commerce events** with intentional noise (missing events, bot traffic, abandoned carts) to simulate real-world data challenges.

### Key Analytics Components

1. **Funnel Analysis** - Track user journey from Visit → Purchase with conversion rates by channel, device, and cohort
2. **Cohort Retention** - Weekly & monthly retention tables with repeat purchase curves
3. **Growth Metrics** - Conversion rate, AOV, proxy LTV calculations
4. **A/B Testing** - Statistical significance testing for variant vs control comparisons

## 🏗️ Project Structure

```
E-commerce-Product-Analytics/
├── data/              # Raw & processed data
│   ├── raw/           # Generated raw data
│   └── processed/     # SQL-processed tables
├── sql/               # SQL scripts
│   ├── raw/           # Raw data processing
│   └── analytics/     # Analytics queries
├── src/               # Data generation & analysis
├── notebooks/         # Exploratory analysis
├── streamlit/         # A/B test inspector app
├── bi/                # Power BI dashboard
└── docs/              # Documentation & insights
```

## 🛠️ Tech Stack

- **Database:** DuckDB (or PostgreSQL)
- **SQL:** Sessionization, funnel, cohorts, window functions
- **Python:** Pandas, NumPy, SciPy for analysis
- **Visualization:** Power BI (main dashboards)
- **Optional:** Streamlit for A/B test exploration
- **Package Management:** uv

## 📊 Dataset Schema

### Users Table
- `user_id`, `signup_date`, `device`, `country`

### Events Table
- `event_id`, `user_id`, `session_id`, `event_type`, `page`, `product_id`, `ts`, `source`, `device`

### Orders Table
- `order_id`, `user_id`, `product_id`, `price`, `ts`, `payment_status`

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- uv package manager
- DuckDB (or PostgreSQL)
- Power BI Desktop (for dashboards)

### Installation

```bash
# Install dependencies with uv
uv sync

# Generate sample data
uv run python src/data_generator.py

# Run SQL analytics
# (Load data into database first, then run sql/raw/*.sql then sql/analytics/*.sql)

# Launch Streamlit app (optional)
uv run streamlit run streamlit/ab_test_inspector.py
```

## 📈 Key Metrics & Insights

*(To be populated after analysis)*

- Funnel conversion rates by stage
- Cohort retention curves
- A/B test results
- Business recommendations

## 📝 Resume Bullets

*(To be refined after completion)*

- Built end-to-end product analytics pipeline processing 1M+ clickstream events
- Designed SQL-based funnel analysis identifying key drop-off points
- Implemented cohort retention analysis with weekly/monthly retention tables
- Created Power BI dashboard with interactive visualizations
- Developed A/B testing framework with statistical significance testing

## 📚 Documentation

- [Project Plan](PROJECT_PLAN.md) - Detailed implementation plan
- [Business Insights](docs/business_insights.md) - Key findings & recommendations
- [Power BI Guide](bi/README.md) - Dashboard documentation

## 🔄 Project Status

**Current Phase:** Planning Complete - Awaiting Implementation

---

**Note:** This project is designed to demonstrate real-world analytics skills with intentionally messy data to showcase data cleaning and analysis capabilities.

## Enhancements 

“For datasets exceeding local memory constraints, this pipeline can be optimized using Polars or DuckDB SQL, both of which offer vectorized execution and lower memory overhead.”
