"""
Wall Street User Management System Migration Script

This script migrates the existing LRBF database to support:
- Role-based access control (admin/member)
- Invitation-only signup system
- Capital transaction tracking
- Monthly statements
- Audit trail

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta


def migrate_database(db_path='data/trading.db'):
    """
    Execute migration to add Wall Street-level user management.
    
    Args:
        db_path: Path to SQLite database file
    
    Returns:
        bool: True if migration successful, False otherwise
    """
    print("\n" + "="*70)
    print("  WALL STREET USER MANAGEMENT SYSTEM - DATABASE MIGRATION")
    print("="*70 + "\n")
    
    if not os.path.exists(db_path):
        print(f"❌ ERROR: Database not found at {db_path}")
        print("   Please ensure the application has been initialized first.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Step 1: Add role column to users table
        print("📊 Step 1: Adding role column to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'member'")
            print("   ✅ Role column added successfully")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⚠️  Role column already exists - skipping")
            else:
                raise
        
        # Step 2: Create invitations table
        print("\n📊 Step 2: Creating invitations table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                first_name TEXT,
                invite_token TEXT UNIQUE NOT NULL,
                invited_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0,
                used_at TIMESTAMP,
                used_by INTEGER,
                FOREIGN KEY (invited_by) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invite_token ON invitations(invite_token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invite_email ON invitations(email)")
        print("   ✅ Invitations table created successfully")
        
        # Step 3: Create capital_transactions table
        print("\n📊 Step 3: Creating capital_transactions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capital_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_date DATE NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_after REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_capital_user ON capital_transactions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_capital_date ON capital_transactions(transaction_date)")
        print("   ✅ Capital transactions table created successfully")
        
        # Step 4: Create monthly_statements table
        print("\n📊 Step 4: Creating monthly_statements table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_statements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                statement_date DATE NOT NULL,
                opening_balance REAL NOT NULL,
                contributions REAL DEFAULT 0,
                distributions REAL DEFAULT 0,
                profit_loss REAL DEFAULT 0,
                closing_balance REAL NOT NULL,
                ownership_pct REAL NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, statement_date)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_statement_user ON monthly_statements(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_statement_date ON monthly_statements(statement_date)")
        print("   ✅ Monthly statements table created successfully")
        
        # Step 5: Create audit_log table
        print("\n📊 Step 5: Creating audit_log table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
        print("   ✅ Audit log table created successfully")
        
        # Step 6: Set first user as admin
        print("\n📊 Step 6: Setting first user as admin...")
        cursor.execute("SELECT id, username FROM users ORDER BY id LIMIT 1")
        first_user = cursor.fetchone()
        
        if first_user:
            cursor.execute("UPDATE users SET role = 'admin' WHERE id = ?", (first_user[0],))
            print(f"   ✅ User '{first_user[1]}' (ID: {first_user[0]}) set as admin")
        else:
            print("   ⚠️  No users found - first user to sign up will be admin")
        
        # Step 7: Migrate existing fund contributions to capital_transactions
        print("\n📊 Step 7: Migrating existing fund contributions...")
        cursor.execute("""
            SELECT id, username, fund_contribution 
            FROM users 
            WHERE fund_contribution > 0
        """)
        existing_contributions = cursor.fetchall()
        
        if existing_contributions:
            for user_id, username, amount in existing_contributions:
                # Check if already migrated
                cursor.execute("""
                    SELECT COUNT(*) FROM capital_transactions 
                    WHERE user_id = ? AND notes LIKE '%Initial capital contribution%'
                """, (user_id,))
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO capital_transactions 
                        (user_id, transaction_date, transaction_type, amount, balance_after, notes)
                        VALUES (?, ?, 'contribution', ?, ?, 'Initial capital contribution (migrated)')
                    """, (user_id, datetime.now().date(), amount, amount))
                    print(f"   ✅ Migrated ${amount:,.2f} for user '{username}'")
                else:
                    print(f"   ⚠️  Contribution for '{username}' already migrated - skipping")
            
            print(f"\n   📝 Total contributions migrated: {len(existing_contributions)}")
        else:
            print("   ⚠️  No existing contributions to migrate")
        
        # Step 8: Recalculate ownership percentages
        print("\n📊 Step 8: Recalculating ownership percentages...")
        cursor.execute("SELECT SUM(fund_contribution) FROM users")
        total_capital = cursor.fetchone()[0] or 0
        
        if total_capital > 0:
            cursor.execute("SELECT id, username, fund_contribution FROM users")
            users = cursor.fetchall()
            
            for user_id, username, contribution in users:
                ownership_pct = (contribution / total_capital) * 100 if total_capital > 0 else 0
                cursor.execute("UPDATE users SET ownership_pct = ? WHERE id = ?", (ownership_pct, user_id))
                print(f"   ✅ {username}: {ownership_pct:.2f}% ownership")
        else:
            print("   ⚠️  No capital contributions - ownership percentages remain at 0%")
        
        # Commit all changes
        conn.commit()
        
        # Step 9: Verify migration
        print("\n📊 Step 9: Verifying migration...")
        
        # Check all tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN (
                'invitations', 'capital_transactions', 'monthly_statements', 'audit_log'
            )
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['audit_log', 'capital_transactions', 'invitations', 'monthly_statements']
        if set(tables) == set(expected_tables):
            print("   ✅ All new tables verified")
        else:
            missing = set(expected_tables) - set(tables)
            print(f"   ❌ Missing tables: {missing}")
            return False
        
        # Check role column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'role' in columns:
            print("   ✅ Role column verified")
        else:
            print("   ❌ Role column missing")
            return False
        
        # Check for admin user
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        print(f"   ✅ Admin users: {admin_count}")
        
        # Check capital transactions
        cursor.execute("SELECT COUNT(*) FROM capital_transactions")
        transaction_count = cursor.fetchone()[0]
        print(f"   ✅ Capital transactions: {transaction_count}")
        
        conn.close()
        
        # Success summary
        print("\n" + "="*70)
        print("  ✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\n📋 Summary:")
        print(f"   • Database: {db_path}")
        print(f"   • New tables: {len(expected_tables)}")
        print(f"   • Admin users: {admin_count}")
        print(f"   • Capital transactions: {transaction_count}")
        print(f"   • Total capital: ${total_capital:,.2f}")
        print("\n🎉 Your fund is now ready for Wall Street-level management!\n")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ DATABASE ERROR: {e}")
        print("   Migration failed. Database has been left unchanged.")
        return False
    
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        print("   Migration failed. Please check the error and try again.")
        return False


def print_usage():
    """Print usage instructions."""
    print("\nUsage:")
    print("  python migrate_wall_street.py")
    print("  python migrate_wall_street.py [path/to/database.db]")
    print("\nExamples:")
    print("  python migrate_wall_street.py")
    print("  python migrate_wall_street.py data/trading.db")
    print("  python migrate_wall_street.py data/custom_db.db")
    print()


if __name__ == '__main__':
    # Handle command line arguments
    if len(sys.argv) > 2:
        print("❌ ERROR: Too many arguments")
        print_usage()
        sys.exit(1)
    
    # Get database path from argument or use default
    db_path = sys.argv[1] if len(sys.argv) == 2 else 'data/trading.db'
    
    # Show usage if help requested
    if db_path in ['-h', '--help', 'help']:
        print_usage()
        sys.exit(0)
    
    # Run migration
    success = migrate_database(db_path)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
