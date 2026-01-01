"""
Export Power BI Views to CSV

This script exports Power BI-ready views from DuckDB to CSV files
for use in Power BI dashboards.

Usage:
    python scripts/export_powerbi_data.py
    # or with uv:
    uv run python scripts/export_powerbi_data.py
"""

import os
from pathlib import Path
import duckdb
import pandas as pd


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "analytics.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "data" / "powerbi"

# Views to export: (view_name, output_filename)
VIEWS_TO_EXPORT = [
    ("v_funnel_metrics", "funnel_metrics.csv"),
    ("v_cohort_retention", "cohort_retention.csv"),
    ("v_ab_test_summary", "ab_test_summary.csv"),
]


def main():
    """Export Power BI views to CSV files."""
    
    print("=" * 60)
    print("EXPORT POWER BI DATA")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Create output directory if it does not exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Output directory ready")
    
    # Connect to DuckDB
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    print(f"[OK] Connected to database")
    
    print("\n" + "-" * 60)
    print("Exporting views...")
    print("-" * 60)
    
    # Export each view
    for view_name, output_filename in VIEWS_TO_EXPORT:
        output_path = OUTPUT_DIR / output_filename
        
        # Query the view
        df = conn.execute(f"SELECT * FROM {view_name}").df()
        
        # Export to CSV
        df.to_csv(output_path, index=False)
        
        print(f"[OK] {view_name} -> {output_filename} ({len(df):,} rows)")
    
    # Close connection
    conn.close()
    
    print("\n" + "=" * 60)
    print("EXPORT COMPLETE")
    print("=" * 60)
    print(f"Files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

