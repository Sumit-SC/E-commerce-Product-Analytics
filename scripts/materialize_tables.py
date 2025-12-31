"""
Materialize Analytics Tables in DuckDB

This script executes SQL files to create analytics tables:
1. user_sessions - Sessionized events from raw clickstream
2. funnel_sessions - Session-level funnel flags
3. purchase_cohorts - Cohort base table for retention analysis
"""

import duckdb
from pathlib import Path


def load_sql_file(file_path: Path) -> str:
    """Load SQL file content and fix DuckDB syntax for WITH + CREATE statements."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the validation queries section
    validation_marker = '-- ============================================================================\n-- Validation'
    if validation_marker in content:
        sql_content = content.split(validation_marker)[0]
    else:
        # If no validation section, find the last semicolon
        last_semicolon = content.rfind(';')
        if last_semicolon != -1:
            sql_content = content[:last_semicolon + 1]
        else:
            sql_content = content
    
    sql_content = sql_content.strip()
    
    # Fix DuckDB syntax: WITH clause must be inside CREATE, not before it
    # Pattern: WITH ... ) CREATE OR REPLACE TABLE ... AS\nSELECT ...
    # Should be: CREATE OR REPLACE TABLE ... AS (WITH ... SELECT ...)
    
    if 'WITH ' in sql_content.upper() and 'CREATE OR REPLACE TABLE' in sql_content.upper():
        lines = sql_content.split('\n')
        
        # Find line with WITH (not in comment)
        with_line_idx = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.upper().startswith('WITH ') and not stripped.startswith('--'):
                with_line_idx = i
                break
        
        # Find line with CREATE
        create_line_idx = -1
        for i, line in enumerate(lines):
            if 'CREATE OR REPLACE TABLE' in line.upper() and not line.strip().startswith('--'):
                create_line_idx = i
                break
        
        if with_line_idx != -1 and create_line_idx != -1 and with_line_idx < create_line_idx:
            # Extract WITH clause (from WITH line to line before CREATE)
            with_lines = lines[with_line_idx:create_line_idx]
            # Remove trailing blank lines and comments
            while with_lines and (not with_lines[-1].strip() or with_lines[-1].strip().startswith('--')):
                with_lines.pop()
            with_clause = '\n'.join(with_lines).strip()
            
            # Extract CREATE statement
            create_lines = lines[create_line_idx:]
            create_part = '\n'.join(create_lines).strip()
            
            # Find "AS" in CREATE (should be on same line or next line after table name)
            as_pos = create_part.upper().find(' AS\n')
            if as_pos == -1:
                as_pos = create_part.upper().find(' AS ')
            
            if as_pos != -1:
                create_header = create_part[:as_pos + 3].strip()
                select_part = create_part[as_pos + 3:].strip()
                
                # Remove trailing semicolon
                if select_part.rstrip().endswith(';'):
                    select_part = select_part.rstrip()[:-1].strip()
                
                # Reconstruct
                sql_content = f"{create_header} (\n{with_clause}\n{select_part}\n)"
    
    return sql_content


def main():
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    db_path = project_root / "analytics.duckdb"
    sql_dir = project_root / "sql" / "analytics"
    
    print("=" * 60)
    print("MATERIALIZING ANALYTICS TABLES")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"SQL Directory: {sql_dir}")
    print()
    
    # Connect to DuckDB
    conn = duckdb.connect(str(db_path))
    
    # Table 1: user_sessions
    print("Creating user_sessions table...")
    print("  Source: sql/analytics/01_sessionization.sql")
    sql_file = sql_dir / "01_sessionization.sql"
    sql = load_sql_file(sql_file)
    conn.execute(sql)
    
    row_count = conn.execute("SELECT COUNT(*) FROM user_sessions").fetchone()[0]
    print(f"  [OK] Created user_sessions with {row_count:,} rows")
    print()
    
    # Table 2: funnel_sessions
    print("Creating funnel_sessions table...")
    print("  Source: sql/analytics/02_funnel.sql")
    sql_file = sql_dir / "02_funnel.sql"
    sql = load_sql_file(sql_file)
    conn.execute(sql)
    
    row_count = conn.execute("SELECT COUNT(*) FROM funnel_sessions").fetchone()[0]
    print(f"  [OK] Created funnel_sessions with {row_count:,} rows")
    print()
    
    # Table 3: purchase_cohorts
    print("Creating purchase_cohorts table...")
    print("  Source: sql/analytics/03_cohorts.sql")
    sql_file = sql_dir / "03_cohorts.sql"
    sql = load_sql_file(sql_file)
    conn.execute(sql)
    
    row_count = conn.execute("SELECT COUNT(*) FROM purchase_cohorts").fetchone()[0]
    print(f"  [OK] Created purchase_cohorts with {row_count:,} rows")
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("All analytics tables created successfully:")
    print("  - user_sessions")
    print("  - funnel_sessions")
    print("  - purchase_cohorts")
    print()
    
    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()

