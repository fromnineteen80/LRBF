#!/usr/bin/env python3
"""
Database Migration Script
Adds missing columns to existing database if needed
Run this if you get database schema errors
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path='instance/lrbf.db'):
    """Add missing columns to morning_forecasts table."""
    
    print(f"Checking database: {db_path}")
    
    if not Path(db_path).exists():
        print("Database file not found. It will be created on first run.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get current schema
        cursor.execute("PRAGMA table_info(morning_forecasts)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"\nCurrent columns: {', '.join(columns)}")
        
        # Check for missing columns
        migrations_needed = []
        
        if 'backup_stocks_json' not in columns:
            migrations_needed.append(('backup_stocks_json', 'TEXT'))
        
        if 'stock_analysis_json' not in columns:
            migrations_needed.append(('stock_analysis_json', 'TEXT'))
        
        if not migrations_needed:
            print("\nDatabase schema is up to date!")
            return True
        
        # Apply migrations
        print(f"\nFound {len(migrations_needed)} missing column(s)")
        
        for column_name, column_type in migrations_needed:
            print(f"   Adding: {column_name} {column_type}")
            cursor.execute(f"""
                ALTER TABLE morning_forecasts 
                ADD COLUMN {column_name} {column_type}
            """)
        
        conn.commit()
        print("\nMigration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\nMigration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'instance/lrbf.db'
    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
