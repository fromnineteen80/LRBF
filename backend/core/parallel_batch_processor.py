"""
Parallel Batch Processor - Analyze 500 Stocks Efficiently

Uses multiprocessing to analyze stocks in parallel.
Target: Process 500 stocks in <10 minutes.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count
from functools import partial
import time

from backend.core.pattern_detector import PatternDetector
from backend.core.category_scorer import CategoryScorer
from backend.data.stock_universe import get_stock_universe
from backend.services.market_data import MarketDataService


class ParallelBatchProcessor:
    """
    Parallel batch processor for 500-stock universe.
    """
    
    def __init__(self, n_workers: Optional[int] = None):
        """
        Initialize parallel processor.
        
        Args:
            n_workers: Number of parallel workers (default: CPU count - 1)
        """
        self.n_workers = n_workers or max(1, cpu_count() - 1)
        print(f"🚀 Initialized with {self.n_workers} parallel workers")
    
    def process_stock(
        self,
        ticker: str,
        lookback_days: int = 20,
        target_date: Optional[date] = None
    ) -> Optional[Dict]:
        """
        Process a single stock (called by worker process).
        
        Args:
            ticker: Stock symbol
            lookback_days: Days of history to analyze
            target_date: Target date for analysis
        
        Returns:
            Dictionary with stock analysis results or None if failed
        """
        try:
            # Initialize services (per-worker)
            market_data = MarketDataService()
            pattern_detector = PatternDetector()
            scorer = CategoryScorer()
            
            if target_date is None:
                target_date = date.today()
            
            # Fetch intraminute data
            df = market_data.get_intraday_data(
                ticker=ticker,
                days=lookback_days,
                interval='1m'
            )
            
            if df.empty or len(df) < 100:
                return None
            
            # Detect all patterns
            patterns = pattern_detector.detect_all_patterns(df, ticker, target_date)
            
            if not patterns:
                return None
            
            # Calculate metrics for today (last day's patterns)
            today_patterns = [p for p in patterns if p['date'] == target_date.isoformat()]
            
            # Aggregate data for scoring
            stock_data = self._aggregate_stock_data(ticker, patterns, today_patterns, df)
            
            # Calculate composite score
            composite_score, category_scores = scorer.calculate_composite_score(stock_data)
            
            return {
                'ticker': ticker,
                'date': target_date.isoformat(),
                'composite_score': composite_score,
                'category_scores': category_scores,
                'patterns': patterns,
                'today_patterns': today_patterns,
                'stock_data': stock_data
            }
            
        except Exception as e:
            print(f"❌ Error processing {ticker}: {str(e)}")
            return None
    
    def _aggregate_stock_data(
        self,
        ticker: str,
        all_patterns: List[Dict],
        today_patterns: List[Dict],
        df: pd.DataFrame
    ) -> Dict:
        """
        Aggregate pattern data into stock-level metrics for scoring.
        
        Args:
            ticker: Stock symbol
            all_patterns: All patterns over 20 days
            today_patterns: Patterns from target date only
            df: OHLCV DataFrame
        
        Returns:
            Dictionary with aggregated metrics
        """
        # Pattern counts
        total_patterns = len(all_patterns)
        total_entries = sum(1 for p in all_patterns if p['outcome'] in ['win', 'loss'])
        wins = sum(1 for p in all_patterns if p['outcome'] == 'win')
        losses = sum(1 for p in all_patterns if p['outcome'] == 'loss')
        
        # Win/loss metrics
        win_rate = wins / total_entries if total_entries > 0 else 0
        avg_win_pct = np.mean([p['pnl_pct'] for p in all_patterns if p['outcome'] == 'win']) if wins > 0 else 0
        avg_loss_pct = np.mean([abs(p['pnl_pct']) for p in all_patterns if p['outcome'] == 'loss']) if losses > 0 else 0
        
        # Expected value
        expected_value_pct = (win_rate * avg_win_pct) - ((1 - win_rate) * avg_loss_pct)
        
        # Pattern frequency
        expected_daily_patterns = total_patterns / 20.0
        entries_per_day = total_entries / 20.0
        confirmation_rate = total_entries / total_patterns if total_patterns > 0 else 0
        
        # Dead zone metrics (from patterns)
        dead_zone_patterns = [p for p in all_patterns if p.get('dead_zone_duration', 0) > 0]
        dead_zone_frequency = (len(dead_zone_patterns) / total_patterns * 100) if total_patterns > 0 else 0
        dead_zone_duration = np.mean([p['dead_zone_duration'] for p in dead_zone_patterns]) if dead_zone_patterns else 0
        opportunity_cost = np.mean([p.get('opportunity_cost', 0) for p in dead_zone_patterns]) if dead_zone_patterns else 0
        
        # Execution metrics
        avg_volume_20d = df['volume'].mean()
        atr_pct = (df['high'] - df['low']).mean() / df['close'].mean() * 100
        spread_bps = 5.0  # Placeholder - would calculate from bid/ask if available
        
        # Time efficiency
        avg_hold_time_minutes = np.mean([p['hold_time_minutes'] for p in all_patterns if 'hold_time_minutes' in p])
        avg_bars_to_entry = np.mean([p['detection_time_bars'] for p in all_patterns if 'detection_time_bars' in p])
        
        # Execution cycle (Category #14)
        avg_cycle_time = np.mean([p['total_cycle_minutes'] for p in all_patterns if 'total_cycle_minutes' in p])
        
        # VWAP stability
        vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()
        vwap_distance = abs(df['close'] - vwap) / vwap * 100
        vwap_stability_score = vwap_distance.std()
        
        # Risk metrics
        max_drawdown_intraday = min([p['pnl_pct'] for p in all_patterns]) if all_patterns else 0
        slippage_avg_bps = 3.0  # Placeholder
        false_positive_rate = (len([p for p in all_patterns if p['outcome'] == 'loss']) / total_patterns * 100) if total_patterns > 0 else 0
        
        # News risk (placeholder - would integrate with earnings calendar)
        days_to_earnings = 100
        
        # Portfolio metrics
        avg_correlation = 0.5  # Placeholder - would calculate from price correlations
        halt_history = 0
        
        # System confidence
        performance_consistency = 75.0  # Placeholder - would calculate from daily variance
        missing_bars = (1 - len(df) / (20 * 390)) * 100  # % missing data
        
        return {
            'ticker': ticker,
            'wins_20d': wins,
            'losses_20d': losses,
            'avg_win_pct': avg_win_pct,
            'avg_loss_pct': avg_loss_pct,
            'confirmation_rate': confirmation_rate,
            'expected_value_pct': expected_value_pct,
            'vwap_occurred_20d': total_patterns,
            'entries_20d': total_entries,
            'expected_daily_patterns': expected_daily_patterns,
            'entries_per_day': entries_per_day,
            'win_rate': win_rate,
            'dead_zone_frequency': dead_zone_frequency,
            'dead_zone_duration': dead_zone_duration,
            'opportunity_cost': opportunity_cost,
            'avg_volume_20d': avg_volume_20d,
            'spread_bps': spread_bps,
            'spread_drift_std': 0.5,
            'atr_pct': atr_pct,
            'volatility_20d': df['close'].pct_change().std() * np.sqrt(252) * 100,
            'intraday_range_pct': atr_pct,
            'vwap_stability_score': vwap_stability_score,
            'vwap_distance_pct': vwap_distance.mean(),
            'avg_hold_time_minutes': avg_hold_time_minutes,
            'avg_bars_to_entry': avg_bars_to_entry,
            'time_to_target': avg_hold_time_minutes * 0.7,
            'slippage_avg_bps': slippage_avg_bps,
            'fill_quality_score': 90.0,
            'false_positive_rate': false_positive_rate,
            'pattern_quality_score': 80.0,
            'max_drawdown_intraday': max_drawdown_intraday,
            'largest_loss_20d': max_drawdown_intraday,
            'days_to_earnings': days_to_earnings,
            'news_event_density': 0,
            'avg_correlation': avg_correlation,
            'sector_classification': 'Unknown',
            'halt_history': halt_history,
            'regulatory_flags': 0,
            'avg_gap_size': 0.5,
            'performance_consistency': performance_consistency,
            'forecast_accuracy_20d': 85.0,
            'missing_bars': missing_bars,
            'anomaly_count': 0,
            'api_latency': 50.0,
            'total_cycle_minutes': avg_cycle_time,
            'avg_execution_latency_ms': 50.0,
            'settlement_lag_minutes': 0.5
        }
    
    def process_batch(
        self,
        tickers: List[str],
        lookback_days: int = 20,
        target_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Process batch of stocks in parallel.
        
        Args:
            tickers: List of stock symbols
            lookback_days: Days of history to analyze
            target_date: Target date for analysis
        
        Returns:
            List of processed stock results
        """
        start_time = time.time()
        
        print(f"\n🚀 Processing {len(tickers)} stocks with {self.n_workers} workers...")
        
        # Create partial function with fixed parameters
        process_func = partial(
            self.process_stock,
            lookback_days=lookback_days,
            target_date=target_date
        )
        
        # Process in parallel
        with Pool(processes=self.n_workers) as pool:
            results = pool.map(process_func, tickers)
        
        # Filter out None results (failed stocks)
        valid_results = [r for r in results if r is not None]
        
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ Processed {len(valid_results)}/{len(tickers)} stocks in {elapsed_time:.1f}s")
        print(f"   ({elapsed_time/len(valid_results):.2f}s per stock)")
        
        return valid_results
    
    def process_full_universe(
        self,
        lookback_days: int = 20,
        target_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Process full 500-stock universe.
        
        Args:
            lookback_days: Days of history to analyze
            target_date: Target date for analysis
        
        Returns:
            List of processed stock results
        """
        universe = get_stock_universe()
        print(f"📊 Loading universe: {len(universe)} stocks")
        
        return self.process_batch(universe, lookback_days, target_date)


# Convenience function
def analyze_universe_parallel(
    lookback_days: int = 20,
    target_date: Optional[date] = None,
    n_workers: Optional[int] = None
) -> List[Dict]:
    """
    Analyze full stock universe in parallel.
    
    Args:
        lookback_days: Days of history
        target_date: Target analysis date
        n_workers: Number of parallel workers
    
    Returns:
        List of analyzed stocks
    """
    processor = ParallelBatchProcessor(n_workers=n_workers)
    return processor.process_full_universe(lookback_days, target_date)
