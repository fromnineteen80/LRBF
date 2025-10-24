"""
Stock Selector V2 - 24-Stock Ranking with Deployment Selector

Ranks top 24 stocks using 16-category composite scoring.
User selects deployment level: 8, 12, 16, or 20 stocks.
Next 4 stocks after selection become automatic reserve.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from backend.core.category_scorer import CategoryScorer


class StockSelector:
    """
    24-stock ranking system with flexible deployment options.
    """
    
    DEPLOYMENT_OPTIONS = [8, 12, 16, 20]
    
    def __init__(self):
        """Initialize stock selector with category scorer."""
        self.scorer = CategoryScorer()
    
    def rank_stocks(
        self,
        stock_data_list: List[Dict],
        top_n: int = 24
    ) -> List[Dict]:
        """
        Rank stocks by 16-category composite score.
        
        Args:
            stock_data_list: List of analyzed stock dictionaries
            top_n: Number of top stocks to return (default 24)
        
        Returns:
            List of ranked stocks with scores
        """
        return self.scorer.rank_stocks(stock_data_list, top_n=top_n)
    
    def select_deployment(
        self,
        ranked_stocks: List[Dict],
        num_stocks: int = 8
    ) -> Dict:
        """
        Select stocks for deployment based on user choice.
        
        Args:
            ranked_stocks: List of 24 ranked stocks
            num_stocks: Deployment level (8, 12, 16, or 20)
        
        Returns:
            Dictionary with:
            {
                'deployed': List of stocks to trade,
                'reserve': List of next 4 stocks,
                'not_deployed': Remaining stocks (13-24),
                'deployment_level': int,
                'position_size_pct': float (per stock)
            }
        """
        if num_stocks not in self.DEPLOYMENT_OPTIONS:
            raise ValueError(f"num_stocks must be one of {self.DEPLOYMENT_OPTIONS}")
        
        if len(ranked_stocks) < num_stocks + 4:
            raise ValueError(f"Need at least {num_stocks + 4} ranked stocks")
        
        # Split stocks
        deployed = ranked_stocks[:num_stocks]
        reserve = ranked_stocks[num_stocks:num_stocks + 4]
        not_deployed = ranked_stocks[num_stocks + 4:]
        
        # Calculate position size (80% deployed capital / num_stocks)
        position_size_pct = (0.80 / num_stocks) * 100
        
        return {
            'deployed': deployed,
            'reserve': reserve,
            'not_deployed': not_deployed,
            'deployment_level': num_stocks,
            'position_size_pct': position_size_pct,
            'reserve_start_rank': num_stocks + 1,
            'reserve_end_rank': num_stocks + 4
        }
    
    def get_deployment_forecasts(
        self,
        ranked_stocks: List[Dict],
        account_balance: float,
        all_levels: bool = True
    ) -> Dict[int, Dict]:
        """
        Generate forecasts for all deployment levels (or specific level).
        
        Args:
            ranked_stocks: List of 24 ranked stocks
            account_balance: Current account balance
            all_levels: If True, return forecasts for all 4 levels
        
        Returns:
            Dictionary mapping deployment_level -> forecast
            {
                8: {
                    'deployed_capital': float,
                    'position_size': float,
                    'expected_trades_low': int,
                    'expected_trades_high': int,
                    'expected_pl_low': float,
                    'expected_pl_high': float,
                    'expected_roi_low': float,
                    'expected_roi_high': float,
                    'risk_metrics': {...}
                },
                12: {...},
                16: {...},
                20: {...}
            }
        """
        forecasts = {}
        deployed_capital = account_balance * 0.80
        
        for num_stocks in self.DEPLOYMENT_OPTIONS:
            selection = self.select_deployment(ranked_stocks, num_stocks)
            deployed = selection['deployed']
            position_size = deployed_capital / num_stocks
            
            # Aggregate expected performance from stocks
            total_patterns_low = sum(s.get('expected_daily_patterns', 0) * 0.8 for s in deployed)
            total_patterns_high = sum(s.get('expected_daily_patterns', 0) * 1.2 for s in deployed)
            
            total_entries_low = sum(s.get('entries_per_day', 0) * 0.8 for s in deployed)
            total_entries_high = sum(s.get('entries_per_day', 0) * 1.2 for s in deployed)
            
            # Calculate expected P&L from EV * entries
            avg_ev = np.mean([s.get('expected_value_pct', 0) for s in deployed])
            expected_pl_low = (total_entries_low * (avg_ev / 100) * position_size) * 0.9
            expected_pl_high = (total_entries_high * (avg_ev / 100) * position_size) * 1.1
            
            # ROI
            roi_low = (expected_pl_low / deployed_capital) * 100
            roi_high = (expected_pl_high / deployed_capital) * 100
            
            # Risk metrics (aggregate from stocks)
            avg_win_rate = np.mean([s.get('win_rate', 0) for s in deployed])
            max_dd = max([abs(s.get('max_drawdown_intraday', 0)) for s in deployed])
            avg_sharpe = np.mean([s.get('sharpe_ratio', 0) for s in deployed if s.get('sharpe_ratio')])
            
            # Dead zone time estimate
            avg_dz_freq = np.mean([s.get('dead_zone_frequency', 0) for s in deployed])
            
            forecasts[num_stocks] = {
                'deployed_capital': deployed_capital,
                'position_size': position_size,
                'expected_patterns_low': int(total_patterns_low),
                'expected_patterns_high': int(total_patterns_high),
                'expected_trades_low': int(total_entries_low),
                'expected_trades_high': int(total_entries_high),
                'expected_pl_low': expected_pl_low,
                'expected_pl_high': expected_pl_high,
                'expected_roi_low': roi_low,
                'expected_roi_high': roi_high,
                'risk_metrics': {
                    'avg_win_rate': avg_win_rate,
                    'max_drawdown': max_dd,
                    'sharpe_ratio': avg_sharpe,
                    'time_in_dead_zones_pct': avg_dz_freq
                }
            }
        
        return forecasts if all_levels else forecasts[self.DEPLOYMENT_OPTIONS[0]]
    
    def categorize_by_risk(self, ranked_stocks: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize stocks by risk profile based on composite scores.
        
        Args:
            ranked_stocks: List of ranked stocks
        
        Returns:
            Dictionary with Conservative, Medium, Aggressive lists
        """
        categorized = {
            'Conservative': [],
            'Medium': [],
            'Aggressive': []
        }
        
        for stock in ranked_stocks:
            composite = stock['composite_score']
            volatility = stock.get('atr_pct', 2.0)
            entries_per_day = stock.get('entries_per_day', 3.0)
            
            # Conservative: High composite score (>88), low volatility, moderate activity
            if composite >= 88 and volatility < 2.5 and entries_per_day < 4:
                categorized['Conservative'].append(stock)
            
            # Aggressive: Moderate score (75-88), higher volatility or high activity
            elif composite >= 75 and (volatility >= 3.0 or entries_per_day >= 5):
                categorized['Aggressive'].append(stock)
            
            # Medium: Everything else
            else:
                categorized['Medium'].append(stock)
        
        return categorized
    
    def format_stock_display(
        self,
        stock: Dict,
        rank: int,
        category: str = None
    ) -> Dict:
        """
        Format stock data for frontend display.
        
        Args:
            stock: Stock dictionary with scores
            rank: Stock rank (1-24)
            category: Risk category (Conservative/Medium/Aggressive)
        
        Returns:
            Formatted dictionary for UI
        """
        return {
            'rank': rank,
            'ticker': stock['ticker'],
            'name': stock.get('name', stock['ticker']),
            'category': category or stock.get('category', 'Medium'),
            'composite_score': round(stock['composite_score'], 1),
            
            # Profitability
            'expected_value_pct': stock.get('expected_value_pct', 0),
            'pattern_frequency': stock.get('expected_daily_patterns', 0),
            'dead_zone_score': stock['category_scores'].get('dead_zone', 0),
            
            # Execution
            'liquidity': stock.get('avg_volume_20d', 0) / 1_000_000,
            'atr_pct': stock.get('atr_pct', 0),
            'avg_hold_time_min': stock.get('avg_hold_time_minutes', 0),
            
            # Risk
            'win_rate': stock.get('win_rate', 0),
            'max_drawdown': abs(stock.get('max_drawdown_intraday', 0)),
            'days_to_earnings': stock.get('days_to_earnings', 100),
            
            # Expected today
            'expected_patterns_today': round(stock.get('expected_daily_patterns', 0)),
            'expected_entries_today': round(stock.get('entries_per_day', 0)),
            
            # All category scores
            'category_scores': stock.get('category_scores', {})
        }


def select_stocks_for_deployment(
    analyzed_stocks: List[Dict],
    account_balance: float,
    deployment_level: int = 8
) -> Dict:
    """
    Convenience function: Analyze, rank, select in one call.
    
    Args:
        analyzed_stocks: List of analyzed stock data
        account_balance: Current account balance
        deployment_level: Number of stocks to deploy (8, 12, 16, or 20)
    
    Returns:
        Complete selection package with forecasts
    """
    selector = StockSelector()
    
    # Rank top 24
    ranked = selector.rank_stocks(analyzed_stocks, top_n=24)
    
    # Select deployment
    selection = selector.select_deployment(ranked, num_stocks=deployment_level)
    
    # Generate forecasts for all levels
    forecasts = selector.get_deployment_forecasts(ranked, account_balance)
    
    # Categorize by risk
    categorized = selector.categorize_by_risk(ranked)
    
    return {
        'ranked_stocks': ranked,
        'selection': selection,
        'forecasts': forecasts,
        'categorized': categorized,
        'account_balance': account_balance,
        'deployed_capital': account_balance * 0.80,
        'reserve_capital': account_balance * 0.20
    }
