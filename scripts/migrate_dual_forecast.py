"""
Database Migration: Add Dual-Forecast Columns to morning_forecasts

Adds support for tracking both default and enhanced strategy forecasts.
"""

import sqlite3
from datetime import datetime

def migrate_database(db_path='data/luggage_room.db'):
    """
    Add dual-forecast columns to morning_forecasts table.
    
    New columns:
    - default_forecast_json: JSON for default strategy forecast
    - enhanced_forecast_json: JSON for enhanced strategy forecast
    - active_preset: Which strategy preset is active ('default', 'enhanced', etc.)
    """
    print("=" * 60)
    print("DATABASE MIGRATION: Dual-Forecast Support")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(morning_forecasts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'default_forecast_json' not in columns:
            migrations_needed.append('default_forecast_json')
        
        if 'enhanced_forecast_json' not in columns:
            migrations_needed.append('enhanced_forecast_json')
        
        if 'active_preset' not in columns:
            migrations_needed.append('active_preset')
        
        if not migrations_needed:
            print("✅ All columns already exist. No migration needed.")
            conn.close()
            return True
        
        print(f"Adding {len(migrations_needed)} new columns:")
        for col in migrations_needed:
            print(f"  - {col}")
        print()
        
        # Add columns
        if 'default_forecast_json' in migrations_needed:
            cursor.execute("""
                ALTER TABLE morning_forecasts 
                ADD COLUMN default_forecast_json TEXT
            """)
            print("✅ Added default_forecast_json column")
        
        if 'enhanced_forecast_json' in migrations_needed:
            cursor.execute("""
                ALTER TABLE morning_forecasts 
                ADD COLUMN enhanced_forecast_json TEXT
            """)
            print("✅ Added enhanced_forecast_json column")
        
        if 'active_preset' in migrations_needed:
            cursor.execute("""
                ALTER TABLE morning_forecasts 
                ADD COLUMN active_preset TEXT DEFAULT 'default'
            """)
            print("✅ Added active_preset column")
        
        # Commit changes
        conn.commit()
        print()
        print("✅ Migration completed successfully!")
        
        # Verify
        cursor.execute("PRAGMA table_info(morning_forecasts)")
        all_columns = [col[1] for col in cursor.fetchall()]
        print()
        print(f"Current columns in morning_forecasts ({len(all_columns)}):")
        for col in all_columns:
            print(f"  - {col}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = migrate_database()
    print()
    print("=" * 60)
    if success:
        print("MIGRATION COMPLETE")
    else:
        print("MIGRATION FAILED")
    print("=" * 60)
