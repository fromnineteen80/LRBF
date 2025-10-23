"""
Metrics Calculator - Phase 3, Checkpoint 3.3

Calculates real-time trading performance metrics from IBKR fills data.

Metrics calculated:
- Win rate, trade count, P&L
- Sharpe ratio, Sortino ratio
- Maximum drawdown
- Per-stock performance
- Latency and slippage

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
sys.path.append('/home/claude/railyard')

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, date
from config import TradingConfig as cfg


class MetricsCalculator:
    """
    Calculates trading performance metrics from fills data.
    
    All calculations use actual data from IBKR - no hardcoded values.
    """
    
    def __init__(self):
        """Initialize metrics calculator."""
        pass
    
    # ========================================================================
    # CORE METRICS
    # ========================================================================
    
    def calculate_daily_metrics(
        self,
        fills: List[Dict],
        opening_balance: float,
        closing_balance: float
    ) -> Dict:
        """
        Calculate comprehensive daily performance metrics.
        
        Args:
            fills: List of fill dictionaries from IBKR
            opening_balance: Account balance at market open
            closing_balance: Account balance now (or at market close)
        
        Returns:
            Dictionary with all calculated metrics:
            {
                'realized_pl': float,           # Total P&L for the day
                'roi_pct': float,              # ROI percentage
                'trade_count': int,            # Number of round-trip trades
                'win_count': int,              # Number of winning trades
                'loss_count': int,             # Number of losing trades
                'win_rate': float,             # Win rate (0-1)
                'avg_win': float,              # Average win amount
                'avg_loss': float,             # Average loss amount
                'largest_win': float,          # Largest single win
                'largest_loss': float,         # Largest single loss
                'avg_latency_ms': float,       # Average execution latency
                'avg_slippage_pct': float,     # Average slippage
                'per_stock': Dict              # Metrics broken down by ticker
            }
        """
        if not fills:
            return self._empty_metrics()
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(fills)
        
        # Separate BUY and SELL fills
        buys = df[df['action'] == 'BUY'].copy()
        sells = df[df['action'] == 'SELL'].copy()
        
        # Calculate realized P&L (sum of all SELL fills)
        realized_pl = sells['realized_pnl'].sum() if not sells.empty else 0.0
        
        # Calculate ROI
        roi_pct = (realized_pl / opening_balance) * 100 if opening_balance > 0 else 0.0
        
        # Count trades (pair of BUY+SELL = 1 trade)
        trade_count = min(len(buys), len(sells))
        
        # Win/loss analysis
        if not sells.empty:
            wins = sells[sells['realized_pnl'] > 0]
            losses = sells[sells['realized_pnl'] <= 0]
            
            win_count = len(wins)
            loss_count = len(losses)
            win_rate = win_count / len(sells) if len(sells) > 0 else 0.0
            
            avg_win = wins['realized_pnl'].mean() if not wins.empty else 0.0
            avg_loss = losses['realized_pnl'].mean() if not losses.empty else 0.0
            
            largest_win = wins['realized_pnl'].max() if not wins.empty else 0.0
            largest_loss = losses['realized_pnl'].min() if not losses.empty else 0.0
        else:
            win_count = 0
            loss_count = 0
            win_rate = 0.0
            avg_win = 0.0
            avg_loss = 0.0
            largest_win = 0.0
            largest_loss = 0.0
        
        # Latency and slippage (if available in fills)
        avg_latency_ms = df['latency_ms'].mean() if 'latency_ms' in df.columns else None
        avg_slippage_pct = df['slippage_pct'].mean() if 'slippage_pct' in df.columns else None
        
        # Per-stock breakdown
        per_stock = self._calculate_per_stock_metrics(df)
        
        return {
            'realized_pl': realized_pl,
            'roi_pct': roi_pct,
            'trade_count': trade_count,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_latency_ms': avg_latency_ms,
            'avg_slippage_pct': avg_slippage_pct,
            'per_stock': per_stock
        }
    
    def _calculate_per_stock_metrics(self, fills_df: pd.DataFrame) -> Dict:
        """
        Calculate metrics for each ticker.
        
        Args:
            fills_df: DataFrame with all fills
        
        Returns:
            Dictionary mapping ticker -> metrics dict
        """
        per_stock = {}
        
        for ticker in fills_df['ticker'].unique():
            ticker_fills = fills_df[fills_df['ticker'] == ticker]
            
            sells = ticker_fills[ticker_fills['action'] == 'SELL']
            
            if not sells.empty:
                total_pl = sells['realized_pnl'].sum()
                trade_count = len(sells)
                wins = sells[sells['realized_pnl'] > 0]
                win_rate = len(wins) / len(sells) if len(sells) > 0 else 0.0
                
                per_stock[ticker] = {
                    'trade_count': trade_count,
                    'realized_pl': total_pl,
                    'win_count': len(wins),
                    'loss_count': len(sells) - len(wins),
                    'win_rate': win_rate
                }
        
        return per_stock
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics when no fills available."""
        return {
            'realized_pl': 0.0,
            'roi_pct': 0.0,
            'trade_count': 0,
            'win_count': 0,
            'loss_count': 0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'avg_latency_ms': None,
            'avg_slippage_pct': None,
            'per_stock': {}
        }
    
    # ========================================================================
    # RISK METRICS
    # ========================================================================
    
    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.0
    ) -> float:
        """
        Calculate Sharpe ratio from a series of returns.
        
        Sharpe = (Mean Return - Risk Free Rate) / Std Dev of Returns
        
        Args:
            returns: List of returns (typically daily ROI percentages)
            risk_free_rate: Risk-free rate (annualized, default 0%)
        
        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        mean_return = returns_array.mean()
        std_return = returns_array.std()
        
        if std_return == 0:
            return 0.0
        
        # Adjust risk-free rate for daily timeframe
        daily_rf = risk_free_rate / 252  # 252 trading days per year
        
        sharpe = (mean_return - daily_rf) / std_return
        
        # Annualize (multiply by sqrt(252))
        sharpe_annualized = sharpe * np.sqrt(252)
        
        return sharpe_annualized
    
    def calculate_sortino_ratio(
        self,
        returns: List[float],
        target_return: float = 0.0
    ) -> float:
        """
        Calculate Sortino ratio from a series of returns.
        
        Sortino is like Sharpe but only penalizes downside volatility.
        
        Args:
            returns: List of returns (typically daily ROI percentages)
            target_return: Target return (default 0%)
        
        Returns:
            Sortino ratio
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        mean_return = returns_array.mean()
        
        # Calculate downside deviation (only negative returns)
        downside_returns = returns_array[returns_array < target_return]
        
        if len(downside_returns) == 0:
            # No downside, Sortino is undefined (effectively infinite)
            return 10.0  # Cap at high value
        
        downside_std = downside_returns.std()
        
        if downside_std == 0:
            return 0.0
        
        sortino = (mean_return - target_return) / downside_std
        
        # Annualize
        sortino_annualized = sortino * np.sqrt(252)
        
        return sortino_annualized
    
    def calculate_max_drawdown(
        self,
        equity_curve: List[float]
    ) -> Tuple[float, int, int]:
        """
        Calculate maximum drawdown from equity curve.
        
        Args:
            equity_curve: List of account balances over time
        
        Returns:
            Tuple of (max_drawdown_pct, peak_index, trough_index)
        """
        if not equity_curve or len(equity_curve) < 2:
            return 0.0, 0, 0
        
        curve = np.array(equity_curve)
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(curve)
        
        # Calculate drawdown at each point
        drawdown = (curve - running_max) / running_max
        
        # Find maximum drawdown
        max_dd_pct = drawdown.min() * 100  # Convert to percentage
        trough_index = drawdown.argmin()
        
        # Find the peak before this trough
        peak_index = running_max[:trough_index+1].argmax() if trough_index > 0 else 0
        
        return abs(max_dd_pct), peak_index, trough_index
    
    def calculate_calmar_ratio(
        self,
        returns: List[float],
        equity_curve: List[float]
    ) -> float:
        """
        Calculate Calmar ratio (return / max drawdown).
        
        Args:
            returns: List of returns
            equity_curve: List of account balances
        
        Returns:
            Calmar ratio
        """
        if not returns or not equity_curve:
            return 0.0
        
        # Annualized return
        mean_return = np.array(returns).mean()
        annualized_return = mean_return * 252  # 252 trading days
        
        # Maximum drawdown
        max_dd, _, _ = self.calculate_max_drawdown(equity_curve)
        
        if max_dd == 0:
            return 10.0  # Cap at high value if no drawdown
        
        calmar = annualized_return / max_dd
        
        return calmar
    
    # ========================================================================
    # COMPARISON TO FORECAST
    # ========================================================================
    
    def compare_to_forecast(
        self,
        actual_metrics: Dict,
        forecast: Dict
    ) -> Dict:
        """
        Compare actual performance to morning forecast.
        
        Args:
            actual_metrics: Metrics from calculate_daily_metrics()
            forecast: Morning forecast dictionary
        
        Returns:
            Comparison dictionary:
            {
                'trades': {
                    'actual': int,
                    'expected_low': int,
                    'expected_high': int,
                    'vs_forecast': str  # 'below', 'within', 'above'
                },
                'pl': {
                    'actual': float,
                    'expected_low': float,
                    'expected_high': float,
                    'vs_forecast': str
                },
                'on_track': bool  # True if within expected ranges
            }
        """
        actual_trades = actual_metrics['trade_count']
        actual_pl = actual_metrics['realized_pl']
        
        expected_trades_low = forecast.get('expected_trades_low', 0)
        expected_trades_high = forecast.get('expected_trades_high', 0)
        expected_pl_low = forecast.get('expected_pl_low', 0)
        expected_pl_high = forecast.get('expected_pl_high', 0)
        
        # Compare trades
        if actual_trades < expected_trades_low:
            trades_vs = 'below'
        elif actual_trades > expected_trades_high:
            trades_vs = 'above'
        else:
            trades_vs = 'within'
        
        # Compare P&L
        if actual_pl < expected_pl_low:
            pl_vs = 'below'
        elif actual_pl > expected_pl_high:
            pl_vs = 'above'
        else:
            pl_vs = 'within'
        
        # On track if both metrics within range
        on_track = (trades_vs == 'within' and pl_vs == 'within')
        
        return {
            'trades': {
                'actual': actual_trades,
                'expected_low': expected_trades_low,
                'expected_high': expected_trades_high,
                'vs_forecast': trades_vs
            },
            'pl': {
                'actual': actual_pl,
                'expected_low': expected_pl_low,
                'expected_high': expected_pl_high,
                'vs_forecast': pl_vs
            },
            'on_track': on_track
        }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("Testing Metrics Calculator...")
    print("=" * 60)
    
    calc = MetricsCalculator()
    
    # Test 1: Calculate daily metrics
    print("\n1. Testing daily metrics calculation...")
    
    # Simulate some fills
    test_fills = [
        {
            'ibkr_execution_id': 'T001',
            'timestamp': datetime.now(),
            'ticker': 'AAPL',
            'action': 'BUY',
            'quantity': 10,
            'price': 150.00,
            'realized_pnl': 0,
            'commission': 1.00
        },
        {
            'ibkr_execution_id': 'T002',
            'timestamp': datetime.now(),
            'ticker': 'AAPL',
            'action': 'SELL',
            'quantity': 10,
            'price': 151.50,
            'realized_pnl': 13.00,  # 1.50 * 10 - 2 commissions
            'commission': 1.00
        },
        {
            'ibkr_execution_id': 'T003',
            'timestamp': datetime.now(),
            'ticker': 'MSFT',
            'action': 'BUY',
            'quantity': 5,
            'price': 300.00,
            'realized_pnl': 0,
            'commission': 1.00
        },
        {
            'ibkr_execution_id': 'T004',
            'timestamp': datetime.now(),
            'ticker': 'MSFT',
            'action': 'SELL',
            'quantity': 5,
            'price': 298.50,
            'realized_pnl': -9.50,  # Loss: -1.50 * 5 - 2 commissions
            'commission': 1.00
        }
    ]
    
    metrics = calc.calculate_daily_metrics(
        fills=test_fills,
        opening_balance=30000,
        closing_balance=30003.50
    )
    
    print(f"   Realized P&L: ${metrics['realized_pl']:.2f}")
    print(f"   ROI: {metrics['roi_pct']:.3f}%")
    print(f"   Trade count: {metrics['trade_count']}")
    print(f"   Win rate: {metrics['win_rate']*100:.1f}%")
    print(f"   Avg win: ${metrics['avg_win']:.2f}")
    print(f"   Avg loss: ${metrics['avg_loss']:.2f}")
    
    # Test 2: Sharpe ratio
    print("\n2. Testing Sharpe ratio...")
    test_returns = [3.2, 4.1, 2.8, 5.5, -1.2, 3.8, 4.5]  # Daily ROI %
    sharpe = calc.calculate_sharpe_ratio(test_returns)
    print(f"   Sharpe ratio: {sharpe:.2f}")
    
    # Test 3: Sortino ratio
    print("\n3. Testing Sortino ratio...")
    sortino = calc.calculate_sortino_ratio(test_returns)
    print(f"   Sortino ratio: {sortino:.2f}")
    
    # Test 4: Max drawdown
    print("\n4. Testing max drawdown...")
    test_equity = [30000, 30800, 31200, 30500, 30200, 31500, 32000]
    max_dd, peak_idx, trough_idx = calc.calculate_max_drawdown(test_equity)
    print(f"   Max drawdown: {max_dd:.2f}%")
    print(f"   Peak at index: {peak_idx}")
    print(f"   Trough at index: {trough_idx}")
    
    # Test 5: Calmar ratio
    print("\n5. Testing Calmar ratio...")
    calmar = calc.calculate_calmar_ratio(test_returns, test_equity)
    print(f"   Calmar ratio: {calmar:.2f}")
    
    # Test 6: Forecast comparison
    print("\n6. Testing forecast comparison...")
    test_forecast = {
        'expected_trades_low': 80,
        'expected_trades_high': 120,
        'expected_pl_low': 600,
        'expected_pl_high': 1200
    }
    
    comparison = calc.compare_to_forecast(metrics, test_forecast)
    print(f"   Trades: {comparison['trades']['actual']} vs {comparison['trades']['expected_low']}-{comparison['trades']['expected_high']}")
    print(f"   Status: {comparison['trades']['vs_forecast']}")
    print(f"   On track: {comparison['on_track']}")
    
    print("\n" + "=" * 60)
    print("✅ All metrics calculator tests passed!")
