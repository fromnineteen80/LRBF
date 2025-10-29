"""
Database Migration: Add cross_strategy_outliers_json column

Run this script to add the new column to existing database.
"""

import sqlite3
import os

def migrate_database(db_path='data/luggage_room.db'):
    """
    Add cross_strategy_outliers_json column to morning_forecasts table.
    """
    print("=" * 60)
    print("DATABASE MIGRATION: Cross-Strategy Outliers")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(morning_forecasts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'cross_strategy_outliers_json' in columns:
            print("✅ Column 'cross_strategy_outliers_json' already exists")
            return True
        
        # Add column
        print("Adding column 'cross_strategy_outliers_json'...")
        cursor.execute("""
            ALTER TABLE morning_forecasts 
            ADD COLUMN cross_strategy_outliers_json TEXT
        """)
        
        conn.commit()
        print("✅ Column added successfully")
        
        # Verify
        cursor.execute("PRAGMA table_info(morning_forecasts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'cross_strategy_outliers_json' in columns:
            print("✅ Migration verified")
            return True
        else:
            print("❌ Migration failed - column not found after addition")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n✅ Migration complete!")
    else:
        print("\n❌ Migration failed!")
