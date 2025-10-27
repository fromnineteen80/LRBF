#!/usr/bin/env python3
"""
Database Migration: Add Seven-Forecast Support

Adds columns to morning_forecasts table:
1. default_forecast_json (3-Step Default)
2. conservative_forecast_json (3-Step Conservative)
3. aggressive_forecast_json (3-Step Aggressive)
4. choppy_forecast_json (3-Step Choppy Market)
5. trending_forecast_json (3-Step Trending)
6. abtest_forecast_json (3-Step AB Test)
7. vwap_breakout_forecast_json (VWAP Breakout strategy)
8. active_preset (user's selection: 'default', 'conservative', etc.)
9. active_strategy ('3step' or 'vwap_breakout')
"""

import sqlite3
import os

def migrate_database():
    db_path = os.path.join('data', 'luggage_room.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    print("=" * 60)
    print("DATABASE MIGRATION: Seven-Forecast Support")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add forecast columns (one per preset/strategy)
        columns = [
            'default_forecast_json',
            'conservative_forecast_json',
            'aggressive_forecast_json',
            'choppy_forecast_json',
            'trending_forecast_json',
            'abtest_forecast_json',
            'vwap_breakout_forecast_json',
            'active_preset',
            'active_strategy'
        ]
        
        for col in columns:
            print(f"Adding {col}...")
            try:
                cursor.execute(f"ALTER TABLE morning_forecasts ADD COLUMN {col} TEXT")
                print(f"  ✓ Added")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print(f"  ↷ Already exists")
                else:
                    raise
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify columns were added
        cursor.execute("PRAGMA table_info(morning_forecasts)")
        all_columns = [col[1] for col in cursor.fetchall()]
        print(f"\nmorning_forecasts table now has {len(all_columns)} columns:")
        for col in all_columns:
            print(f"  - {col}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = migrate_database()
    exit(0 if success else 1)
