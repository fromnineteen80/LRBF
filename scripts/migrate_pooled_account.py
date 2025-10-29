"""
Database Migration: Add Pooled Fund Account Fields

Adds columns to users table for multi-user pooled IBKR account tracking:
- fund_contribution: Amount each user contributed (USD)
- ownership_pct: Calculated ownership percentage of fund
- last_contribution_date: Date of most recent contribution

This enables P&L allocation by ownership while sharing one IBKR account.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sqlite3
from datetime import datetime


def migrate_users_table(db_path: str = "data/luggage_room.db"):
    """
    Add pooled fund fields to users table.
    
    Args:
        db_path: Path to SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Starting database migration...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        migrations_needed = []
        
        if 'fund_contribution' not in columns:
            migrations_needed.append("ALTER TABLE users ADD COLUMN fund_contribution REAL DEFAULT 0.0")
        
        if 'ownership_pct' not in columns:
            migrations_needed.append("ALTER TABLE users ADD COLUMN ownership_pct REAL DEFAULT 0.0")
        
        if 'last_contribution_date' not in columns:
            migrations_needed.append("ALTER TABLE users ADD COLUMN last_contribution_date TIMESTAMP")
        
        if not migrations_needed:
            print("✅ Database already up to date. No migration needed.")
            conn.close()
            return True
        
        # Execute migrations
        for migration_sql in migrations_needed:
            print(f"   Executing: {migration_sql}")
            cursor.execute(migration_sql)
        
        conn.commit()
        
        print(f"✅ Successfully added {len(migrations_needed)} columns to users table")
        print("   - fund_contribution (REAL)")
        print("   - ownership_pct (REAL)")
        print("   - last_contribution_date (TIMESTAMP)")
        
        # Verify migration
        cursor.execute("PRAGMA table_info(users)")
        new_columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n📊 Users table now has {len(new_columns)} columns:")
        for col in new_columns:
            print(f"   - {col}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def calculate_ownership_percentages(db_path: str = "data/luggage_room.db"):
    """
    Recalculate ownership percentages based on contributions.
    
    Call this after updating fund_contribution values.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all contributions
        cursor.execute("SELECT id, username, fund_contribution FROM users")
        users = cursor.fetchall()
        
        total_contributions = sum(user[2] for user in users if user[2])
        
        if total_contributions == 0:
            print("⚠️  No contributions recorded. Ownership percentages remain 0.")
            conn.close()
            return
        
        # Update ownership percentages
        for user_id, username, contribution in users:
            if contribution and contribution > 0:
                ownership_pct = (contribution / total_contributions) * 100
                cursor.execute(
                    "UPDATE users SET ownership_pct = ? WHERE id = ?",
                    (ownership_pct, user_id)
                )
                print(f"✅ {username}: ${contribution:,.2f} → {ownership_pct:.2f}% ownership")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Ownership percentages updated. Total fund: ${total_contributions:,.2f}")
        
    except Exception as e:
        print(f"❌ Error calculating ownership: {e}")


def add_user_contribution(
    username: str,
    contribution: float,
    db_path: str = "data/luggage_room.db"
):
    """
    Record a user's contribution to the fund.
    
    Args:
        username: User's username
        contribution: Amount contributed (USD)
        db_path: Database path
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update contribution and date
        cursor.execute(
            """
            UPDATE users 
            SET fund_contribution = fund_contribution + ?,
                last_contribution_date = ?
            WHERE username = ?
            """,
            (contribution, datetime.now(), username)
        )
        
        if cursor.rowcount == 0:
            print(f"❌ User '{username}' not found")
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        
        # Recalculate all ownership percentages
        calculate_ownership_percentages(db_path)
        
        print(f"✅ Added ${contribution:,.2f} contribution for {username}")
        return True
        
    except Exception as e:
        print(f"❌ Error adding contribution: {e}")
        return False


def get_user_ownership(username: str, db_path: str = "data/luggage_room.db") -> dict:
    """
    Get user's ownership details.
    
    Returns:
        Dictionary with contribution and ownership info
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT username, fund_contribution, ownership_pct, last_contribution_date
            FROM users
            WHERE username = ?
            """,
            (username,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'username': result[0],
                'contribution': result[1],
                'ownership_pct': result[2],
                'last_contribution_date': result[3]
            }
        return None
        
    except Exception as e:
        print(f"❌ Error getting ownership: {e}")
        return None


# ========================================================================
# CLI INTERFACE
# ========================================================================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("LRBF DATABASE MIGRATION - Pooled Fund Account")
    print("=" * 60)
    print()
    
    # Run migration
    success = migrate_users_table()
    
    if success and len(sys.argv) > 1:
        # Optional: Add initial contributions via CLI
        # Example: python migrate_pooled_account.py user1 50000 user2 50000
        args = sys.argv[1:]
        
        if len(args) % 2 == 0:
            print("\n📝 Adding initial contributions...")
            
            for i in range(0, len(args), 2):
                username = args[i]
                contribution = float(args[i + 1])
                add_user_contribution(username, contribution)
        else:
            print("\n⚠️  Invalid arguments. Usage:")
            print("   python migrate_pooled_account.py [username1 amount1 username2 amount2 ...]")
    
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)
