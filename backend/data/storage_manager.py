"""
Storage Manager - Scalable Data Storage for 500-Stock Universe

Handles:
- Raw pattern storage (Parquet files - compressed, columnar)
- Daily score storage (SQLite/PostgreSQL)
- Efficient querying for visualizations
- Rolling window updates (20-day lookback)

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import os
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import json
from pathlib import Path


class StorageManager:
    """
    Manages data storage for pattern detection and scoring system.
    """
    
    def __init__(self, base_path: str = '/home/claude/railyard/data'):
        """
        Initialize storage manager.
        
        Args:
            base_path: Root directory for data storage
        """
        self.base_path = Path(base_path)
        self.patterns_path = self.base_path / 'raw_patterns'
        self.scores_path = self.base_path / 'daily_scores'
        self.reports_path = self.base_path / 'morning_reports'
        
        # Create directories
        self.patterns_path.mkdir(parents=True, exist_ok=True)
        self.scores_path.mkdir(parents=True, exist_ok=True)
        self.reports_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.db_path = self.scores_path / 'stock_scores.db'
        self._initialize_database()
    
    # ========================================================================
    # DATABASE INITIALIZATION
    # ========================================================================
    
    def _initialize_database(self):
        """Create database tables for daily scores and metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Daily scores table (500 stocks × 20 days = 10,000 records)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                date DATE NOT NULL,
                composite_score REAL NOT NULL,
                
                -- Tier 1: Profitability (45%)
                expected_value_score REAL,
                pattern_frequency_score REAL,
                dead_zone_score REAL,
                
                -- Tier 2: Execution (30%)
                liquidity_score REAL,
                volatility_score REAL,
                vwap_stability_score REAL,
                time_efficiency_score REAL,
                
                -- Tier 3: Risk (15%)
                slippage_score REAL,
                false_positive_score REAL,
                drawdown_score REAL,
                news_risk_score REAL,
                
                -- Tier 4: Portfolio (7%)
                correlation_score REAL,
                halt_risk_score REAL,
                execution_cycle_score REAL,
                
                -- Tier 5: Confidence (3%)
                historical_reliability_score REAL,
                data_quality_score REAL,
                
                -- Metadata
                pattern_count INTEGER,
                daily_rank INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(ticker, date)
            )
        ''')
        
        # 20-day consistency rankings (top 24 stocks)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                analysis_date DATE NOT NULL,
                
                -- 20-day aggregated metrics
                avg_composite_score REAL,
                score_std_dev REAL,
                avg_daily_rank REAL,
                rank_stability REAL,
                days_in_top_24 INTEGER,
                
                -- Final ranking
                final_rank INTEGER,
                category TEXT,  -- Conservative/Medium/Aggressive
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(ticker, analysis_date)
            )
        ''')
        
        # Pattern processing metadata (track what's been processed)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                stocks_analyzed INTEGER,
                patterns_detected INTEGER,
                processing_time_seconds REAL,
                status TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database initialized: {self.db_path}")
    
    # ========================================================================
    # RAW PATTERN STORAGE (PARQUET)
    # ========================================================================
    
    def store_patterns(self, patterns: List[Dict], date_str: str):
        """
        Store raw pattern data to Parquet file (compressed, columnar).
        
        Args:
            patterns: List of pattern dictionaries
            date_str: Date string (YYYY-MM-DD)
        """
        if not patterns:
            print(f"⚠️  No patterns to store for {date_str}")
            return
        
        df = pd.DataFrame(patterns)
        
        # Ensure all category scores are present
        required_cols = [
            'pattern_id', 'ticker', 'timestamp', 'date',
            'detection_time_bars', 'entry_latency_ms', 'hold_time_minutes',
            'exit_latency_ms', 'total_cycle_minutes', 'outcome', 'pnl',
            'expected_value_pct', 'win_rate', 'confirmation_rate'
        ]
        
        # Store to Parquet (compressed)
        file_path = self.patterns_path / f"{date_str}.parquet"
        df.to_parquet(file_path, compression='snappy', index=False)
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"✅ Stored {len(patterns):,} patterns for {date_str} ({file_size_mb:.2f} MB)")
    
    def load_patterns(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        ticker: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load raw patterns from Parquet files.
        
        Args:
            start_date: Start date (YYYY-MM-DD) or None for all
            end_date: End date (YYYY-MM-DD) or None for all
            ticker: Filter by ticker or None for all
        
        Returns:
            DataFrame with all matching patterns
        """
        pattern_files = sorted(self.patterns_path.glob("*.parquet"))
        
        if not pattern_files:
            return pd.DataFrame()
        
        # Filter by date range
        if start_date or end_date:
            filtered_files = []
            for f in pattern_files:
                file_date = f.stem  # Filename without extension
                if start_date and file_date < start_date:
                    continue
                if end_date and file_date > end_date:
                    continue
                filtered_files.append(f)
            pattern_files = filtered_files
        
        # Load and concatenate
        dfs = [pd.read_parquet(f) for f in pattern_files]
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        
        # Filter by ticker
        if ticker and not df.empty:
            df = df[df['ticker'] == ticker]
        
        print(f"✅ Loaded {len(df):,} patterns")
        return df
    
    # ========================================================================
    # DAILY SCORES STORAGE
    # ========================================================================
    
    def store_daily_scores(self, scores: List[Dict]):
        """
        Store daily composite scores for stocks.
        
        Args:
            scores: List of score dictionaries (one per stock per day)
        """
        if not scores:
            return
        
        conn = sqlite3.connect(self.db_path)
        df = pd.DataFrame(scores)
        
        # Insert or replace (in case of re-processing)
        df.to_sql('daily_scores', conn, if_exists='append', index=False)
        
        conn.close()
        print(f"✅ Stored daily scores for {len(scores)} stocks")
    
    def load_daily_scores(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        ticker: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load daily scores from database.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            ticker: Filter by ticker
        
        Returns:
            DataFrame with daily scores
        """
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM daily_scores WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if ticker:
            query += " AND ticker = ?"
            params.append(ticker)
        
        query += " ORDER BY date DESC, composite_score DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_last_20_days_scores(self, reference_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get scores for last 20 trading days (rolling window).
        
        Args:
            reference_date: Reference date (YYYY-MM-DD) or None for today
        
        Returns:
            DataFrame with 20 days of scores
        """
        if reference_date is None:
            reference_date = date.today().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        
        # Get last 20 days of data (assuming trading days only)
        query = """
            SELECT * FROM daily_scores 
            WHERE date <= ? 
            ORDER BY date DESC 
            LIMIT (SELECT COUNT(DISTINCT ticker) FROM daily_scores) * 20
        """
        
        df = pd.read_sql_query(query, conn, params=[reference_date])
        conn.close()
        
        return df
    
    # ========================================================================
    # STOCK RANKINGS STORAGE
    # ========================================================================
    
    def store_rankings(self, rankings: List[Dict], analysis_date: str):
        """
        Store 20-day stock rankings (top 24).
        
        Args:
            rankings: List of ranking dictionaries
            analysis_date: Date of analysis (YYYY-MM-DD)
        """
        conn = sqlite3.connect(self.db_path)
        
        for rank in rankings:
            rank['analysis_date'] = analysis_date
        
        df = pd.DataFrame(rankings)
        df.to_sql('stock_rankings', conn, if_exists='append', index=False)
        
        conn.close()
        print(f"✅ Stored rankings for {len(rankings)} stocks")
    
    def load_rankings(self, analysis_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load stock rankings.
        
        Args:
            analysis_date: Date of analysis or None for latest
        
        Returns:
            DataFrame with rankings
        """
        conn = sqlite3.connect(self.db_path)
        
        if analysis_date:
            query = "SELECT * FROM stock_rankings WHERE analysis_date = ? ORDER BY final_rank"
            df = pd.read_sql_query(query, conn, params=[analysis_date])
        else:
            query = """
                SELECT * FROM stock_rankings 
                WHERE analysis_date = (SELECT MAX(analysis_date) FROM stock_rankings)
                ORDER BY final_rank
            """
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    # ========================================================================
    # PROCESSING LOG
    # ========================================================================
    
    def log_processing(
        self,
        date_str: str,
        stocks_analyzed: int,
        patterns_detected: int,
        processing_time: float,
        status: str = 'success',
        error_message: Optional[str] = None
    ):
        """
        Log batch processing results.
        
        Args:
            date_str: Date processed (YYYY-MM-DD)
            stocks_analyzed: Number of stocks analyzed
            patterns_detected: Number of patterns found
            processing_time: Processing time in seconds
            status: 'success' or 'error'
            error_message: Error details if status='error'
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO processing_log 
            (date, stocks_analyzed, patterns_detected, processing_time_seconds, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date_str, stocks_analyzed, patterns_detected, processing_time, status, error_message))
        
        conn.commit()
        conn.close()
    
    def get_processing_status(self, last_n_days: int = 20) -> pd.DataFrame:
        """
        Get processing status for last N days.
        
        Args:
            last_n_days: Number of days to retrieve
        
        Returns:
            DataFrame with processing logs
        """
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT * FROM processing_log 
            ORDER BY date DESC 
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[last_n_days])
        conn.close()
        
        return df
    
    # ========================================================================
    # CLEANUP & MAINTENANCE
    # ========================================================================
    
    def cleanup_old_data(self, keep_days: int = 60):
        """
        Remove pattern data older than keep_days.
        
        Args:
            keep_days: Number of days to retain
        """
        cutoff_date = (date.today() - timedelta(days=keep_days)).isoformat()
        
        # Remove old Parquet files
        removed_count = 0
        for file_path in self.patterns_path.glob("*.parquet"):
            file_date = file_path.stem
            if file_date < cutoff_date:
                file_path.unlink()
                removed_count += 1
        
        # Remove old database records
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM daily_scores WHERE date < ?", (cutoff_date,))
        cursor.execute("DELETE FROM stock_rankings WHERE analysis_date < ?", (cutoff_date,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Cleaned up data older than {cutoff_date} ({removed_count} files removed)")
    
    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage metrics
        """
        # Pattern files
        pattern_files = list(self.patterns_path.glob("*.parquet"))
        total_pattern_size = sum(f.stat().st_size for f in pattern_files)
        
        # Database size
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        
        # Record counts
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM daily_scores")
        daily_score_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stock_rankings")
        ranking_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT date) FROM daily_scores")
        days_stored = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'pattern_files': len(pattern_files),
            'pattern_storage_mb': total_pattern_size / (1024 * 1024),
            'database_size_mb': db_size / (1024 * 1024),
            'daily_score_records': daily_score_count,
            'ranking_records': ranking_count,
            'days_stored': days_stored
        }


# Convenience functions
def get_storage_manager() -> StorageManager:
    """Get singleton storage manager instance."""
    return StorageManager()
