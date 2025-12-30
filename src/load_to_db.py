"""
Load Raw CSV Data into DuckDB

Loads users, events, and orders CSV files into DuckDB tables with proper
schema definitions and indexes for analytics queries.

Usage:
    python src/load_to_db.py
"""

import os
import duckdb
import pandas as pd
from pathlib import Path


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = PROJECT_ROOT / "analytics.duckdb"

# CSV file paths
USERS_CSV = DATA_DIR / "users.csv"
EVENTS_CSV = DATA_DIR / "events.csv"
ORDERS_CSV = DATA_DIR / "orders.csv"


def connect_db(db_path: Path) -> duckdb.DuckDBPyConnection:
    """
    Create or connect to DuckDB database.
    
    Args:
        db_path: Path to database file
        
    Returns:
        DuckDB connection object
    """
    return duckdb.connect(str(db_path))


def load_users_table(conn: duckdb.DuckDBPyConnection, csv_path: Path):
    """
    Load users CSV into users_raw table with proper schema.
    
    Args:
        conn: DuckDB connection
        csv_path: Path to users.csv
    """
    print("Loading users table...")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Create table with explicit schema
    conn.execute("""
        CREATE OR REPLACE TABLE users_raw AS
        SELECT
            CAST(user_id AS INTEGER) AS user_id,
            CAST(signup_date AS DATE) AS signup_date,
            CAST(device AS VARCHAR) AS device,
            CAST(country AS VARCHAR) AS country,
            CAST(loyalty_tier AS VARCHAR) AS loyalty_tier
        FROM df
    """)
    
    # Create index
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users_raw(user_id)")
    
    print(f"  Loaded {len(df):,} users")


