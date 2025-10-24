"""
Filter Report - Track Filter Impact and A/B Testing
Analyzes performance difference between filtered and unfiltered trades
"""

from datetime import datetime, date
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from config.config import TradingConfig


class FilterReporter:
    """
    Tracks and reports on filter performance and impact.
    Used for A/B testing and optimization.
    """
    
    def __init__(self, config: TradingConfig = None):
        """Initialize filter reporter with configuration."""
        self.config = config or TradingConfig
        self.filter_events = []
        self.simulated_trades = []  # Trades that would have happened without filters
        self.actual_trades = []     # Trades that actually happened with filters
    
    def log_filter_event(
        self,
        ticker: str,
        pattern_data: Dict,
        filter_results: Dict,
        trade_allowed: bool,
        timestamp: datetime = None
    ):
        """
        Log a filter check event.
        
        Args:
            ticker: Stock symbol
            pattern_data: Pattern detection results
            filter_results: Results from filter_engine
            trade_allowed: Whether trade was allowed
            timestamp: Event timestamp
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        event = {
            'timestamp': timestamp.isoformat(),
            'date': timestamp.date().isoformat(),
            'ticker': ticker,
            'entry_price': pattern_data.get('entry_price', 0),
            'trade_allowed': trade_allowed,
            'filters_checked': filter_results.get('filters_checked', []),
            'filters_passed': filter_results.get('filters_passed', []),
            'filters_failed': filter_results.get('filters_failed', []),
            'pattern_data': pattern_data
        }
        
        self.filter_events.append(event)
        
        # If tracking filter impact, simulate what would happen without filters
        if self.config.TRACK_FILTER_IMPACT:
            self._simulate_unfiltered_trade(ticker, pattern_data, timestamp)
    
    def _simulate_unfiltered_trade(
        self,
        ticker: str,
        pattern_data: Dict,
        timestamp: datetime
    ):
        """
        Simulate trade outcome if filters were not applied.
        Used for A/B testing comparison.
        """
        # Store simulated trade for later comparison
        simulated = {
            'timestamp': timestamp.isoformat(),
            'date': timestamp.date().isoformat(),
            'ticker': ticker,
            'entry_price': pattern_data.get('entry_price', 0),
            'target_1': pattern_data.get('target_1', 0),
            'target_2': pattern_data.get('target_2', 0),
            'stop_loss': pattern_data.get('stop_loss', 0),
            'expected_value': pattern_data.get('expected_value', 0),
            'simulated': True
        }
        
        self.simulated_trades.append(simulated)
    
    def log_actual_trade(
        self,
        ticker: str,
        entry_price: float,
        exit_price: float,
        pnl: float,
        trade_outcome: str,
        timestamp: datetime = None
    ):
        """
        Log an actual trade that was executed.
        
        Args:
            ticker: Stock symbol
            entry_price: Entry price
            exit_price: Exit price
            pnl: Profit/loss
            trade_outcome: 'win' or 'loss'
            timestamp: Trade timestamp
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        trade = {
            'timestamp': timestamp.isoformat(),
            'date': timestamp.date().isoformat(),
            'ticker': ticker,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_pct': (exit_price - entry_price) / entry_price * 100,
            'outcome': trade_outcome,
            'simulated': False
        }
        
        self.actual_trades.append(trade)
    
    def get_daily_filter_summary(self, target_date: date = None) -> Dict:
        """
        Generate daily summary of filter performance.
        
        Args:
            target_date: Date to summarize (defaults to today)
        
        Returns:
            Dictionary with filter statistics
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        date_str = target_date.isoformat()
        
        # Filter events for this date
        daily_events = [
            e for e in self.filter_events
            if e['date'] == date_str
        ]
        
        if not daily_events:
            return {
                'date': date_str,
                'total_patterns': 0,
                'trades_allowed': 0,
                'trades_blocked': 0,
                'block_rate': 0.0,
                'filter_breakdown': {}
            }
        
        total = len(daily_events)
        allowed = sum(1 for e in daily_events if e['trade_allowed'])
        blocked = total - allowed
        
        # Count failures by filter type
        filter_failures = {}
        for event in daily_events:
            if not event['trade_allowed']:
                for failure in event['filters_failed']:
                    filter_name = failure.split(':')[0].strip()
                    filter_failures[filter_name] = filter_failures.get(filter_name, 0) + 1
        
        return {
            'date': date_str,
            'total_patterns': total,
            'trades_allowed': allowed,
            'trades_blocked': blocked,
            'block_rate': (blocked / total * 100) if total > 0 else 0.0,
            'filter_breakdown': filter_failures
        }
    
    def get_ab_test_comparison(self, target_date: date = None) -> Dict:
        """
        Compare filtered vs unfiltered performance.
        Only available when AB_TEST_MODE is enabled.
        
        Args:
            target_date: Date to compare (defaults to today)
        
        Returns:
            Dictionary with A/B test results
        """
        if not self.config.AB_TEST_MODE:
            return {
                'error': 'A/B test mode not enabled',
                'ab_test_mode': False
            }
        
        if target_date is None:
            target_date = datetime.now().date()
        
        date_str = target_date.isoformat()
        
        # Get actual trades for this date
        actual = [
            t for t in self.actual_trades
            if t['date'] == date_str
        ]
        
        # Get simulated trades for this date
        simulated = [
            t for t in self.simulated_trades
            if t['date'] == date_str
        ]
        
        # Calculate metrics for actual trades
        actual_metrics = self._calculate_trade_metrics(actual)
        
        # For simulated trades, we need to estimate outcomes
        # based on historical win rates and average gains/losses
        simulated_metrics = self._estimate_simulated_metrics(simulated)
        
        # Calculate improvement
        improvement = {}
        for key in ['avg_pnl_pct', 'win_rate', 'total_pnl']:
            if simulated_metrics.get(key, 0) != 0:
                improvement[key] = (
                    (actual_metrics.get(key, 0) - simulated_metrics.get(key, 0)) / 
                    abs(simulated_metrics.get(key, 0)) * 100
                )
            else:
                improvement[key] = 0.0
        
        return {
            'date': date_str,
            'ab_test_mode': True,
            'with_filters': actual_metrics,
            'without_filters': simulated_metrics,
            'improvement': improvement,
            'trades_prevented': len(simulated) - len(actual)
        }
    
    def _calculate_trade_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate metrics from actual trades."""
        if not trades:
            return {
                'trade_count': 0,
                'win_count': 0,
                'loss_count': 0,
                'win_rate': 0.0,
                'avg_pnl_pct': 0.0,
                'total_pnl': 0.0,
                'avg_win_pct': 0.0,
                'avg_loss_pct': 0.0
            }
        
        wins = [t for t in trades if t['outcome'] == 'win']
        losses = [t for t in trades if t['outcome'] == 'loss']
        
        return {
            'trade_count': len(trades),
            'win_count': len(wins),
            'loss_count': len(losses),
            'win_rate': len(wins) / len(trades) * 100 if trades else 0.0,
            'avg_pnl_pct': np.mean([t['pnl_pct'] for t in trades]),
            'total_pnl': sum(t['pnl'] for t in trades),
            'avg_win_pct': np.mean([t['pnl_pct'] for t in wins]) if wins else 0.0,
            'avg_loss_pct': np.mean([t['pnl_pct'] for t in losses]) if losses else 0.0
        }
    
    def _estimate_simulated_metrics(self, simulated_trades: List[Dict]) -> Dict:
        """
        Estimate metrics for simulated (unfiltered) trades.
        Uses expected values from pattern detector.
        """
        if not simulated_trades:
            return {
                'trade_count': 0,
                'win_count': 0,
                'loss_count': 0,
                'win_rate': 0.0,
                'avg_pnl_pct': 0.0,
                'total_pnl': 0.0,
                'avg_win_pct': 0.0,
                'avg_loss_pct': 0.0,
                'estimated': True
            }
        
        # Use historical pattern performance to estimate
        # In production, these would come from pattern_detector's historical data
        # For now, use conservative estimates
        estimated_win_rate = 0.55  # 55% win rate without filters
        avg_win = 1.2  # 1.2% average win
        avg_loss = -0.5  # -0.5% average loss
        
        trade_count = len(simulated_trades)
        win_count = int(trade_count * estimated_win_rate)
        loss_count = trade_count - win_count
        
        # Estimate P&L
        estimated_pnl_pct = (win_count * avg_win + loss_count * avg_loss) / trade_count
        
        return {
            'trade_count': trade_count,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': estimated_win_rate * 100,
            'avg_pnl_pct': estimated_pnl_pct,
            'total_pnl': 0.0,  # Can't estimate without position sizes
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'estimated': True
        }
    
    def get_filter_impact_report(self, days: int = 7) -> Dict:
        """
        Generate multi-day report on filter impact.
        
        Args:
            days: Number of days to include in report
        
        Returns:
            Dictionary with aggregated filter statistics
        """
        end_date = datetime.now().date()
        start_date = end_date - pd.Timedelta(days=days-1)
        
        # Get all events in date range
        events_in_range = [
            e for e in self.filter_events
            if start_date.isoformat() <= e['date'] <= end_date.isoformat()
        ]
        
        if not events_in_range:
            return {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days,
                'total_patterns': 0,
                'trades_allowed': 0,
                'trades_blocked': 0,
                'daily_summaries': []
            }
        
        # Generate daily summaries
        daily_summaries = []
        current_date = start_date
        while current_date <= end_date:
            summary = self.get_daily_filter_summary(current_date)
            if summary['total_patterns'] > 0:
                daily_summaries.append(summary)
            current_date += pd.Timedelta(days=1)
        
        # Aggregate statistics
        total_patterns = sum(d['total_patterns'] for d in daily_summaries)
        total_allowed = sum(d['trades_allowed'] for d in daily_summaries)
        total_blocked = sum(d['trades_blocked'] for d in daily_summaries)
        
        # Most common filter failures
        all_failures = {}
        for summary in daily_summaries:
            for filter_name, count in summary.get('filter_breakdown', {}).items():
                all_failures[filter_name] = all_failures.get(filter_name, 0) + count
        
        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days,
            'total_patterns': total_patterns,
            'trades_allowed': total_allowed,
            'trades_blocked': total_blocked,
            'block_rate': (total_blocked / total_patterns * 100) if total_patterns > 0 else 0.0,
            'most_common_failures': sorted(
                all_failures.items(),
                key=lambda x: x[1],
                reverse=True
            ),
            'daily_summaries': daily_summaries
        }
    
    def get_filter_effectiveness(self) -> Dict:
        """
        Calculate which filters are most effective at improving performance.
        Requires A/B test data.
        """
        if not self.config.AB_TEST_MODE:
            return {
                'error': 'A/B test mode required',
                'ab_test_mode': False
            }
        
        # Compare blocked trades to actual trades
        # This is a simplified analysis - in production, would be more sophisticated
        
        blocked_patterns = [
            e for e in self.filter_events
            if not e['trade_allowed']
        ]
        
        # Count which filters blocked the most
        filter_block_counts = {}
        for event in blocked_patterns:
            for failure in event['filters_failed']:
                filter_name = failure.split(':')[0].strip()
                filter_block_counts[filter_name] = filter_block_counts.get(filter_name, 0) + 1
        
        # In production, would correlate with actual trade outcomes
        # For now, return block counts
        return {
            'ab_test_mode': True,
            'total_blocks': len(blocked_patterns),
            'filter_block_counts': sorted(
                filter_block_counts.items(),
                key=lambda x: x[1],
                reverse=True
            ),
            'note': 'Full effectiveness analysis requires more historical data'
        }
    
    def clear_logs(self, before_date: date = None):
        """
        Clear logs before a certain date.
        
        Args:
            before_date: Clear logs before this date (defaults to all)
        """
        if before_date is None:
            self.filter_events = []
            self.simulated_trades = []
            self.actual_trades = []
        else:
            date_str = before_date.isoformat()
            self.filter_events = [e for e in self.filter_events if e['date'] >= date_str]
            self.simulated_trades = [t for t in self.simulated_trades if t['date'] >= date_str]
            self.actual_trades = [t for t in self.actual_trades if t['date'] >= date_str]
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """Export filter events to DataFrame for analysis."""
        if not self.filter_events:
            return pd.DataFrame()
        
        return pd.DataFrame(self.filter_events)
    
    def get_realtime_filter_status(self) -> Dict:
        """
        Get current filter status for live monitoring dashboard.
        Shows recent filter activity.
        """
        recent_events = self.filter_events[-10:] if self.filter_events else []
        
        # Get today's summary
        today_summary = self.get_daily_filter_summary()
        
        # Format recent events for display
        recent_formatted = []
        for event in recent_events:
            status = "✓" if event['trade_allowed'] else "✗"
            filters_info = (
                f"Passed: {len(event['filters_passed'])}, "
                f"Failed: {len(event['filters_failed'])}"
            )
            
            recent_formatted.append({
                'time': event['timestamp'].split('T')[1][:8],  # HH:MM:SS
                'ticker': event['ticker'],
                'status': status,
                'filters_info': filters_info,
                'trade_allowed': event['trade_allowed']
            })
        
        return {
            'today': today_summary,
            'recent_events': recent_formatted,
            'active_filters': self.config.get_active_filters()
        }


# Convenience function for integration
def create_filter_reporter(config: TradingConfig = None) -> FilterReporter:
    """Create a FilterReporter instance."""
    return FilterReporter(config)
