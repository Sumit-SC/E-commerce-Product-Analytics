"""
Export Power BI Views to CSV

This script exports Power BI-ready views from DuckDB to CSV files
for use in Power BI dashboards.

Prerequisites:
    - Run materialize_tables.py first to create the base tables

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
SQL_DIR = PROJECT_ROOT / "sql" / "analytics"

# Views to export: (view_name, output_filename)
VIEWS_TO_EXPORT = [
    ("v_funnel_metrics", "funnel_metrics.csv"),
    ("v_cohort_retention", "cohort_retention.csv"),
    ("v_ab_test_summary", "ab_test_summary.csv"),
]


def create_views(conn):
    """Create Power BI views from SQL file."""
    sql_file = SQL_DIR / "08_powerbi_views.sql"
    
    print(f"Creating views from: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into individual statements (CREATE VIEW statements)
    # Remove comments and find CREATE statements
    statements = []
    current_stmt = []
    
    for line in content.split('\n'):
        stripped = line.strip()
        # Skip pure comment lines at statement start
        if not current_stmt and stripped.startswith('--'):
            continue
        
        current_stmt.append(line)
        
        # End of statement
        if stripped.endswith(';'):
            stmt = '\n'.join(current_stmt).strip()
            # Only keep CREATE VIEW statements
            if 'CREATE OR REPLACE VIEW' in stmt.upper():
                statements.append(stmt)
            current_stmt = []
    
    # Execute each CREATE VIEW statement
    for stmt in statements:
        # Extract view name for logging
        view_name = stmt.split('VIEW')[1].split('AS')[0].strip()
        conn.execute(stmt)
        print(f"  [OK] Created view: {view_name}")


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
    
    # Connect to DuckDB (read-write to create views)
    conn = duckdb.connect(str(DB_PATH))
    print(f"[OK] Connected to database")
    
    print("\n" + "-" * 60)
    print("Creating Power BI views...")
    print("-" * 60)
    
    # Create views
    create_views(conn)
    
    print("\n" + "-" * 60)
    print("Exporting views to CSV...")
    print("-" * 60)
    
    # Export each view
    for view_name, output_filename in VIEWS_TO_EXPORT:
        output_path = OUTPUT_DIR / output_filename
        
        # Query the view
        df = conn.execute(f"SELECT * FROM {view_name}").df()
        
        # Export to CSV
        df.to_csv(output_path, index=False)
        
        print(f"[OK] {view_name} -> {output_filename} ({len(df):,} rows)")
    
    # Validate cohort retention rates
    print("\n" + "-" * 60)
    print("Validating cohort retention data...")
    print("-" * 60)
    
    invalid_count = conn.execute("""
        SELECT COUNT(*) FROM v_cohort_retention WHERE retention_rate > 1.0
    """).fetchone()[0]
    
    if invalid_count > 0:
        print(f"  [WARNING] Found {invalid_count} rows with retention_rate > 100%!")
    else:
        print("  [OK] All retention rates are valid (0-100%)")
    
    # Show sample stats
    stats = conn.execute("""
        SELECT 
            MIN(retention_rate) AS min_rate,
            MAX(retention_rate) AS max_rate,
            AVG(retention_rate) AS avg_rate
        FROM v_cohort_retention
    """).fetchone()
    print(f"  Retention rate range: {stats[0]:.2%} to {stats[1]:.2%} (avg: {stats[2]:.2%})")
    
    # Close connection
    conn.close()
    
    print("\n" + "=" * 60)
    print("EXPORT COMPLETE")
    print("=" * 60)
    print(f"Files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
