"""
Cohort Retention Analysis

Loads cohort retention data from DuckDB and prepares it for analysis.
Creates a retention matrix (cohort_week x cohort_index) for visualization.

Usage:
    python src/cohort_analysis.py
"""

import os
import duckdb
import pandas as pd
from pathlib import Path


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "analytics.duckdb"

# SQL query file path
RETENTION_QUERY_FILE = PROJECT_ROOT / "sql" / "analytics" / "05_cohort_retention_rates.sql"


def load_retention_query() -> str:
    """
    Load the cohort retention rates SQL query from file.
    
    Returns:
        SQL query string
    """
    if not RETENTION_QUERY_FILE.exists():
        raise FileNotFoundError(f"Retention query file not found: {RETENTION_QUERY_FILE}")
    
    with open(RETENTION_QUERY_FILE, 'r') as f:
        query = f.read()
    
    # DuckDB handles SQL comments, but we'll extract just the SELECT statement
    # Find the main SELECT query (after all CTEs and comments)
    # For simplicity, we'll use the query as-is since DuckDB handles comments
    
    return query


def load_retention_data(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Execute the cohort retention rates query and load into DataFrame.
    
    Args:
        conn: DuckDB connection
        
    Returns:
        DataFrame with columns: cohort_week, cohort_index, users_active, 
        cohort_size, retention_rate
    """
    print("Loading cohort retention data from DuckDB...")
    
    # Load and execute the query
    query = load_retention_query()
    df = conn.execute(query).df()
    
    # Convert cohort_week to datetime if it's not already
    if 'cohort_week' in df.columns:
        df['cohort_week'] = pd.to_datetime(df['cohort_week'])
    
    print(f"  Loaded {len(df):,} retention records")
    
    return df


def create_retention_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot retention data into a matrix format.
    
    Args:
        df: DataFrame with cohort_week, cohort_index, retention_rate
        
    Returns:
        Pivoted DataFrame with:
        - index = cohort_week (rows)
        - columns = cohort_index (weeks since signup)
        - values = retention_rate
    """
    print("\nCreating retention matrix...")
    
    # Pivot the data: cohort_week x cohort_index
    retention_matrix = df.pivot_table(
        index='cohort_week',
        columns='cohort_index',
        values='retention_rate',
        fill_value=None  # Keep NaN for missing periods
    )
    
    # Sort cohorts chronologically
    retention_matrix = retention_matrix.sort_index()
    
    # Sort columns (cohort_index) numerically
    retention_matrix = retention_matrix.sort_index(axis=1)
    
    print(f"  Matrix shape: {retention_matrix.shape[0]} cohorts × {retention_matrix.shape[1]} periods")
    
    return retention_matrix


def main():
    """Main execution function."""
    print("="*60)
    print("COHORT RETENTION ANALYSIS")
    print("="*60)
    print(f"Database: {DB_PATH}")
    print("="*60)
    
    # Verify database exists
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    
    # Connect to DuckDB
    conn = duckdb.connect(str(DB_PATH))
    
    try:
        # Load retention data
        retention_df = load_retention_data(conn)
        
        # Display head of raw data
        print("\n" + "="*60)
        print("RAW RETENTION DATA (First 10 rows)")
        print("="*60)
        print(retention_df.head(10).to_string())
        
        # Create retention matrix
        retention_matrix = create_retention_matrix(retention_df)
        
        # Display matrix info
        print("\n" + "="*60)
        print("RETENTION MATRIX INFO")
        print("="*60)
        print(f"Shape: {retention_matrix.shape[0]} cohorts × {retention_matrix.shape[1]} periods")
        print(f"\nFirst 5 cohorts (first 10 periods):")
        print(retention_matrix.iloc[:5, :10].to_string())
        
        print("\n" + "="*60)
        print("Data preparation complete!")
        print("="*60)
        print("\nNext steps:")
        print("  - Retention matrix ready for visualization")
        print("  - Use retention_matrix for heatmaps and retention curves")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()

