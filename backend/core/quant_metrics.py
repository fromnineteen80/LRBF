"""
Professional Quant Metrics Calculator
Implements institutional-grade performance metrics for morning report

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from scipy import stats


class QuantMetricsCalculator:
    """
    Calculate professional quantitative metrics used by institutional desks.
    
    All metrics calculable from:
    - IBKR API (fills, account balance, returns)
    - Pattern detector (win rate, expected value)
    - Fills database (daily P&L history)
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize quant metrics calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate (default 5% = 0.05)
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days_per_year = 252
    
    # ========================================================================
    # CORE PERFORMANCE METRICS
    # ========================================================================
    
    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sharpe Ratio: Risk-adjusted return
        
        Formula: (Mean Return - Risk Free Rate) / Std Dev of Returns
        Target: > 2.0
        
        Args:
            returns: Series of daily returns
            periods_per_year: 252 for daily, 52 for weekly
            
        Returns:
            Sharpe ratio (annualized)
        """
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - (self.risk_free_rate / periods_per_year)
        
        if returns.std() == 0:
            return 0.0
        
        sharpe = np.sqrt(periods_per_year) * (excess_returns.mean() / returns.std())
        return float(sharpe)
    
    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sortino Ratio: Downside risk focus
        
        Formula: (Mean Return - Risk Free Rate) / Downside Deviation
        Target: > 2.5
        
        Only penalizes downside volatility (negative returns)
        
        Args:
            returns: Series of daily returns
            periods_per_year: 252 for daily
            
        Returns:
            Sortino ratio (annualized)
        """
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - (self.risk_free_rate / periods_per_year)
        
        # Calculate downside deviation (only negative returns)
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return float('inf') if excess_returns.mean() > 0 else 0.0
        
        downside_deviation = downside_returns.std()
        sortino = np.sqrt(periods_per_year) * (excess_returns.mean() / downside_deviation)
        
        return float(sortino)
    
    def calculate_calmar_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Calmar Ratio: Return vs max drawdown
        
        Formula: Annualized Return / Max Drawdown
        Target: > 2.0
        
        Args:
            returns: Series of daily returns
            periods_per_year: 252 for daily
            
        Returns:
            Calmar ratio
        """
        if len(returns) < 2:
            return 0.0
        
        annualized_return = returns.mean() * periods_per_year
        max_dd = self.calculate_max_drawdown(returns)
        
        if max_dd == 0:
            return float('inf') if annualized_return > 0 else 0.0
        
        calmar = annualized_return / abs(max_dd)
        return float(calmar)
    
    def calculate_omega_ratio(
        self,
        returns: pd.Series,
        threshold: float = 0.0
    ) -> float:
        """
        Calculate Omega Ratio: Probability-weighted gains vs losses
        
        Formula: Sum of gains above threshold / Sum of losses below threshold
        
        Args:
            returns: Series of daily returns
            threshold: Minimum acceptable return (default 0%)
            
        Returns:
            Omega ratio
        """
        if len(returns) < 2:
            return 0.0
        
        gains = returns[returns > threshold] - threshold
        losses = threshold - returns[returns < threshold]
        
        if losses.sum() == 0:
            return float('inf') if gains.sum() > 0 else 0.0
        
        omega = gains.sum() / losses.sum()
        return float(omega)
    
    # ========================================================================
    # RISK METRICS
    # ========================================================================
    
    def calculate_max_drawdown(self, returns: pd.Series) -> float:
        """
        Calculate Maximum Drawdown: Worst peak-to-trough decline
        
        Args:
            returns: Series of daily returns
            
        Returns:
            Max drawdown as percentage (negative value)
        """
        if len(returns) < 2:
            return 0.0
        
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        
        return float(drawdown.min())
    
    def calculate_recovery_factor(
        self,
        returns: pd.Series
    ) -> float:
        """
        Calculate Recovery Factor: Net profit / Max drawdown
        
        Measures how much profit was made relative to worst drawdown
        
        Args:
            returns: Series of daily returns
            
        Returns:
            Recovery factor
        """
        if len(returns) < 2:
            return 0.0
        
        net_profit = returns.sum()
        max_dd = abs(self.calculate_max_drawdown(returns))
        
        if max_dd == 0:
            return float('inf') if net_profit > 0 else 0.0
        
        recovery = net_profit / max_dd
        return float(recovery)
    
    def calculate_value_at_risk(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk (VaR): Maximum expected loss at confidence level
        
        Args:
            returns: Series of daily returns
            confidence: Confidence level (0.95 = 95%)
            
        Returns:
            VaR as percentage (negative value)
        """
        if len(returns) < 2:
            return 0.0
        
        var = returns.quantile(1 - confidence)
        return float(var)
    
    def calculate_conditional_var(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Conditional VaR (CVaR): Expected loss beyond VaR
        
        Also known as Expected Shortfall
        
        Args:
            returns: Series of daily returns
            confidence: Confidence level (0.95 = 95%)
            
        Returns:
            CVaR as percentage (negative value)
        """
        if len(returns) < 2:
            return 0.0
        
        var = self.calculate_value_at_risk(returns, confidence)
        cvar = returns[returns <= var].mean()
        
        return float(cvar)
    
    # ========================================================================
    # SIZING METRICS
    # ========================================================================
    
    def calculate_kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate Kelly Criterion: Optimal position size per trade
        
        Formula: (Win% × Avg Win - Loss% × Avg Loss) / Avg Win
        
        Args:
            win_rate: Win rate (0.0 to 1.0)
            avg_win: Average winning trade %
            avg_loss: Average losing trade % (positive)
            
        Returns:
            Optimal position size as fraction of capital
        """
        if avg_win == 0:
            return 0.0
        
        loss_rate = 1 - win_rate
        kelly = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
        
        # Cap at 100% (full kelly) and use half-kelly for safety
        kelly = max(0, min(kelly, 1.0)) / 2
        
        return float(kelly)
    
    def calculate_risk_of_ruin(
        self,
        win_rate: float,
        risk_per_trade: float = 0.01,
        max_losses: int = 20
    ) -> float:
        """
        Calculate Risk of Ruin: Probability of account wipeout
        
        Args:
            win_rate: Win rate (0.0 to 1.0)
            risk_per_trade: Risk per trade as fraction (default 1%)
            max_losses: Number of consecutive losses before ruin
            
        Returns:
            Probability of ruin (0.0 to 1.0)
        """
        loss_rate = 1 - win_rate
        
        if loss_rate == 0:
            return 0.0
        
        # Simplified risk of ruin formula
        ruin_prob = (loss_rate / win_rate) ** max_losses
        
        return float(min(ruin_prob, 1.0))
    
    def calculate_leverage_factor(
        self,
        account_balance: float,
        deployed_capital: float
    ) -> float:
        """
        Calculate Leverage Factor: Effective capital utilization
        
        Args:
            account_balance: Total account balance
            deployed_capital: Capital actively deployed
            
        Returns:
            Leverage factor (1.0 = no leverage, >1.0 = leveraged)
        """
        if account_balance == 0:
            return 0.0
        
        leverage = deployed_capital / account_balance
        return float(leverage)
    
    # ========================================================================
    # ALPHA METRICS
    # ========================================================================
    
    def calculate_alpha_vs_benchmark(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """
        Calculate Alpha vs Benchmark: Excess return above market
        
        Args:
            returns: Strategy returns
            benchmark_returns: Benchmark returns (e.g., SPY)
            
        Returns:
            Alpha (annualized)
        """
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0.0
        
        # Align series
        aligned_returns, aligned_benchmark = returns.align(
            benchmark_returns, join='inner'
        )
        
        if len(aligned_returns) < 2:
            return 0.0
        
        # Calculate beta first
        beta = self.calculate_beta(aligned_returns, aligned_benchmark)
        
        # Alpha = Strategy Return - (Risk Free + Beta × (Benchmark Return - Risk Free))
        strategy_return = aligned_returns.mean() * self.trading_days_per_year
        benchmark_return = aligned_benchmark.mean() * self.trading_days_per_year
        
        alpha = strategy_return - (self.risk_free_rate + beta * (benchmark_return - self.risk_free_rate))
        
        return float(alpha)
    
    def calculate_beta(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """
        Calculate Beta: Market correlation
        
        Target: < 0.3 for strategy independence
        
        Args:
            returns: Strategy returns
            benchmark_returns: Benchmark returns
            
        Returns:
            Beta coefficient
        """
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0.0
        
        # Align series
        aligned_returns, aligned_benchmark = returns.align(
            benchmark_returns, join='inner'
        )
        
        if len(aligned_returns) < 2:
            return 0.0
        
        covariance = aligned_returns.cov(aligned_benchmark)
        benchmark_variance = aligned_benchmark.var()
        
        if benchmark_variance == 0:
            return 0.0
        
        beta = covariance / benchmark_variance
        return float(beta)
    
    def calculate_information_ratio(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Information Ratio: Consistency of alpha generation
        
        Formula: Alpha / Tracking Error
        
        Args:
            returns: Strategy returns
            benchmark_returns: Benchmark returns
            periods_per_year: 252 for daily
            
        Returns:
            Information ratio (annualized)
        """
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0.0
        
        # Align series
        aligned_returns, aligned_benchmark = returns.align(
            benchmark_returns, join='inner'
        )
        
        if len(aligned_returns) < 2:
            return 0.0
        
        # Calculate excess returns
        excess_returns = aligned_returns - aligned_benchmark
        
        if excess_returns.std() == 0:
            return 0.0
        
        # Information Ratio = Mean Excess Return / Std Dev of Excess Returns
        ir = np.sqrt(periods_per_year) * (excess_returns.mean() / excess_returns.std())
        
        return float(ir)
    
    # ========================================================================
    # AGGREGATE CALCULATIONS
    # ========================================================================
    
    def calculate_all_metrics(
        self,
        returns: pd.Series,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        account_balance: float,
        deployed_capital: float,
        benchmark_returns: pd.Series = None
    ) -> Dict:
        """
        Calculate all professional quant metrics at once.
        
        Args:
            returns: Series of daily returns
            win_rate: Win rate (0.0 to 1.0)
            avg_win: Average win %
            avg_loss: Average loss % (positive)
            account_balance: Total account balance
            deployed_capital: Deployed capital
            benchmark_returns: Optional benchmark returns (e.g., SPY)
            
        Returns:
            Dict with all metrics organized by category
        """
        metrics = {
            'core_performance': {
                'sharpe_ratio': self.calculate_sharpe_ratio(returns),
                'sortino_ratio': self.calculate_sortino_ratio(returns),
                'calmar_ratio': self.calculate_calmar_ratio(returns),
                'omega_ratio': self.calculate_omega_ratio(returns)
            },
            'risk_metrics': {
                'max_drawdown_pct': self.calculate_max_drawdown(returns) * 100,
                'recovery_factor': self.calculate_recovery_factor(returns),
                'var_95': self.calculate_value_at_risk(returns) * 100,
                'cvar_95': self.calculate_conditional_var(returns) * 100
            },
            'sizing_metrics': {
                'kelly_criterion': self.calculate_kelly_criterion(win_rate, avg_win, avg_loss),
                'risk_of_ruin': self.calculate_risk_of_ruin(win_rate),
                'leverage_factor': self.calculate_leverage_factor(account_balance, deployed_capital)
            },
            'alpha_metrics': {}
        }
        
        # Add alpha metrics if benchmark provided
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            metrics['alpha_metrics'] = {
                'alpha_vs_spy': self.calculate_alpha_vs_benchmark(returns, benchmark_returns),
                'beta': self.calculate_beta(returns, benchmark_returns),
                'information_ratio': self.calculate_information_ratio(returns, benchmark_returns)
            }
        
        return metrics
    
    def calculate_per_stock_metrics(
        self,
        stock_data: pd.DataFrame,
        fills_history: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Calculate metrics per stock from fills history.
        
        Args:
            stock_data: DataFrame with selected stocks
            fills_history: List of fill records from database
            
        Returns:
            Dict of {ticker: metrics}
        """
        per_stock_metrics = {}
        
        # Group fills by ticker
        fills_by_ticker = {}
        for fill in fills_history:
            ticker = fill['ticker']
            if ticker not in fills_by_ticker:
                fills_by_ticker[ticker] = []
            fills_by_ticker[ticker].append(fill)
        
        # Calculate metrics per ticker
        for ticker in stock_data['ticker']:
            fills = fills_by_ticker.get(ticker, [])
            
            if not fills:
                per_stock_metrics[ticker] = self._empty_metrics()
                continue
            
            # Extract returns from fills
            returns = pd.Series([f['realized_pnl'] / f['price'] / f['quantity'] for f in fills])
            wins = returns[returns > 0]
            losses = returns[returns < 0]
            
            win_rate = len(wins) / len(returns) if len(returns) > 0 else 0
            avg_win = wins.mean() if len(wins) > 0 else 0
            avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
            
            per_stock_metrics[ticker] = {
                'sharpe_ratio': self.calculate_sharpe_ratio(returns),
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'total_trades': len(returns)
            }
        
        return per_stock_metrics
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics dict for stocks with no trades"""
        return {
            'sharpe_ratio': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'total_trades': 0
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_spy_returns(start_date: str, end_date: str) -> pd.Series:
    """
    Fetch SPY returns for alpha/beta calculations.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        Series of daily SPY returns
    """
    try:
        import yfinance as yf
        spy = yf.download('SPY', start=start_date, end=end_date, progress=False)
        returns = spy['Close'].pct_change().dropna()
        return returns
    except Exception as e:
        print(f"Warning: Could not fetch SPY data: {e}")
        return pd.Series()
