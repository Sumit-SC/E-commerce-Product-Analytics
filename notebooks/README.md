# Notebooks Directory

This directory contains Jupyter notebooks for exploratory analysis and statistical testing.

## Files

```
notebooks/
├── 01_cohort_retention_analysis.ipynb    # Retention heatmaps & curves
├── 02_ab_test_analysis.ipynb             # A/B test statistical analysis
└── analytics.duckdb                      # Notebook-local DB copy (auto-created)
```

---

## 01_cohort_retention_analysis.ipynb

**Purpose:** Analyze user retention patterns using cohort analysis

**Sections:**
1. **Data Loading** — Connect to DuckDB, load cohort retention data
2. **Descriptive Statistics** — Cohort sizes, retention distribution
3. **Retention Heatmap** — Visual matrix of retention by cohort and period
4. **Retention Curves** — Line plots for selected cohorts
5. **Mean vs Median Retention** — Statistical comparison
6. **Early vs Late Cohorts** — Behavior differences by signup time
7. **Drop-off Analysis** — Identify sharp retention declines
8. **Summary & Insights** — Business interpretations

**Key Outputs:**
- Retention heatmap visualization
- Cohort performance comparison
- Drop-off point identification
- Business recommendations

---

## 02_ab_test_analysis.ipynb

**Purpose:** Statistical analysis of checkout layout A/B test

**Sections:**
1. **Data Loading** — Load experiment data from `funnel_sessions`
2. **Sanity Checks** — Sample size, conversion rate, class balance
3. **EDA & Uncertainty** — Conversion rates with standard error bars
4. **Descriptive Statistics** — Boxplots, variance comparison
5. **Hypothesis Testing** — Two-proportion z-test
6. **Confidence Interval** — 95% CI for conversion difference
7. **Bootstrap Analysis** — Non-parametric uplift distribution
8. **Decision Framework** — Practical vs statistical significance
9. **Recommendation** — Ship / Hold / Iterate decision

**Key Outputs:**
- Z-test results (z-statistic, p-value)
- Effect size (Cohen's h)
- 95% confidence interval
- Bootstrap distribution plot
- Business recommendation

**Statistical Methods:**
- Two-proportion z-test (large sample)
- Bootstrap resampling (10,000 samples)
- Cohen's h for effect size
- Confidence interval interpretation

---

## Prerequisites

Before running notebooks, ensure:

1. **Analytics tables exist** in DuckDB:
   - `user_sessions`
   - `funnel_sessions`
   - `purchase_cohorts`

2. **Run materialization script:**
   ```bash
   uv run python scripts/materialize_tables.py
   ```

3. **Jupyter is installed:**
   ```bash
   uv sync  # or pip install jupyter
   ```

---

## Running Notebooks

### Using uv (Recommended)

```bash
# Start Jupyter from project root
uv run jupyter notebook notebooks/

# Or run a specific notebook
uv run jupyter notebook notebooks/01_cohort_retention_analysis.ipynb
```

### Using pip

```bash
# Activate virtual environment first
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Start Jupyter
jupyter notebook notebooks/

# Or run a specific notebook
jupyter notebook notebooks/01_cohort_retention_analysis.ipynb
```

### Using JupyterLab

```bash
# Using uv
uv run jupyter lab

# Using pip
jupyter lab
```

---

## Notebook Configuration

Both notebooks use this configuration at the top:

```python
# Imports
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Database path (relative to notebook location)
project_root = Path().resolve().parent
DB_PATH = project_root / "analytics.duckdb"
```

**Note:** Notebooks expect to be run from the `notebooks/` directory. The database path resolves to the project root.

---

## Customization

### Adding New Notebooks

1. Create notebook in `notebooks/` directory
2. Use the same import/config pattern
3. Connect to DuckDB: `conn = duckdb.connect(str(DB_PATH))`
4. Update this README with notebook description

### Modifying Analysis

- **Cohort granularity:** Change `DATE_TRUNC('week', ...)` to `'month'` for monthly cohorts
- **A/B test metric:** Change from `has_purchase` to `has_checkout` for different metric
- **Bootstrap samples:** Increase from 10,000 for more precision

---

## Troubleshooting

### Table does not exist

**Cause:** Analytics tables not created

**Fix:** Run the materialization script:
```bash
uv run python scripts/materialize_tables.py
```

### Database connection error

**Cause:** Incorrect database path

**Fix:** Verify you're running from `notebooks/` directory, or update `DB_PATH`:
```python
DB_PATH = Path("../analytics.duckdb")  # Relative to notebooks/
# or
DB_PATH = Path("W:/CodeBase/.../analytics.duckdb")  # Absolute path
```

### Kernel not found

**Cause:** Jupyter not using project environment

**Fix:** Use `uv run jupyter notebook` or install ipykernel:
```bash
uv run python -m ipykernel install --user --name ecommerce-analytics
```

---

## Output Examples

### Retention Heatmap
Shows retention rate (color) by cohort week (rows) and weeks since signup (columns).

### Bootstrap Distribution
Shows distribution of uplift (variant - control) from 10,000 bootstrap samples with 95% CI bounds.

### A/B Test Summary
| Metric | Control | Variant |
|--------|---------|---------|
| Sample Size | 23,481 | 23,522 |
| Conversion | 85.28% | 91.64% |
| Difference | +6.36 pp |
| P-value | < 0.0001 |
| Recommendation | **SHIP** |

