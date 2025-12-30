# SQL Scripts

This directory contains SQL scripts organized into raw data processing and analytics.

## Structure

- **raw/** - Raw data processing scripts (data cleaning, sessionization)
- **analytics/** - Analytics queries (funnel, cohort, A/B testing)

## Scripts

### Raw Processing (`sql/raw/`)
1. **01_sessionization.sql** - Create user sessions from raw events (30-min timeout)
2. **02_data_cleaning.sql** - Handle missing events, duplicates, bot traffic

### Analytics (`sql/analytics/`)
1. **01_funnel_analysis.sql** - Build funnel stages and calculate conversion rates
2. **02_cohort_retention.sql** - Calculate cohort assignments and retention metrics
3. **03_ab_test_analysis.sql** - A/B test comparison queries

## Usage

Load raw data into database first, then run scripts in order:
1. Raw processing scripts first
2. Analytics scripts second
