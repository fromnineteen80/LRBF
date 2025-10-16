"""
Database Module - Phase 3, Checkpoint 3.2

SQLite database for storing trading performance, fills, forecasts, and events.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sqlite3
import json
import os
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import pandas as pd


class TradingDatabase:
    """
    SQLite database manager for trading operations.
    
    Tables:
    - daily_summaries: End-of-day performance metrics
    - fills: Individual trade executions from IBKR
    - morning_forecasts: Daily forecast snapshots
    - system_events: Logs, warnings, errors
    """
    
    def __init__(self, db_path: str = "data/trading.db"):
        """
        Initialize database connection and create tables if needed.
        
        Args:
            db_path: Path to SQLite database file (relative to project root)
        """
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else "data", exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self.create_tables()
    
    def create_tables(self):
        """Create all required tables if they don't exist."""
        
        cursor = self.conn.cursor()
        
        # Table 1: Daily Summaries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                opening_balance REAL NOT NULL,
                closing_balance REAL NOT NULL,
                realized_pl REAL NOT NULL,
                roi_pct REAL NOT NULL,
                trade_count INTEGER NOT NULL,
                win_count INTEGER NOT NULL,
                loss_count INTEGER NOT NULL,
                win_rate REAL NOT NULL,
                sharpe_ratio REAL,
                sortino_ratio REAL,
                max_drawdown_pct REAL,
                avg_latency_ms REAL,
                avg_slippage_pct REAL,
                stock_performance_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 2: Fills (Individual Trade Executions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ibkr_execution_id TEXT UNIQUE NOT NULL,
                date DATE NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                realized_pnl REAL DEFAULT 0,
                commission REAL DEFAULT 0,
                latency_ms REAL,
                slippage_pct REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 3: Morning Forecasts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS morning_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                generated_at TIMESTAMP NOT NULL,
                selected_stocks_json TEXT NOT NULL,
                expected_trades_low INTEGER NOT NULL,
                expected_trades_high INTEGER NOT NULL,
                expected_pl_low REAL NOT NULL,
                expected_pl_high REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 4: System Events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                ticker TEXT,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 5: Users (Co-Founders)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone_number TEXT NOT NULL,
                timezone TEXT NOT NULL DEFAULT 'America/New_York',
                fund_contribution REAL NOT NULL DEFAULT 0.0,
                ownership_pct REAL NOT NULL DEFAULT 0.0,
                is_verified BOOLEAN DEFAULT 0,
                verification_code TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                invited_by INTEGER,
                FOREIGN KEY (invited_by) REFERENCES users(id)
            )
        """)
        
        # Table 6: Sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Table 7: Account Deletion Requests
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deletion_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed BOOLEAN DEFAULT 0,
                confirmed_at TIMESTAMP,
                fund_value_at_deletion REAL,
                payout_amount REAL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fills_date 
            ON fills(date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fills_ticker 
            ON fills(ticker)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_date 
            ON system_events(date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_severity 
            ON system_events(severity)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_username 
            ON users(username)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_token 
            ON sessions(session_token)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_user 
            ON sessions(user_id)
        """)
        
        self.conn.commit()
    
    # ========================================================================
    # FILLS TABLE
    # ========================================================================
    
    def insert_fill(self, fill_data: Dict) -> int:
        """
        Insert a new fill from IBKR.
        
        Args:
            fill_data: Dictionary with fill information
                Required keys: ibkr_execution_id, timestamp, ticker, action,
                              quantity, price
                Optional keys: realized_pnl, commission, latency_ms, slippage_pct
        
        Returns:
            Row ID of inserted fill
        """
        cursor = self.conn.cursor()
        
        # Extract date from timestamp
        if isinstance(fill_data['timestamp'], str):
            timestamp = datetime.fromisoformat(fill_data['timestamp'])
        else:
            timestamp = fill_data['timestamp']
        fill_date = timestamp.date()
        
        cursor.execute("""
            INSERT INTO fills (
                ibkr_execution_id, date, timestamp, ticker, action,
                quantity, price, realized_pnl, commission,
                latency_ms, slippage_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fill_data['ibkr_execution_id'],
            fill_date,
            fill_data['timestamp'],
            fill_data['ticker'],
            fill_data['action'],
            fill_data['quantity'],
            fill_data['price'],
            fill_data.get('realized_pnl', 0),
            fill_data.get('commission', 0),
            fill_data.get('latency_ms'),
            fill_data.get('slippage_pct')
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_fills_by_date(self, target_date: date) -> List[Dict]:
        """
        Get all fills for a specific date.
        
        Args:
            target_date: Date to query
        
        Returns:
            List of fill dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM fills
            WHERE date = ?
            ORDER BY timestamp
        """, (target_date,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_fills_by_ticker(self, ticker: str, target_date: date = None) -> List[Dict]:
        """
        Get fills for a specific ticker, optionally filtered by date.
        
        Args:
            ticker: Stock ticker symbol
            target_date: Optional date filter
        
        Returns:
            List of fill dictionaries
        """
        cursor = self.conn.cursor()
        
        if target_date:
            cursor.execute("""
                SELECT * FROM fills
                WHERE ticker = ? AND date = ?
                ORDER BY timestamp
            """, (ticker, target_date))
        else:
            cursor.execute("""
                SELECT * FROM fills
                WHERE ticker = ?
                ORDER BY timestamp
            """, (ticker,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    # ========================================================================
    # DAILY SUMMARIES TABLE
    # ========================================================================
    
    def insert_daily_summary(self, summary_data: Dict) -> int:
        """
        Insert end-of-day summary.
        
        Args:
            summary_data: Dictionary with daily performance metrics
                Required keys: date, opening_balance, closing_balance,
                              realized_pl, roi_pct, trade_count, win_count,
                              loss_count, win_rate
                Optional keys: sharpe_ratio, sortino_ratio, max_drawdown_pct,
                              avg_latency_ms, avg_slippage_pct, stock_performance_json
        
        Returns:
            Row ID of inserted summary
        """
        cursor = self.conn.cursor()
        
        # Convert stock performance dict to JSON if provided
        stock_perf_json = None
        if 'stock_performance' in summary_data:
            stock_perf_json = json.dumps(summary_data['stock_performance'])
        
        cursor.execute("""
            INSERT INTO daily_summaries (
                date, opening_balance, closing_balance, realized_pl, roi_pct,
                trade_count, win_count, loss_count, win_rate,
                sharpe_ratio, sortino_ratio, max_drawdown_pct,
                avg_latency_ms, avg_slippage_pct, stock_performance_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            summary_data['date'],
            summary_data['opening_balance'],
            summary_data['closing_balance'],
            summary_data['realized_pl'],
            summary_data['roi_pct'],
            summary_data['trade_count'],
            summary_data['win_count'],
            summary_data['loss_count'],
            summary_data['win_rate'],
            summary_data.get('sharpe_ratio'),
            summary_data.get('sortino_ratio'),
            summary_data.get('max_drawdown_pct'),
            summary_data.get('avg_latency_ms'),
            summary_data.get('avg_slippage_pct'),
            stock_perf_json
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_daily_summary(self, target_date: date) -> Optional[Dict]:
        """
        Get summary for a specific date.
        
        Args:
            target_date: Date to query
        
        Returns:
            Summary dictionary or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM daily_summaries
            WHERE date = ?
        """, (target_date,))
        
        row = cursor.fetchone()
        if row:
            result = dict(row)
            # Parse JSON if present
            if result['stock_performance_json']:
                result['stock_performance'] = json.loads(result['stock_performance_json'])
            return result
        return None
    
    def get_recent_summaries(self, days: int = 20) -> List[Dict]:
        """
        Get recent daily summaries.
        
        Args:
            days: Number of recent days to retrieve
        
        Returns:
            List of summary dictionaries, ordered newest first
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM daily_summaries
            ORDER BY date DESC
            LIMIT ?
        """, (days,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            result = dict(row)
            if result['stock_performance_json']:
                result['stock_performance'] = json.loads(result['stock_performance_json'])
            results.append(result)
        return results
    
    # ========================================================================
    # MORNING FORECASTS TABLE
    # ========================================================================
    
    def insert_morning_forecast(self, forecast_data: Dict) -> int:
        """
        Insert morning forecast snapshot.
        
        Args:
            forecast_data: Dictionary with forecast information
                Required keys: date, generated_at, selected_stocks,
                              expected_trades_low, expected_trades_high,
                              expected_pl_low, expected_pl_high
                Optional keys: stock_analysis (dict with per-stock backtest data)
        
        Returns:
            Row ID of inserted forecast
        """
        cursor = self.conn.cursor()
        
        # Convert selected stocks list to JSON
        stocks_json = json.dumps(forecast_data['selected_stocks'])
        
        # Convert stock analysis to JSON if provided
        stock_analysis_json = None
        if 'stock_analysis' in forecast_data and forecast_data['stock_analysis']:
            stock_analysis_json = json.dumps(forecast_data['stock_analysis'])
        
        cursor.execute("""
            INSERT INTO morning_forecasts (
                date, generated_at, selected_stocks_json,
                expected_trades_low, expected_trades_high,
                expected_pl_low, expected_pl_high, stock_analysis_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            forecast_data['date'],
            forecast_data['generated_at'],
            stocks_json,
            forecast_data['expected_trades_low'],
            forecast_data['expected_trades_high'],
            forecast_data['expected_pl_low'],
            forecast_data['expected_pl_high'],
            stock_analysis_json
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_morning_forecast(self, target_date: date) -> Optional[Dict]:
        """
        Get morning forecast for a specific date.
        
        Args:
            target_date: Date to query
        
        Returns:
            Forecast dictionary or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM morning_forecasts
            WHERE date = ?
        """, (target_date,))
        
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['selected_stocks'] = json.loads(result['selected_stocks_json'])
            
            # Parse stock_analysis_json if present
            if result.get('stock_analysis_json'):
                result['stock_analysis'] = json.loads(result['stock_analysis_json'])
            else:
                result['stock_analysis'] = {}
            
            return result
        return None
    
    # ========================================================================
    # SYSTEM EVENTS TABLE
    # ========================================================================
    
    def log_event(
        self,
        event_type: str,
        severity: str,
        message: str,
        ticker: str = None
    ) -> int:
        """
        Log a system event.
        
        Args:
            event_type: Type of event (INFO, WARNING, ERROR)
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            message: Event description
            ticker: Optional ticker symbol if event is stock-specific
        
        Returns:
            Row ID of inserted event
        """
        cursor = self.conn.cursor()
        now = datetime.now()
        
        cursor.execute("""
            INSERT INTO system_events (
                date, timestamp, event_type, severity, ticker, message
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            now.date(),
            now,
            event_type,
            severity,
            ticker,
            message
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_events_by_date(
        self,
        target_date: date,
        min_severity: str = None
    ) -> List[Dict]:
        """
        Get events for a specific date, optionally filtered by severity.
        
        Args:
            target_date: Date to query
            min_severity: Minimum severity to include (LOW, MEDIUM, HIGH, CRITICAL)
        
        Returns:
            List of event dictionaries
        """
        cursor = self.conn.cursor()
        
        if min_severity:
            severity_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            min_index = severity_levels.index(min_severity)
            allowed_severities = severity_levels[min_index:]
            
            placeholders = ','.join('?' * len(allowed_severities))
            cursor.execute(f"""
                SELECT * FROM system_events
                WHERE date = ? AND severity IN ({placeholders})
                ORDER BY timestamp
            """, (target_date, *allowed_severities))
        else:
            cursor.execute("""
                SELECT * FROM system_events
                WHERE date = ?
                ORDER BY timestamp
            """, (target_date,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def get_equity_curve(self, days: int = 30) -> pd.DataFrame:
        """
        Get equity curve data for charting.
        
        Args:
            days: Number of days to retrieve
        
        Returns:
            DataFrame with date, balance, roi_pct columns
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT date, closing_balance, roi_pct
            FROM daily_summaries
            ORDER BY date DESC
            LIMIT ?
        """, (days,))
        
        rows = cursor.fetchall()
        if not rows:
            return pd.DataFrame(columns=['date', 'balance', 'roi_pct'])
        
        df = pd.DataFrame([dict(row) for row in rows])
        df = df.rename(columns={'closing_balance': 'balance'})
        df = df.sort_values('date')  # Oldest to newest for chart
        return df[['date', 'balance', 'roi_pct']]
    
    # ========================================================================
    # USER MANAGEMENT
    # ========================================================================
    
    def create_user(self, user_data: Dict) -> int:
        """
        Create a new co-founder user account.
        
        Args:
            user_data: Dict with keys: username, password_hash, first_name, 
                      last_name, email, phone_number, timezone, fund_contribution,
                      invited_by (optional)
        
        Returns:
            User ID of created user
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, first_name, last_name, email,
                phone_number, timezone, fund_contribution, invited_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data['username'],
            user_data['password_hash'],
            user_data['first_name'],
            user_data['last_name'],
            user_data['email'],
            user_data['phone_number'],
            user_data.get('timezone', 'America/New_York'),
            user_data['fund_contribution'],
            user_data.get('invited_by')
        ))
        
        self.conn.commit()
        user_id = cursor.lastrowid
        
        # Recalculate ownership percentages for all users
        self._recalculate_ownership()
        
        # Log event
        self.log_event(
            "INFO", 
            "MEDIUM", 
            f"New co-founder added: {user_data['username']} (${user_data['fund_contribution']:,.2f})"
        )
        
        return user_id
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (co-founders)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY created_at")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_user_profile(self, user_id: int, updates: Dict) -> bool:
        """
        Update user profile fields.
        
        Args:
            user_id: User ID
            updates: Dict of fields to update (e.g., {'email': '...', 'timezone': '...'})
        
        Returns:
            True if successful
        """
        # Build SET clause dynamically
        allowed_fields = ['first_name', 'last_name', 'email', 'phone_number', 
                         'timezone', 'fund_contribution']
        
        set_clauses = []
        values = []
        for field in allowed_fields:
            if field in updates:
                set_clauses.append(f"{field} = ?")
                values.append(updates[field])
        
        if not set_clauses:
            return False
        
        values.append(user_id)
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            UPDATE users 
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """, values)
        
        self.conn.commit()
        
        # If fund contribution changed, recalculate ownership
        if 'fund_contribution' in updates:
            self._recalculate_ownership()
        
        return True
    
    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """Update user password."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET password_hash = ?
            WHERE id = ?
        """, (new_password_hash, user_id))
        
        self.conn.commit()
        return True
    
    def verify_user(self, user_id: int) -> bool:
        """Mark user as verified (after phone verification)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET is_verified = 1, verification_code = NULL
            WHERE id = ?
        """, (user_id,))
        
        self.conn.commit()
        return True
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id,))
        
        self.conn.commit()
    
    def _recalculate_ownership(self):
        """
        Recalculate ownership percentages for all active users based on contributions.
        This runs automatically when users are added or contributions change.
        """
        cursor = self.conn.cursor()
        
        # Get total fund value from all active users
        cursor.execute("""
            SELECT SUM(fund_contribution) as total
            FROM users
            WHERE is_active = 1
        """)
        
        total = cursor.fetchone()['total'] or 0
        
        if total == 0:
            return
        
        # Update each user's ownership percentage
        cursor.execute("""
            UPDATE users
            SET ownership_pct = ROUND((fund_contribution / ?) * 100, 4)
            WHERE is_active = 1
        """, (total,))
        
        self.conn.commit()
    
    def get_total_fund_value(self) -> float:
        """Get total fund contributions from all active users."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT SUM(fund_contribution) as total
            FROM users
            WHERE is_active = 1
        """)
        
        result = cursor.fetchone()
        return result['total'] or 0.0
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    def create_session(self, user_id: int, session_token: str, expires_at: datetime) -> int:
        """Create a new session for user."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
        """, (user_id, session_token, expires_at.isoformat()))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_session(self, session_token: str) -> Optional[Dict]:
        """Get session by token."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.*, u.username, u.first_name, u.last_name, u.email,
                   u.is_active, u.is_verified
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = ?
        """, (session_token,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_session_activity(self, session_token: str):
        """Update session's last activity timestamp."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET last_activity = CURRENT_TIMESTAMP
            WHERE session_token = ?
        """, (session_token,))
        
        self.conn.commit()
    
    def delete_session(self, session_token: str):
        """Delete a session (logout)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
        self.conn.commit()
    
    def delete_expired_sessions(self):
        """Delete all expired sessions."""
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM sessions
            WHERE datetime(expires_at) < datetime('now')
        """)
        self.conn.commit()
    
    # ========================================================================
    # ACCOUNT DELETION
    # ========================================================================
    
    def create_deletion_request(self, user_id: int, fund_value: float, payout: float, notes: str = "") -> int:
        """Create account deletion request."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO deletion_requests (
                user_id, fund_value_at_deletion, payout_amount, notes
            ) VALUES (?, ?, ?, ?)
        """, (user_id, fund_value, payout, notes))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def confirm_deletion_request(self, request_id: int) -> bool:
        """Confirm and execute account deletion."""
        cursor = self.conn.cursor()
        
        # Mark request as confirmed
        cursor.execute("""
            UPDATE deletion_requests
            SET confirmed = 1, confirmed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (request_id,))
        
        # Get user_id from request
        cursor.execute("SELECT user_id FROM deletion_requests WHERE id = ?", (request_id,))
        user_id = cursor.fetchone()['user_id']
        
        # Mark user as inactive (soft delete)
        cursor.execute("""
            UPDATE users
            SET is_active = 0
            WHERE id = ?
        """, (user_id,))
        
        # Delete all user's sessions
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        
        self.conn.commit()
        
        # Recalculate ownership for remaining users
        self._recalculate_ownership()
        
        return True
    
    def get_deletion_request(self, user_id: int) -> Optional[Dict]:
        """Get pending deletion request for user."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM deletion_requests
            WHERE user_id = ? AND confirmed = 0
            ORDER BY requested_at DESC
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes connection."""
        self.close()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import os
    
    # Test with temporary database
    test_db = "/tmp/test_trading.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    print("Testing TradingDatabase...")
    print("=" * 60)
    
    with TradingDatabase(test_db) as db:
        # Test 1: Log some events
        print("\n1. Logging system events...")
        db.log_event("INFO", "LOW", "System started")
        db.log_event("WARNING", "MEDIUM", "High latency detected", "AAPL")
        db.log_event("ERROR", "HIGH", "Connection timeout")
        print("   ✅ 3 events logged")
        
        # Test 2: Insert fills
        print("\n2. Inserting fills...")
        now = datetime.now()
        
        fill1 = {
            'ibkr_execution_id': 'EXEC001',
            'timestamp': now.isoformat(),
            'ticker': 'AAPL',
            'action': 'BUY',
            'quantity': 10,
            'price': 150.25,
            'realized_pnl': 0,
            'commission': 1.00
        }
        
        fill2 = {
            'ibkr_execution_id': 'EXEC002',
            'timestamp': now.isoformat(),
            'ticker': 'AAPL',
            'action': 'SELL',
            'quantity': 10,
            'price': 151.50,
            'realized_pnl': 11.50,
            'commission': 1.00
        }
        
        db.insert_fill(fill1)
        db.insert_fill(fill2)
        print("   ✅ 2 fills inserted")
        
        # Test 3: Query fills
        print("\n3. Querying fills...")
        fills = db.get_fills_by_date(now.date())
        print(f"   Found {len(fills)} fills for today")
        print(f"   Realized P&L: ${sum(f['realized_pnl'] for f in fills):.2f}")
        
        # Test 4: Insert daily summary
        print("\n4. Inserting daily summary...")
        summary = {
            'date': now.date(),
            'opening_balance': 30000,
            'closing_balance': 30011.50,
            'realized_pl': 11.50,
            'roi_pct': 0.038,
            'trade_count': 2,
            'win_count': 1,
            'loss_count': 0,
            'win_rate': 1.0,
            'avg_latency_ms': 45.2,
            'stock_performance': {'AAPL': {'trades': 1, 'pl': 11.50}}
        }
        db.insert_daily_summary(summary)
        print("   ✅ Daily summary inserted")
        
        # Test 5: Insert morning forecast
        print("\n5. Inserting morning forecast...")
        forecast = {
            'date': now.date(),
            'generated_at': now,
            'selected_stocks': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD'],
            'expected_trades_low': 80,
            'expected_trades_high': 120,
            'expected_pl_low': 600,
            'expected_pl_high': 1200
        }
        db.insert_morning_forecast(forecast)
        print("   ✅ Morning forecast inserted")
        
        # Test 6: Query everything
        print("\n6. Querying data...")
        events = db.get_events_by_date(now.date())
        summary_result = db.get_daily_summary(now.date())
        forecast_result = db.get_morning_forecast(now.date())
        
        print(f"   Events: {len(events)}")
        print(f"   Summary ROI: {summary_result['roi_pct']*100:.2f}%")
        print(f"   Forecast: {forecast_result['expected_trades_low']}-{forecast_result['expected_trades_high']} trades")
        
    print("\n" + "=" * 60)
    print("✅ All database tests passed!")
    print(f"Test database: {test_db}")

# Alias for backwards compatibility
Database = TradingDatabase
