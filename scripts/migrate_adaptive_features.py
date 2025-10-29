#!/usr/bin/env python3
"""
Database Migration: Add Adaptive Features Support

Adds columns to support:
1. Time-of-day pattern classification (morning_forecasts.time_profiles_json)
2. News event screening (morning_forecasts.news_screening_json)
3. News intervention tracking (daily_summaries.news_interventions_json)

Run this script ONCE before using time/news features.
Safe to run multiple times (checks if columns exist first).
"""

import sqlite3
import os
import sys


def migrate_database():
    """Add columns for time-of-day and news screening features"""
    
    # Database path
    db_path = os.path.join('data', 'luggage_room.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        print("Run from project root directory")
        return False
    
    print("=" * 60)
    print("DATABASE MIGRATION: Adaptive Features")
    print("=" * 60)
    print()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Add time_profiles_json to morning_forecasts
        print("Adding time_profiles_json to morning_forecasts...")
        try:
            cursor.execute("""
                ALTER TABLE morning_forecasts 
                ADD COLUMN time_profiles_json TEXT
            """)
            print("  ✓ Column added")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("  ↷ Column already exists")
            else:
                raise
        
        # 2. Add news_screening_json to morning_forecasts
        print("Adding news_screening_json to morning_forecasts...")
        try:
            cursor.execute("""
                ALTER TABLE morning_forecasts 
                ADD COLUMN news_screening_json TEXT
            """)
            print("  ✓ Column added")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("  ↷ Column already exists")
            else:
                raise
        
        # 3. Add news_interventions_json to daily_summaries
        print("Adding news_interventions_json to daily_summaries...")
        try:
            cursor.execute("""
                ALTER TABLE daily_summaries 
                ADD COLUMN news_interventions_json TEXT
            """)
            print("  ✓ Column added")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("  ↷ Column already exists")
            else:
                raise
        
        conn.commit()
        print()
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\nError during migration: {e}")
        return False
        
    finally:
        conn.close()


def verify_migration():
    """Verify all columns were added correctly"""
    
    db_path = os.path.join('data', 'luggage_room.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print()
        print("=" * 60)
        print("VERIFICATION")
        print("=" * 60)
        print()
        
        # Check morning_forecasts columns
        cursor.execute("PRAGMA table_info(morning_forecasts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        has_time_profiles = 'time_profiles_json' in columns
        has_news_screening = 'news_screening_json' in columns
        
        print("morning_forecasts table:")
        print(f"  time_profiles_json:   {'✓' if has_time_profiles else '✗'}")
        print(f"  news_screening_json:  {'✓' if has_news_screening else '✗'}")
        
        # Check daily_summaries columns
        cursor.execute("PRAGMA table_info(daily_summaries)")
        columns = [col[1] for col in cursor.fetchall()]
        
        has_interventions = 'news_interventions_json' in columns
        
        print()
        print("daily_summaries table:")
        print(f"  news_interventions_json: {'✓' if has_interventions else '✗'}")
        
        print()
        
        if has_time_profiles and has_news_screening and has_interventions:
            print("Status: ALL COLUMNS PRESENT ✓")
        else:
            print("Status: SOME COLUMNS MISSING ✗")
            return False
        
        return True
        
    finally:
        conn.close()


if __name__ == '__main__':
    try:
        migrate_database()
        
        if verify_migration():
            print()
            print("=" * 60)
            print("SUCCESS - Database is ready for adaptive features!")
            print("=" * 60)
        else:
            print()
            print("=" * 60)
            print("WARNING - Some columns may be missing")
            print("=" * 60)
    
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