def load_events_table(conn: duckdb.DuckDBPyConnection, csv_path: Path):
    """
    Load events CSV into events_raw table with proper schema.
    
    Args:
        conn: DuckDB connection
        csv_path: Path to events.csv
    """
    print("Loading events table...")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Handle nullable columns (convert empty strings to None)
    df['session_id'] = df['session_id'].replace('', None)
    df['product_id'] = df['product_id'].replace('', None)
    df['ab_test_id'] = df['ab_test_id'].replace('', None)
    df['variant'] = df['variant'].replace('', None)
    
    # Create table with explicit schema
    conn.execute("""
        CREATE OR REPLACE TABLE events_raw AS
        SELECT
            CAST(event_id AS VARCHAR) AS event_id,
            CAST(user_id AS INTEGER) AS user_id,
            CAST(session_id AS VARCHAR) AS session_id,
            CAST(event_type AS VARCHAR) AS event_type,
            CAST(page AS VARCHAR) AS page,
            CAST(product_id AS INTEGER) AS product_id,
            CAST(product_category AS VARCHAR) AS product_category,
            CAST(ts AS TIMESTAMP) AS ts,
            CAST(source AS VARCHAR) AS source,
            CAST(device AS VARCHAR) AS device,
            CAST(ab_test_id AS VARCHAR) AS ab_test_id,
            CAST(variant AS VARCHAR) AS variant
        FROM df
    """)
    
    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_user_id ON events_raw(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events_raw(ts)")
    
    print(f"  Loaded {len(df):,} events")


def load_orders_table(conn: duckdb.DuckDBPyConnection, csv_path: Path):
    """
    Load orders CSV into orders_raw table with proper schema.
    Adds product_category by joining with events_raw.
    
    Args:
        conn: DuckDB connection
        csv_path: Path to orders.csv
    """
    print("Loading orders table...")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Create temporary table first
    conn.execute("""
        CREATE OR REPLACE TABLE orders_temp AS
        SELECT
            CAST(order_id AS VARCHAR) AS order_id,
            CAST(user_id AS INTEGER) AS user_id,
            CAST(product_id AS INTEGER) AS product_id,
            CAST(price AS DOUBLE) AS price,
            CAST(quantity AS INTEGER) AS quantity,
            CAST(discount_amount AS DOUBLE) AS discount_amount,
            CAST(ts AS TIMESTAMP) AS ts,
            CAST(payment_status AS VARCHAR) AS payment_status
        FROM df
    """)
    
    # Create final table with product_category from events
    conn.execute("""
        CREATE OR REPLACE TABLE orders_raw AS
        SELECT
            o.order_id,
            o.user_id,
            o.product_id,
            COALESCE(e.product_category, 'unknown') AS product_category,
            o.price,
            o.quantity,
            o.discount_amount,
            o.ts,
            o.payment_status
        FROM orders_temp o
        LEFT JOIN (
            SELECT DISTINCT product_id, product_category
            FROM events_raw
            WHERE product_id IS NOT NULL
            AND product_category IS NOT NULL
        ) e ON o.product_id = e.product_id
    """)
    
    # Drop temporary table
    conn.execute("DROP TABLE IF EXISTS orders_temp")
    
    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders_raw(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_ts ON orders_raw(ts)")
    
    print(f"  Loaded {len(df):,} orders")


def validate_data(conn: duckdb.DuckDBPyConnection):
    """
    Print validation statistics after loading data.
    
    Args:
        conn: DuckDB connection
    """
    print("\n" + "="*60)
    print("VALIDATION STATISTICS")
    print("="*60)
    
    # Row counts
    print("\nRow Counts:")
    users_count = conn.execute("SELECT COUNT(*) FROM users_raw").fetchone()[0]
    events_count = conn.execute("SELECT COUNT(*) FROM events_raw").fetchone()[0]
    orders_count = conn.execute("SELECT COUNT(*) FROM orders_raw").fetchone()[0]
    
    print(f"  users_raw:  {users_count:,}")
    print(f"  events_raw: {events_count:,}")
    print(f"  orders_raw: {orders_count:,}")
    
    # Event type distribution
    print("\nEvent Type Distribution:")
    event_types = conn.execute("""
        SELECT event_type, COUNT(*) as cnt
        FROM events_raw
        GROUP BY event_type
        ORDER BY cnt DESC
    """).fetchall()
    
    for event_type, count in event_types:
        pct = (count / events_count * 100) if events_count > 0 else 0
        print(f"  {event_type:15s}: {count:8,} ({pct:5.2f}%)")
    
    # A/B test checkout events
    print("\nA/B Test Coverage:")
    checkout_with_ab = conn.execute("""
        SELECT COUNT(*) 
        FROM events_raw 
        WHERE event_type = 'checkout' 
        AND ab_test_id IS NOT NULL
    """).fetchone()[0]
    
    total_checkouts = conn.execute("""
        SELECT COUNT(*) 
        FROM events_raw 
        WHERE event_type = 'checkout'
    """).fetchone()[0]
    
    print(f"  Checkout events with ab_test_id: {checkout_with_ab:,} / {total_checkouts:,}")
    if total_checkouts > 0:
        print(f"  Coverage: {checkout_with_ab/total_checkouts*100:.2f}%")
    
    # Control vs Variant purchases
    print("\nA/B Test Purchase Comparison:")
    ab_purchases = conn.execute("""
        SELECT 
            variant,
            COUNT(*) as purchase_count
        FROM events_raw
        WHERE event_type = 'purchase'
        AND variant IS NOT NULL
        GROUP BY variant
        ORDER BY variant
    """).fetchall()
    
    if ab_purchases:
        for variant, count in ab_purchases:
            print(f"  {variant:10s}: {count:8,} purchases")
        
        # Calculate conversion rates if we have checkout data
        conversion_data = conn.execute("""
            SELECT 
                e.variant,
                COUNT(DISTINCT CASE WHEN e.event_type = 'checkout' THEN e.session_id END) as checkouts,
                COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.session_id END) as purchases
            FROM events_raw e
            WHERE e.variant IS NOT NULL
            AND e.event_type IN ('checkout', 'purchase')
            GROUP BY e.variant
        """).fetchall()
        
        if conversion_data:
            print("\n  Conversion Rates (Checkout -> Purchase):")
            for variant, checkouts, purchases in conversion_data:
                conv_rate = (purchases / checkouts * 100) if checkouts > 0 else 0
                print(f"    {variant:10s}: {purchases:,} / {checkouts:,} = {conv_rate:.2f}%")
    else:
        print("  No A/B test purchases found")
    
    print("\n" + "="*60)


def main():
    """Main execution function."""
    print("="*60)
    print("LOADING DATA INTO DUCKDB")
    print("="*60)
    print(f"Database: {DB_PATH}")
    print(f"Data directory: {DATA_DIR}")
    print("="*60)
    
    # Verify CSV files exist
    if not USERS_CSV.exists():
        raise FileNotFoundError(f"Users CSV not found: {USERS_CSV}")
    if not EVENTS_CSV.exists():
        raise FileNotFoundError(f"Events CSV not found: {EVENTS_CSV}")
    if not ORDERS_CSV.exists():
        raise FileNotFoundError(f"Orders CSV not found: {ORDERS_CSV}")
    
    # Connect to database
    conn = connect_db(DB_PATH)
    
    try:
        # Load tables
        load_users_table(conn, USERS_CSV)
        load_events_table(conn, EVENTS_CSV)
        load_orders_table(conn, ORDERS_CSV)
        
        # Validate
        validate_data(conn)
        
        print("\n[SUCCESS] Data loading complete!")
        print(f"Database saved to: {DB_PATH}")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()

