"""
EOD Reporter - Phase 4
Comprehensive end-of-day analysis with Capitalise.ai evaluation.

This module:
1. Compares forecast vs. actual results
2. Analyzes execution quality (pattern detection gaps)
3. Evaluates win rate performance
4. Provides decision tree recommendations

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
sys.path.append('/home/claude/railyard')

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import pandas as pd
import numpy as np

from backend.models.database import TradingDatabase
from config import TradingConfig as cfg


class EODAnalyzer:
    """
    Comprehensive end-of-day analysis engine.
    
    Evaluates trading performance and Capitalise.ai execution quality.
    """
    
    def __init__(self, db: TradingDatabase = None):
        """
        Initialize analyzer.
        
        Args:
            db: Optional database connection (creates new if None)
        """
        self.db = db if db else TradingDatabase()
        self._should_close_db = db is None
    
    def __del__(self):
        """Cleanup database connection if we created it."""
        if self._should_close_db and hasattr(self, 'db'):
            self.db.close()
    
    def generate_eod_report(
        self,
        target_date: date = None,
        opening_balance: float = None,
        closing_balance: float = None
    ) -> Dict:
        """
        Generate comprehensive end-of-day report.
        
        Args:
            target_date: Date to analyze (default: today)
            opening_balance: Account balance at open (from IBKR)
            closing_balance: Account balance at close (from IBKR)
        
        Returns:
            Dictionary with complete EOD analysis
        """
        
        if target_date is None:
            target_date = date.today()
        
        print(f"\n{'='*70}")
        print(f"  EOD REPORT GENERATOR - {target_date}")
        print(f"{'='*70}\n")
        
        # 1. Get morning forecast
        forecast = self.db.get_morning_forecast(target_date)
        if not forecast:
            return {
                'error': 'No morning forecast found',
                'date': target_date,
                'message': 'Cannot generate EOD report without morning forecast'
            }
        
        print(f"✅ Morning forecast loaded")
        
        # 2. Get actual fills
        fills = self.db.get_fills_by_date(target_date)
        print(f"✅ Loaded {len(fills)} fills from database")
        
        # 3. Build comprehensive report
        report = {
            'metadata': {
                'date': target_date.isoformat(),
                'generated_at': datetime.now().isoformat(),
                'opening_balance': opening_balance,
                'closing_balance': closing_balance
            },
            'forecast': self._extract_forecast_summary(forecast),
            'actual': self._calculate_actual_results(fills, opening_balance, closing_balance),
            'evaluation': self._evaluate_capitalise_performance(forecast, fills),
            'decision_tree': None,  # Will be calculated after evaluation
            'trends': self._calculate_trends(target_date),
            'events': self._get_notable_events(target_date)
        }
        
        # 4. Add decision tree recommendation
        report['decision_tree'] = self._generate_decision_tree(report['evaluation'])
        
        # 5. Store summary in database
        self._store_daily_summary(report)
        
        return report
    
    def _extract_forecast_summary(self, forecast: Dict) -> Dict:
        """
        Extract key metrics from morning forecast.
        
        Args:
            forecast: Morning forecast from database
        
        Returns:
            Summarized forecast metrics
        """
        
        return {
            'selected_stocks': forecast['selected_stocks'],
            'expected_trades_low': forecast['expected_trades_low'],
            'expected_trades_high': forecast['expected_trades_high'],
            'expected_trades_mid': (forecast['expected_trades_low'] + forecast['expected_trades_high']) / 2,
            'expected_pl_low': forecast['expected_pl_low'],
            'expected_pl_high': forecast['expected_pl_high'],
            'expected_pl_mid': (forecast['expected_pl_low'] + forecast['expected_pl_high']) / 2,
            'stock_analysis': forecast.get('stock_analysis', {}),
            'backtest_patterns_total': self._sum_backtest_patterns(forecast.get('stock_analysis', {})),
            'backtest_expected_win_rate': self._calculate_backtest_win_rate(forecast.get('stock_analysis', {}))
        }
    
    def _sum_backtest_patterns(self, stock_analysis: Dict) -> int:
        """Sum total patterns found in morning backtest across all stocks."""
        return sum(
            stock.get('patterns_total', 0) 
            for stock in stock_analysis.values()
        )
    
    def _calculate_backtest_win_rate(self, stock_analysis: Dict) -> float:
        """Calculate aggregate win rate from morning backtest."""
        total_wins = sum(stock.get('wins', 0) for stock in stock_analysis.values())
        total_losses = sum(stock.get('losses', 0) for stock in stock_analysis.values())
        total_trades = total_wins + total_losses
        
        if total_trades == 0:
            return 0.0
        
        return total_wins / total_trades
    
    def _calculate_actual_results(
        self,
        fills: List[Dict],
        opening_balance: float,
        closing_balance: float
    ) -> Dict:
        """
        Calculate actual trading results from fills.
        
        Args:
            fills: List of trade fills from database
            opening_balance: Starting balance
            closing_balance: Ending balance
        
        Returns:
            Actual performance metrics
        """
        
        if len(fills) == 0:
            return {
                'trade_count': 0,
                'realized_pl': 0.0,
                'roi_pct': 0.0,
                'win_count': 0,
                'loss_count': 0,
                'win_rate': 0.0,
                'per_stock': {}
            }
        
        # Calculate overall metrics
        total_realized_pl = sum(f['realized_pnl'] for f in fills)
        
        # Calculate ROI
        if opening_balance and opening_balance > 0:
            roi_pct = (total_realized_pl / opening_balance) * 100
        else:
            roi_pct = 0.0
        
        # Count wins/losses
        wins = sum(1 for f in fills if f['realized_pnl'] > 0)
        losses = sum(1 for f in fills if f['realized_pnl'] < 0)
        
        win_rate = wins / len(fills) if len(fills) > 0 else 0.0
        
        # Per-stock breakdown
        per_stock = self._calculate_per_stock_results(fills)
        
        return {
            'trade_count': len(fills),
            'realized_pl': total_realized_pl,
            'roi_pct': roi_pct,
            'win_count': wins,
            'loss_count': losses,
            'win_rate': win_rate,
            'per_stock': per_stock
        }
    
    def _calculate_per_stock_results(self, fills: List[Dict]) -> Dict:
        """
        Break down results by stock ticker.
        
        Args:
            fills: List of trade fills
        
        Returns:
            Dictionary keyed by ticker with performance metrics
        """
        
        per_stock = {}
        
        for fill in fills:
            ticker = fill['ticker']
            
            if ticker not in per_stock:
                per_stock[ticker] = {
                    'trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'realized_pl': 0.0
                }
            
            per_stock[ticker]['trades'] += 1
            per_stock[ticker]['realized_pl'] += fill['realized_pnl']
            
            if fill['realized_pnl'] > 0:
                per_stock[ticker]['wins'] += 1
            elif fill['realized_pnl'] < 0:
                per_stock[ticker]['losses'] += 1
        
        # Calculate win rates
        for ticker in per_stock:
            total = per_stock[ticker]['trades']
            wins = per_stock[ticker]['wins']
            per_stock[ticker]['win_rate'] = wins / total if total > 0 else 0.0
        
        return per_stock
    
    def _evaluate_capitalise_performance(
        self,
        forecast: Dict,
        fills: List[Dict]
    ) -> Dict:
        """
        Evaluate Capitalise.ai execution quality.
        
        This is the CRITICAL analysis that determines if we should
        build our own execution engine.
        
        Args:
            forecast: Morning forecast data
            fills: Actual trade fills
        
        Returns:
            Comprehensive execution quality evaluation
        """
        
        stock_analysis = forecast.get('stock_analysis', {})
        
        # Extract backtest metrics from stock_analysis
        # patterns_total = sum of all patterns found in 20-day backtest
        backtest_patterns_total = sum(
            stock.get('patterns_total', 0) 
            for stock in stock_analysis.values()
        )
        
        # expected_entries_per_day = sum of all expected confirmed entries per day
        backtest_entries_expected = sum(
            stock.get('expected_entries_per_day', 0) 
            for stock in stock_analysis.values()
        )
        
        # Calculate aggregate win rate from backtest
        total_wins = sum(stock.get('wins', 0) for stock in stock_analysis.values())
        total_losses = sum(stock.get('losses', 0) for stock in stock_analysis.values())
        total_backtest_trades = total_wins + total_losses
        backtest_win_rate = total_wins / total_backtest_trades if total_backtest_trades > 0 else 0.0
        
        # Calculate actual metrics
        actual_trades = len(fills)
        actual_wins = sum(1 for f in fills if f['realized_pnl'] > 0)
        actual_losses = sum(1 for f in fills if f['realized_pnl'] < 0)
        actual_win_rate = actual_wins / actual_trades if actual_trades > 0 else 0.0
        
        # Calculate execution gaps
        # Pattern detection: How many of the backtest patterns did Capitalise.ai detect?
        # We estimate this by comparing actual trades to expected daily entries
        if backtest_entries_expected > 0:
            # Capitalise.ai should execute about backtest_entries_expected trades per day
            detection_rate = (actual_trades / backtest_entries_expected)
            pattern_detection_gap_pct = max(0, (1 - detection_rate) * 100)
        else:
            detection_rate = 0
            pattern_detection_gap_pct = 100
        
        # Entry confirmation gap: negligible in our model (we assume confirmed = executed)
        entry_confirmation_gap_pct = 0  # Capitalise.ai executes all confirmed entries
        
        # Win rate delta
        win_rate_delta = actual_win_rate - backtest_win_rate
        
        # Determine primary bottleneck
        if pattern_detection_gap_pct > entry_confirmation_gap_pct:
            primary_bottleneck = "pattern_detection"
            bottleneck_severity = pattern_detection_gap_pct
        else:
            primary_bottleneck = "entry_confirmation"
            bottleneck_severity = entry_confirmation_gap_pct
        
        # Calculate trades_executed for waterfall display
        patterns_detected = int(backtest_entries_expected * detection_rate)
        
        return {
            'backtest': {
                'patterns_total': backtest_patterns_total,
                'patterns_found': backtest_patterns_total,  # Alias for compatibility
                'entries_expected': backtest_entries_expected,
                'win_rate': backtest_win_rate
            },
            'actual': {
                'patterns_detected': patterns_detected,
                'entries_executed': actual_trades,
                'trades_executed': actual_trades,
                'win_rate': actual_win_rate,
                'wins': actual_wins,
                'losses': actual_losses
            },
            'gaps': {
                'pattern_detection_pct': detection_rate * 100,
                'pattern_detection_gap_pct': pattern_detection_gap_pct,
                'entry_confirmation_pct': 100,
                'entry_confirmation_gap_pct': entry_confirmation_gap_pct,
                'win_rate_delta': win_rate_delta,
                'win_rate_delta_pct': win_rate_delta * 100
            },
            'bottleneck': {
                'primary': primary_bottleneck,
                'severity_pct': bottleneck_severity,
                'description': self._describe_bottleneck(primary_bottleneck, bottleneck_severity)
            }
        }
    
    def _describe_bottleneck(self, bottleneck: str, severity: float) -> str:
        """Generate human-readable bottleneck description."""
        
        if bottleneck == "pattern_detection":
            return f"Capitalise.ai is missing {severity:.0f}% of patterns that our backtest identified"
        else:
            return f"Pattern detection is good, but {severity:.0f}% of detected patterns fail to confirm entry"
    
    def _generate_decision_tree(self, evaluation: Dict) -> Dict:
        """
        Generate recommendation based on execution quality evaluation.
        
        Decision Tree Logic:
        - Gap < 10%: Continue with Capitalise.ai (excellent execution)
        - Gap 10-25%: Monitor closely, collect more data
        - Gap 25-40%: Consider building custom engine (medium priority)
        - Gap > 40%: High priority to build custom engine
        
        Args:
            evaluation: Execution quality evaluation
        
        Returns:
            Decision tree recommendation
        """
        
        gaps = evaluation['gaps']
        bottleneck = evaluation['bottleneck']
        
        # Calculate overall performance gap (worst of the two gaps)
        overall_gap = max(
            gaps['pattern_detection_gap_pct'],
            gaps['entry_confirmation_gap_pct']
        )
        
        # Determine severity category
        if overall_gap < 10:
            severity = "LOW"
            action = "continue_capitalise"
            justification = [
                "Execution quality is excellent",
                "Gap is within acceptable tolerance",
                "No immediate action needed"
            ]
            next_steps = [
                "Continue monitoring daily",
                "Maintain current configuration"
            ]
            
        elif overall_gap < 25:
            severity = "MEDIUM"
            action = "monitor_closely"
            justification = [
                "Some execution degradation detected",
                "Gap is noticeable but not critical",
                "Collect more data before major changes"
            ]
            next_steps = [
                "Track performance for 5 more trading days",
                "Analyze patterns to identify specific issues",
                "Consider parameter tuning"
            ]
            
        elif overall_gap < 40:
            severity = "MEDIUM-HIGH"
            action = "consider_custom_engine"
            justification = [
                f"{bottleneck['primary']} gap is significant ({bottleneck['severity_pct']:.0f}%)",
                "Win rate degradation suggests execution issues" if gaps['win_rate_delta'] < -0.05 else "Win rate is stable",
                "Custom engine could improve performance by 20-30%",
                "ROI on development time: Medium-High"
            ]
            next_steps = [
                "Continue with Capitalise.ai for 5 more days",
                "Collect more data to confirm bottleneck",
                "Begin parallel development of Railyard Executor",
                "Plan side-by-side comparison"
            ]
            
        else:  # gap >= 40%
            severity = "HIGH"
            action = "build_custom_engine"
            justification = [
                f"{bottleneck['primary']} gap is severe ({bottleneck['severity_pct']:.0f}%)",
                "Large performance degradation vs. backtest",
                "Custom engine could improve performance by 30-50%",
                "ROI on development time: Very High"
            ]
            next_steps = [
                "Prioritize development of Railyard Executor",
                "Continue Capitalise.ai only for data collection",
                "Plan migration timeline (2-4 weeks)",
                "Begin integration testing"
            ]
        
        return {
            'gap_size_pct': overall_gap,
            'severity': severity,
            'recommended_action': action,
            'justification': justification,
            'next_steps': next_steps,
            'estimated_improvement_pct': self._estimate_improvement(overall_gap),
            'development_priority': severity
        }
    
    def _estimate_improvement(self, gap: float) -> Tuple[float, float]:
        """
        Estimate potential improvement with custom engine.
        
        Args:
            gap: Overall execution gap percentage
        
        Returns:
            Tuple of (low_estimate, high_estimate) improvement percentages
        """
        
        # Conservative estimate: capture 50-70% of the gap
        low = gap * 0.50
        high = gap * 0.70
        
        return (low, high)
    
    def _calculate_trends(self, target_date: date) -> Dict:
        """
        Calculate performance trends.
        
        Args:
            target_date: Date to analyze
        
        Returns:
            Trend metrics (5-day, MTD, YTD)
        """
        
        # Get last 5 days of summaries
        last_5_days = self.db.get_recent_summaries(5)
        
        if len(last_5_days) == 0:
            return {
                'days_tracked': 0,
                'message': 'Not enough historical data for trend analysis'
            }
        
        # Calculate 5-day metrics
        total_pl_5d = sum(d['realized_pl'] for d in last_5_days)
        avg_roi_5d = np.mean([d['roi_pct'] for d in last_5_days])
        avg_win_rate_5d = np.mean([d['win_rate'] for d in last_5_days])
        
        return {
            'days_tracked': len(last_5_days),
            'last_5_days': {
                'total_pl': total_pl_5d,
                'avg_roi_pct': avg_roi_5d,
                'avg_win_rate': avg_win_rate_5d,
                'total_trades': sum(d['trade_count'] for d in last_5_days)
            }
        }
    
    def _get_notable_events(self, target_date: date) -> List[Dict]:
        """
        Get notable system events from the day.
        
        Args:
            target_date: Date to query
        
        Returns:
            List of notable events
        """
        
        events = self.db.get_events_by_date(target_date)
        
        # Filter to high severity events
        notable = [
            e for e in events 
            if e['severity'] in ['HIGH', 'CRITICAL']
        ]
        
        return notable
    
    def _store_daily_summary(self, report: Dict):
        """
        Store daily summary in database.
        
        Args:
            report: Complete EOD report
        """
        
        metadata = report['metadata']
        actual = report['actual']
        
        summary_data = {
            'date': metadata['date'],
            'opening_balance': metadata.get('opening_balance', 0.0),
            'closing_balance': metadata.get('closing_balance', 0.0),
            'realized_pl': actual['realized_pl'],
            'roi_pct': actual['roi_pct'],
            'trade_count': actual['trade_count'],
            'win_count': actual['win_count'],
            'loss_count': actual['loss_count'],
            'win_rate': actual['win_rate'],
            'stock_performance': actual['per_stock']
        }
        
        try:
            self.db.insert_daily_summary(summary_data)
            print(f"✅ Daily summary stored in database")
        except Exception as e:
            print(f"⚠️  Warning: Failed to store daily summary: {e}")


def generate_eod_report(
    target_date: date = None,
    opening_balance: float = None,
    closing_balance: float = None,
    output_path: str = None
) -> str:
    """
    Main entry point: Generate complete EOD report.
    
    Args:
        target_date: Date to analyze (default: today)
        opening_balance: Account balance at open (from IBKR)
        closing_balance: Account balance at close (from IBKR)
        output_path: Where to save HTML (default: auto-generate)
    
    Returns:
        Path to generated HTML report
    """
    
    if target_date is None:
        target_date = date.today()
    
    # Generate analysis
    analyzer = EODAnalyzer()
    report = analyzer.generate_eod_report(
        target_date=target_date,
        opening_balance=opening_balance,
        closing_balance=closing_balance
    )
    
    # Generate HTML
    from backend.reports.eod_html_generator import generate_eod_html
    
    if output_path is None:
        output_path = f"/home/claude/railyard/output/eod_report_{target_date.isoformat()}.html"
    
    html_path = generate_eod_html(report, output_path)
    
    print(f"\n{'='*70}")
    print(f"  ✅ EOD REPORT COMPLETE")
    print(f"{'='*70}")
    print(f"  Report: {html_path}")
    print(f"{'='*70}\n")
    
    return html_path


if __name__ == "__main__":
    """
    Test/demo mode.
    """
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate EOD Report')
    parser.add_argument('--date', type=str, help='Date (YYYY-MM-DD)', default=None)
    parser.add_argument('--opening', type=float, help='Opening balance', default=30000.0)
    parser.add_argument('--closing', type=float, help='Closing balance', default=31050.0)
    
    args = parser.parse_args()
    
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        target_date = date.today()
    
    generate_eod_report(
        target_date=target_date,
        opening_balance=args.opening,
        closing_balance=args.closing
    )
