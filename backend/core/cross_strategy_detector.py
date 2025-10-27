"""
Cross-Strategy Outlier Detection

Identifies stocks that are highly ranked in BOTH strategies:
- Selected strategy (e.g., 3-step geometric - default)
- Alternative strategy (e.g., VWAP breakout)

Philosophy:
- User selects primary strategy (gets top 8-20 stocks)
- System flags up to 2 stocks that are EXCEPTIONAL in the other strategy
- Gives user option to override for those 1-2 stocks only
- Threshold: Stock must be significantly better in alternative strategy

Author: The Luggage Room Boys Fund
Date: October 2025
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class CrossStrategyDetector:
    """
    Detects stocks that are outliers in both strategies.
    
    Example:
        User selects: 3-Step Geometric (default preset)
        System returns: Top 8 stocks for 3-step
        
        But system detects:
        - Stock #3 in 3-step is ALSO #1 in VWAP breakout
        - Stock #5 in 3-step is ALSO #2 in VWAP breakout
        
        System flags these 2 stocks as "cross-strategy outliers"
        User can choose to trade them with VWAP breakout instead
    """
    
    # Thresholds for outlier detection
    OUTLIER_THRESHOLDS = {
        'min_alternative_rank': 3,        # Must be top 3 in alternative strategy
        'min_composite_score_diff': 5.0,  # Must be 5+ points better in alternative
        'min_pattern_frequency_diff': 1.0, # Must have 1+ more patterns/day in alternative
        'max_outliers_per_day': 2         # Flag at most 2 stocks per day
    }
    
    def __init__(self, thresholds: Dict = None):
        """
        Initialize detector.
        
        Args:
            thresholds: Optional custom thresholds (overrides defaults)
        """
        self.thresholds = self.OUTLIER_THRESHOLDS.copy()
        if thresholds:
            self.thresholds.update(thresholds)
    
    def detect_outliers(
        self,
        selected_strategy: str,
        selected_preset: str,
        all_forecasts: Dict,
        num_stocks: int = 8
    ) -> List[Dict]:
        """
        Detect cross-strategy outliers in selected portfolio.
        
        Args:
            selected_strategy: User's chosen strategy ('3step' or 'vwap_breakout')
            selected_preset: User's chosen preset ('default', 'conservative', etc.)
            all_forecasts: All 7 forecasts from morning report
            num_stocks: Portfolio size (8, 12, 16, or 20)
        
        Returns:
            List of outlier stocks (max 2):
            [
                {
                    'ticker': 'AAPL',
                    'selected_rank': 3,           # Rank in selected strategy
                    'selected_score': 78.5,       # Composite score in selected strategy
                    'alternative_strategy': 'vwap_breakout',
                    'alternative_rank': 1,        # Rank in alternative strategy
                    'alternative_score': 85.2,    # Composite score in alternative strategy
                    'advantage': {
                        'score_diff': 6.7,        # How much better in alternative
                        'rank_diff': -2,          # Rank improvement (negative = better)
                        'pattern_freq_diff': 1.8  # More patterns/day in alternative
                    },
                    'recommendation': 'Consider trading AAPL with VWAP Breakout strategy instead'
                },
                ...
            ]
        """
        outliers = []
        
        # Get selected strategy stocks
        selected_key = self._get_forecast_key(selected_strategy, selected_preset)
        if selected_key not in all_forecasts:
            logger.error(f"Selected forecast not found: {selected_key}")
            return []
        
        selected_forecast = all_forecasts[selected_key]
        selected_stocks = selected_forecast['selected_stocks'][:num_stocks]
        
        # Get alternative strategy (the one NOT selected)
        alternative_strategy = 'vwap_breakout' if selected_strategy == '3step' else '3step'
        
        # For 3-step, we need to check ALL presets as alternatives
        if alternative_strategy == '3step':
            alternative_keys = [
                '3step_default', '3step_conservative', '3step_aggressive',
                '3step_choppy', '3step_trending', '3step_ab_test'
            ]
        else:
            alternative_keys = ['vwap_breakout']
        
        # Check each stock in selected portfolio
        for i, stock_data in enumerate(selected_stocks):
            ticker = stock_data['ticker']
            selected_rank = i + 1
            selected_score = stock_data.get('composite_score', 0)
            selected_freq = stock_data.get('pattern_frequency', 0)
            
            # Find this stock's rank in alternative strategy
            best_alternative = self._find_best_alternative_rank(
                ticker, alternative_keys, all_forecasts
            )
            
            if not best_alternative:
                continue  # Stock not in alternative strategy
            
            # Calculate advantage metrics
            score_diff = best_alternative['score'] - selected_score
            rank_diff = best_alternative['rank'] - selected_rank
            freq_diff = best_alternative['frequency'] - selected_freq
            
            # Check if meets outlier thresholds
            if self._is_outlier(best_alternative['rank'], score_diff, freq_diff):
                outlier = {
                    'ticker': ticker,
                    'selected_strategy': selected_strategy,
                    'selected_preset': selected_preset,
                    'selected_rank': selected_rank,
                    'selected_score': selected_score,
                    'alternative_strategy': best_alternative['strategy'],
                    'alternative_preset': best_alternative['preset'],
                    'alternative_rank': best_alternative['rank'],
                    'alternative_score': best_alternative['score'],
                    'advantage': {
                        'score_diff': round(score_diff, 2),
                        'rank_diff': rank_diff,
                        'pattern_freq_diff': round(freq_diff, 2)
                    },
                    'recommendation': self._generate_recommendation(
                        ticker, selected_strategy, best_alternative['strategy'],
                        selected_rank, best_alternative['rank']
                    )
                }
                outliers.append(outlier)
        
        # Sort by advantage (highest score diff first) and limit to max 2
        outliers.sort(key=lambda x: x['advantage']['score_diff'], reverse=True)
        outliers = outliers[:self.thresholds['max_outliers_per_day']]
        
        if outliers:
            logger.info(f"Detected {len(outliers)} cross-strategy outliers")
            for outlier in outliers:
                logger.info(
                    f"  {outlier['ticker']}: #{outlier['selected_rank']} in "
                    f"{outlier['selected_strategy']} but #{outlier['alternative_rank']} "
                    f"in {outlier['alternative_strategy']} "
                    f"(+{outlier['advantage']['score_diff']} score advantage)"
                )
        
        return outliers
    
    def _get_forecast_key(self, strategy: str, preset: str) -> str:
        """Convert strategy + preset to forecast key."""
        if strategy == 'vwap_breakout':
            return 'vwap_breakout'
        else:
            return f'3step_{preset}'
    
    def _find_best_alternative_rank(
        self, ticker: str, alternative_keys: List[str], all_forecasts: Dict
    ) -> Dict:
        """
        Find ticker's best rank across all alternative strategies.
        
        Returns:
            {
                'strategy': '3step' or 'vwap_breakout',
                'preset': 'default' or 'conservative' etc.,
                'rank': 1-500,
                'score': 0-100,
                'frequency': patterns per day
            }
        """
        best = None
        
        for key in alternative_keys:
            if key not in all_forecasts:
                continue
            
            forecast = all_forecasts[key]
            stocks = forecast.get('selected_stocks', [])
            
            # Find ticker in this forecast
            for i, stock_data in enumerate(stocks):
                if stock_data['ticker'] == ticker:
                    rank = i + 1
                    score = stock_data.get('composite_score', 0)
                    frequency = stock_data.get('pattern_frequency', 0)
                    
                    # Track best alternative rank
                    if best is None or rank < best['rank']:
                        strategy, preset = self._parse_forecast_key(key)
                        best = {
                            'strategy': strategy,
                            'preset': preset,
                            'rank': rank,
                            'score': score,
                            'frequency': frequency
                        }
        
        return best
    
    def _parse_forecast_key(self, key: str) -> Tuple[str, str]:
        """Parse forecast key into strategy and preset."""
        if key == 'vwap_breakout':
            return 'vwap_breakout', 'default'
        else:
            # '3step_default' -> ('3step', 'default')
            parts = key.split('_', 1)
            return parts[0], parts[1] if len(parts) > 1 else 'default'
    
    def _is_outlier(self, alt_rank: int, score_diff: float, freq_diff: float) -> bool:
        """
        Check if stock meets outlier thresholds.
        
        All conditions must be met:
        1. Ranked in top 3 in alternative strategy
        2. Score is 5+ points better in alternative
        3. Pattern frequency is 1+ more per day in alternative
        """
        return (
            alt_rank <= self.thresholds['min_alternative_rank'] and
            score_diff >= self.thresholds['min_composite_score_diff'] and
            freq_diff >= self.thresholds['min_pattern_frequency_diff']
        )
    
    def _generate_recommendation(
        self, ticker: str, selected_strategy: str, alt_strategy: str,
        selected_rank: int, alt_rank: int
    ) -> str:
        """Generate human-readable recommendation."""
        strategy_names = {
            '3step': '3-Step Geometric',
            'vwap_breakout': 'VWAP Breakout'
        }
        
        return (
            f"{ticker} is ranked #{selected_rank} in {strategy_names[selected_strategy]} "
            f"but #{alt_rank} in {strategy_names[alt_strategy]}. "
            f"Consider trading this stock with {strategy_names[alt_strategy]} strategy "
            f"to capitalize on stronger pattern quality."
        )


def add_outliers_to_forecast(
    selected_strategy: str,
    selected_preset: str,
    all_forecasts: Dict,
    num_stocks: int = 8
) -> Dict:
    """
    Add cross-strategy outliers to selected forecast.
    
    Called by morning report after generating all 7 forecasts.
    
    Args:
        selected_strategy: User's chosen strategy
        selected_preset: User's chosen preset
        all_forecasts: All 7 forecasts
        num_stocks: Portfolio size
    
    Returns:
        Updated forecast with 'cross_strategy_outliers' field added
    """
    detector = CrossStrategyDetector()
    outliers = detector.detect_outliers(
        selected_strategy, selected_preset, all_forecasts, num_stocks
    )
    
    # Add to selected forecast
    selected_key = detector._get_forecast_key(selected_strategy, selected_preset)
    if selected_key in all_forecasts:
        all_forecasts[selected_key]['cross_strategy_outliers'] = outliers
    
    return all_forecasts


if __name__ == "__main__":
    # Example usage
    print("Cross-Strategy Outlier Detection")
    print("=" * 60)
    print("\nThresholds:")
    detector = CrossStrategyDetector()
    for key, value in detector.thresholds.items():
        print(f"  {key}: {value}")
    
    print("\nExample Scenario:")
    print("  User selects: 3-Step Geometric (Default)")
    print("  Portfolio size: 8 stocks")
    print("\n  Stock rankings:")
    print("    AAPL: #3 in 3-Step (score 78), #1 in VWAP (score 86)")
    print("    MSFT: #5 in 3-Step (score 75), #2 in VWAP (score 82)")
    print("    GOOGL: #2 in 3-Step (score 80), #15 in VWAP (score 68)")
    print("\n  Result:")
    print("    ✅ AAPL flagged as outlier (score +8, rank +2)")
    print("    ✅ MSFT flagged as outlier (score +7, rank +3)")
    print("    ❌ GOOGL NOT flagged (worse in alternative)")
