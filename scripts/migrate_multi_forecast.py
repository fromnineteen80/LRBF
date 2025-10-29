"""
Database Migration: Add Multi-Forecast Support

Adds columns to morning_forecasts table to store all 7 forecast scenarios:
- all_forecasts_json: Complete forecast data for all scenarios
- active_strategy: Currently selected strategy (default/preset name)
- active_preset: Currently selected preset configuration

This enables morning report to generate all 7 forecasts once, then user
can switch between them without re-running the scan.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sqlite3
import json
from datetime import datetime


def migrate_forecasts_table(db_path: str = "data/luggage_room.db"):
    """
    Add multi-forecast support to morning_forecasts table.
    
    Args:
        db_path: Path to SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Starting morning_forecasts migration...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(morning_forecasts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'all_forecasts_json' not in columns:
            migrations_needed.append(
                "ALTER TABLE morning_forecasts ADD COLUMN all_forecasts_json TEXT"
            )
        
        if 'active_strategy' not in columns:
            migrations_needed.append(
                "ALTER TABLE morning_forecasts ADD COLUMN active_strategy TEXT DEFAULT 'default'"
            )
        
        if 'active_preset' not in columns:
            migrations_needed.append(
                "ALTER TABLE morning_forecasts ADD COLUMN active_preset TEXT"
            )
        
        if not migrations_needed:
            print("✅ morning_forecasts table already up to date.")
            conn.close()
            return True
        
        # Execute migrations
        for migration_sql in migrations_needed:
            print(f"   Executing: {migration_sql}")
            cursor.execute(migration_sql)
        
        conn.commit()
        
        print(f"✅ Successfully added {len(migrations_needed)} columns to morning_forecasts")
        print("   - all_forecasts_json (TEXT) - Stores all 7 forecast scenarios")
        print("   - active_strategy (TEXT) - Currently selected strategy")
        print("   - active_preset (TEXT) - Currently selected preset config")
        
        # Verify migration
        cursor.execute("PRAGMA table_info(morning_forecasts)")
        new_columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n📊 morning_forecasts table now has {len(new_columns)} columns:")
        for col in new_columns:
            print(f"   - {col}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def store_all_forecasts(
    date: str,
    forecasts: dict,
    selected_stocks: list,
    backup_stocks: list = None,
    db_path: str = "data/luggage_room.db"
):
    """
    Store all 7 forecast scenarios for a given date.
    
    Args:
        date: Date string (YYYY-MM-DD)
        forecasts: Dictionary with all forecast scenarios:
            {
                'default': {...},
                'conservative': {...},
                'aggressive': {...},
                'choppy_market': {...},
                'trending_market': {...},
                'ab_test': {...},
                'vwap_breakout': {...}
            }
        selected_stocks: List of selected ticker symbols
        backup_stocks: List of backup ticker symbols
        db_path: Database path
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Use default forecast for backward compatibility fields
        default_forecast = forecasts.get('default', {})
        
        cursor.execute(
            """
            INSERT OR REPLACE INTO morning_forecasts (
                date,
                generated_at,
                selected_stocks_json,
                backup_stocks_json,
                all_forecasts_json,
                active_strategy,
                expected_trades_low,
                expected_trades_high,
                expected_pl_low,
                expected_pl_high
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date,
                datetime.now(),
                json.dumps(selected_stocks),
                json.dumps(backup_stocks or []),
                json.dumps(forecasts),
                'default',  # Start with default strategy
                default_forecast.get('expected_daily_trades_low', 0),
                default_forecast.get('expected_daily_trades_high', 0),
                default_forecast.get('expected_pl_low', 0.0),
                default_forecast.get('expected_pl_high', 0.0)
            )
        )
        
        conn.commit()
        conn.close()
        
        print(f"✅ Stored all {len(forecasts)} forecasts for {date}")
        return True
        
    except Exception as e:
        print(f"❌ Error storing forecasts: {e}")
        return False


def get_all_forecasts(date: str, db_path: str = "data/luggage_room.db") -> dict:
    """
    Retrieve all forecast scenarios for a date.
    
    Returns:
        Dictionary with all 7 forecast scenarios
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT all_forecasts_json FROM morning_forecasts WHERE date = ?",
            (date,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return json.loads(result[0])
        return {}
        
    except Exception as e:
        print(f"❌ Error retrieving forecasts: {e}")
        return {}


def set_active_strategy(
    date: str,
    strategy: str,
    preset: str = None,
    db_path: str = "data/luggage_room.db"
):
    """
    Set the active strategy/preset for a given date.
    
    Args:
        date: Date string (YYYY-MM-DD)
        strategy: Strategy name ('default', 'conservative', etc.)
        preset: Preset configuration name (optional)
        db_path: Database path
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            UPDATE morning_forecasts
            SET active_strategy = ?, active_preset = ?
            WHERE date = ?
            """,
            (strategy, preset, date)
        )
        
        if cursor.rowcount == 0:
            print(f"❌ No forecast found for {date}")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        
        print(f"✅ Set active strategy to '{strategy}' for {date}")
        return True
        
    except Exception as e:
        print(f"❌ Error setting active strategy: {e}")
        return False


def get_active_forecast(date: str, db_path: str = "data/luggage_room.db") -> dict:
    """
    Get the currently active forecast for a date.
    
    Returns:
        Dictionary with active forecast data
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT all_forecasts_json, active_strategy
            FROM morning_forecasts
            WHERE date = ?
            """,
            (date,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            all_forecasts = json.loads(result[0])
            active_strategy = result[1] or 'default'
            
            return {
                'strategy': active_strategy,
                'forecast': all_forecasts.get(active_strategy, {})
            }
        
        return {}
        
    except Exception as e:
        print(f"❌ Error retrieving active forecast: {e}")
        return {}


# ========================================================================
# CLI INTERFACE
# ========================================================================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("LRBF DATABASE MIGRATION - Multi-Forecast Support")
    print("=" * 60)
    print()
    
    # Run migration
    success = migrate_forecasts_table()
    
    if success:
        print("\n✅ Migration complete!")
        print("\nNext steps:")
        print("1. Morning report will now generate all 7 forecasts")
        print("2. Use set_active_strategy() to switch between them")
        print("3. Live monitor will track against active forecast")
    
    print("\n" + "=" * 60)
