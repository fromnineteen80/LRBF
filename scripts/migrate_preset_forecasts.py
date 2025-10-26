"""
Database Migration: Add Preset Forecasts Support
Stores all preset forecasts in single JSON column for easy toggling.
"""

import sqlite3
from datetime import datetime

def migrate_database(db_path='data/luggage_room.db'):
    """
    Add preset forecasts support to morning_forecasts table.
    
    New columns:
    - preset_forecasts_json: JSON containing all preset forecasts
    - active_preset: Currently active preset ('default', 'conservative', etc.)
    """
    print("=" * 60)
    print("DATABASE MIGRATION: Preset Forecasts Support")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(morning_forecasts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'preset_forecasts_json' not in columns:
            migrations_needed.append('preset_forecasts_json')
        
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
        if 'preset_forecasts_json' in migrations_needed:
            cursor.execute("""
                ALTER TABLE morning_forecasts 
                ADD COLUMN preset_forecasts_json TEXT
            """)
            print("✅ Added preset_forecasts_json column")
            print("   Structure: {")
            print('     "default": {...forecast...},')
            print('     "conservative": {...forecast...},')
            print('     "aggressive": {...forecast...},')
            print('     "choppy_market": {...forecast...},')
            print('     "trending_market": {...forecast...}')
            print("   }")
        
        if 'active_preset' in migrations_needed:
            cursor.execute("""
                ALTER TABLE morning_forecasts 
                ADD COLUMN active_preset TEXT DEFAULT 'default'
            """)
            print("✅ Added active_preset column")
            print("   Default: 'default'")
            print("   Options: 'default', 'conservative', 'aggressive',")
            print("            'choppy_market', 'trending_market'")
        
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
        print()
        print("Next steps:")
        print("1. Update morning_report.py to generate all preset forecasts")
        print("2. Update storage_manager.py to store preset_forecasts_json")
        print("3. Update API endpoint to support preset parameter")
    else:
        print("MIGRATION FAILED")
    print("=" * 60)
