# Power BI Directory

This directory is reserved for Power BI dashboard files (.pbix).

## Status

**🚧 In Progress** — Dashboard files will be added after design completion.

---

## Data Sources

Power BI should connect to pre-aggregated CSV files in `data/powerbi/`:

| File | Description | Use Case |
|------|-------------|----------|
| `funnel_metrics.csv` | Funnel conversion by source, device, date | Funnel visualization, conversion trends |
| `cohort_retention.csv` | Weekly retention rates by cohort | Retention heatmap, cohort comparison |
| `ab_test_summary.csv` | A/B test variant comparison | Experiment results dashboard |

---

## Generating Data

Before importing to Power BI, generate the CSV files:

### Using uv

```bash
# Run full pipeline
uv run python src/data_generator.py
uv run python src/load_to_db.py
uv run python scripts/materialize_tables.py

# Create views and export
uv run python -c "import duckdb; conn = duckdb.connect('analytics.duckdb'); conn.execute(open('sql/analytics/06_powerbi_views.sql').read()); conn.close()"
uv run python scripts/export_powerbi_data.py
```

### Using pip

```bash
# Activate environment
.venv\Scripts\activate  # Windows

# Run full pipeline
python src/data_generator.py
python src/load_to_db.py
python scripts/materialize_tables.py

# Create views and export
python -c "import duckdb; conn = duckdb.connect('analytics.duckdb'); conn.execute(open('sql/analytics/06_powerbi_views.sql').read()); conn.close()"
python scripts/export_powerbi_data.py
```

---

## Suggested Dashboards

### 1. Funnel Analysis Dashboard

**Visuals:**
- Funnel chart (Visit → View → Cart → Checkout → Purchase)
- Conversion rate trend line by date
- Breakdown by device (bar chart)
- Breakdown by source (bar chart)

**Filters:**
- Date range
- Device type
- Traffic source

### 2. Cohort Retention Dashboard

**Visuals:**
- Retention heatmap (matrix visual)
- Retention curves (line chart by cohort)
- Cohort size bar chart
- Average retention by week number

**Filters:**
- Cohort week range
- Maximum cohort index

### 3. A/B Test Results Dashboard

**Visuals:**
- Conversion rate comparison (clustered bar)
- Sample size comparison
- Uplift percentage
- Statistical significance indicator

**Metrics:**
- Control conversion rate
- Variant conversion rate
- Absolute difference
- Relative lift

---

## Data Model Tips

### Rate Columns

All rate columns are **0-1 ratios** (not percentages). In Power BI:
- Format as Percentage: Right-click column → Format → Percentage
- Power BI will display 0.85 as "85%"

### Date Handling

- `session_date` and `cohort_week` are DATE columns
- Create a date table for time intelligence
- Use relative date filters

### Relationships

For more complex models, consider:
```
Date Table ──< funnel_metrics (session_date)
Date Table ──< cohort_retention (cohort_week)
```

---

## File Naming Convention

When saving Power BI files:

```
bi/
├── ecommerce_funnel_dashboard.pbix
├── ecommerce_retention_dashboard.pbix
├── ecommerce_ab_test_dashboard.pbix
└── README.md
```

---

## Best Practices

1. **Use DirectQuery or Import** — CSV files are small, Import is fine
2. **Refresh data** — Re-run `export_powerbi_data.py` for updates
3. **Add slicers** — Date, device, source for interactivity
4. **Conditional formatting** — Highlight low/high conversion rates
5. **Mobile layout** — Design for mobile viewing

---

## Resources

- [Power BI Desktop Download](https://powerbi.microsoft.com/desktop/)
- [Power BI Documentation](https://docs.microsoft.com/power-bi/)
- [Funnel Chart Guide](https://docs.microsoft.com/power-bi/visuals/power-bi-visualization-funnel-charts)
- [Matrix Visual (Heatmap)](https://docs.microsoft.com/power-bi/visuals/desktop-matrix-visual)
