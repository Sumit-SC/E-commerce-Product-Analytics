# Power BI Dashboard

This directory contains the Power BI dashboard file and documentation.

## Dashboard Components

1. **Funnel Visualization** - Multi-stage conversion funnel with drill-downs
2. **Retention Heatmap** - Cohort × Period retention matrix
3. **Conversion Analysis** - Conversion rates by channel, device, time
4. **A/B Test Results** - Variant vs control comparisons with significance

## Data Model

Star schema with fact tables (events, orders) and dimension tables (users, products, dates).

## Usage

1. Load processed data from `data/processed/` into Power BI
2. Build relationships between tables
3. Create visualizations as per plan

