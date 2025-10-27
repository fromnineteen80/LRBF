"""
Seven-Forecast Generator
Generates all 7 forecast scenarios in one morning report run:
- 3-Step Geometric: default, conservative, aggressive, choppy, trending, abtest
- VWAP Breakout: vwap_breakout
"""

import json
from typing import Dict, List
from config.config import TradingConfig
from config.filter_presets import FILTER_PRESETS, VWAP_BREAKOUT_CONFIG
from backend.core.filter_engine import FilterEngine
from backend.core.vwap_breakout_detector import analyze_vwap_breakout_patterns


class SevenForecastGenerator:
    """
    Generate 7 forecasts for morning report:
    
    3-Step Geometric Strategy (6 presets):
    1. default - No filters
    2. conservative - All filters, tight
    3. aggressive - Minimal filters
    4. choppy - S/R focused
    5. trending - Momentum focused
    6. abtest - Experimental
    
    VWAP Breakout Strategy:
    7. vwap_breakout - Crossover pattern
    """
    
    def __init__(self, config: TradingConfig):
        self.config = config
        
    def generate_all_forecasts(
        self, 
        pattern_results: Dict, 
        selected_stocks: List[str],
        market_data: Dict
    ) -> Dict[str, Dict]:
        """
        Generate all 7 forecasts.
        
        Args:
            pattern_results: Raw pattern detection results (unfiltered)
            selected_stocks: List of selected tickers
            market_data: Historical market data
            
        Returns:
            Dictionary with all forecasts:
            {
                'default': {...},
                'conservative': {...},
                'aggressive': {...},
                'choppy': {...},
                'trending': {...},
                'abtest': {...},
                'vwap_breakout': {...}
            }
        """
        all_forecasts = {}
        
        print("\n=== Generating Seven Forecasts ===")
        
        # Generate 3-Step presets (1-6)
        preset_names = ['default', 'conservative', 'aggressive', 'choppy', 'trending', 'abtest']
        
        for preset_name in preset_names:
            print(f"   {preset_name.upper()}: ", end="")
            
            forecast = self._generate_preset_forecast(
                pattern_results=pattern_results,
                selected_stocks=selected_stocks,
                market_data=market_data,
                preset_name=preset_name
            )
            
            all_forecasts[preset_name] = forecast
            print(f"{forecast['expected_daily_trades_low']}-{forecast['expected_daily_trades_high']} trades/day")
        
        # Generate VWAP Breakout (7)
        print(f"   VWAP_BREAKOUT: ", end="")
        vwap_forecast = self._generate_vwap_breakout_forecast(
            selected_stocks=selected_stocks,
            market_data=market_data
        )
        all_forecasts['vwap_breakout'] = vwap_forecast
        print(f"{vwap_forecast['expected_daily_trades_low']}-{vwap_forecast['expected_daily_trades_high']} trades/day")
        
        print("=== Seven Forecasts Complete ===\n")
        
        return all_forecasts
    
    def _generate_preset_forecast(
        self,
        pattern_results: Dict,
        selected_stocks: List[str],
        market_data: Dict,
        preset_name: str
    ) -> Dict:
        """
        Generate forecast for one 3-step preset.
        
        Returns:
            Forecast dict with:
            - expected_daily_trades_low/high
            - expected_pl_low/high
            - win_rate
            - filter_impact (if filtered)
            - per_stock_breakdown
        """
        # Get preset configuration
        preset_config = FILTER_PRESETS[preset_name]
        use_filters = preset_config['use_filters']
        
        # Initialize filter engine if needed
        filter_engine = None
        if use_filters:
            # Temporarily apply preset config to TradingConfig
            self._apply_preset_to_config(preset_name, preset_config)
            filter_engine = FilterEngine(self.config)
        
        # Calculate metrics per stock
        per_stock_metrics = {}
        total_raw_patterns = 0
        total_filtered_patterns = 0
        total_daily_entries = 0
        weighted_win_rate = 0
        total_expected_pl = 0
        
        for ticker in selected_stocks:
            stock_patterns = pattern_results.get(ticker, {})
            raw_patterns = stock_patterns.get('patterns', [])
            
            # Apply filters if enabled
            if use_filters and filter_engine and raw_patterns:
                filtered_patterns = []
                for pattern in raw_patterns:
                    if filter_engine.apply_filters(
                        ticker=ticker,
                        pattern=pattern,
                        market_data=market_data.get(ticker),
                        current_price=pattern.get('current_price', 0)
                    ):
                        filtered_patterns.append(pattern)
                
                patterns_used = filtered_patterns
            else:
                patterns_used = raw_patterns
            
            # Calculate metrics
            confirmation_rate = stock_patterns.get('confirmation_rate', 0)
            win_rate = stock_patterns.get('win_rate', 0)
            expected_value = stock_patterns.get('expected_value', 0)
            
            # Daily metrics
            daily_patterns = len(patterns_used) / self.config.ANALYSIS_PERIOD_DAYS
            daily_entries = daily_patterns * confirmation_rate
            daily_pl = daily_entries * expected_value * (self.config.DEPLOYMENT_RATIO * 10000 / len(selected_stocks))
            
            per_stock_metrics[ticker] = {
                'raw_patterns': len(raw_patterns),
                'filtered_patterns': len(patterns_used),
                'patterns_removed': len(raw_patterns) - len(patterns_used),
                'daily_entries': daily_entries,
                'win_rate': win_rate,
                'expected_value': expected_value,
                'daily_pl': daily_pl
            }
            
            # Aggregate
            total_raw_patterns += len(raw_patterns)
            total_filtered_patterns += len(patterns_used)
            total_daily_entries += daily_entries
            total_expected_pl += daily_pl
            
            # Weight win rate by entry frequency
            if daily_entries > 0:
                weighted_win_rate += win_rate * daily_entries
        
        # Calculate aggregate win rate
        if total_daily_entries > 0:
            aggregate_win_rate = weighted_win_rate / total_daily_entries
        else:
            aggregate_win_rate = 0.0
        
        # Build forecast
        forecast = {
            'preset_name': preset_name,
            'description': preset_config['description'],
            'use_filters': use_filters,
            'total_raw_patterns': total_raw_patterns,
            'total_filtered_patterns': total_filtered_patterns,
            'patterns_removed': total_raw_patterns - total_filtered_patterns,
            'filter_impact_pct': ((total_raw_patterns - total_filtered_patterns) / total_raw_patterns * 100) if total_raw_patterns > 0 else 0,
            'expected_daily_trades_low': int(total_daily_entries * 0.8),
            'expected_daily_trades_high': int(total_daily_entries * 1.2),
            'expected_pl_low': total_expected_pl * 0.8,
            'expected_pl_high': total_expected_pl * 1.2,
            'win_rate': aggregate_win_rate,
            'per_stock_metrics': per_stock_metrics
        }
        
        return forecast
    
    def _generate_vwap_breakout_forecast(
        self,
        selected_stocks: List[str],
        market_data: Dict
    ) -> Dict:
        """
        Generate forecast for VWAP Breakout strategy.
        Different pattern detection than 3-Step Geometric.
        """
        # Apply VWAP breakout config
        vwap_config = VWAP_BREAKOUT_CONFIG
        
        vwap_results = {}
        total_patterns = 0
        total_entries = 0
        weighted_win_rate = 0
        total_expected_pl = 0
        
        for ticker in selected_stocks:
            if ticker not in market_data:
                continue
            
            df = market_data[ticker]
            
            # Run VWAP breakout pattern detection
            result = analyze_vwap_breakout_patterns(ticker, df, self.config)
            
            vwap_results[ticker] = result
            
            # Aggregate metrics
            patterns = result.get('total_patterns', 0)
            entries = result.get('confirmed_entries', 0)
            win_rate = result.get('win_rate', 0)
            daily_pl = result.get('expected_daily_pl', 0)
            
            total_patterns += patterns
            total_entries += entries
            total_expected_pl += daily_pl
            
            if entries > 0:
                weighted_win_rate += win_rate * entries
        
        # Calculate aggregate win rate
        if total_entries > 0:
            aggregate_win_rate = weighted_win_rate / total_entries
        else:
            aggregate_win_rate = 0.0
        
        forecast = {
            'strategy': 'vwap_breakout',
            'description': vwap_config['description'],
            'total_patterns': total_patterns,
            'total_entries': total_entries,
            'expected_daily_trades_low': int(total_entries * 0.8),
            'expected_daily_trades_high': int(total_entries * 1.2),
            'expected_pl_low': total_expected_pl * 0.8,
            'expected_pl_high': total_expected_pl * 1.2,
            'win_rate': aggregate_win_rate,
            'stock_results': vwap_results
        }
        
        return forecast
    
    def _apply_preset_to_config(self, preset_name: str, preset_config: dict):
        """
        Temporarily apply preset configuration to TradingConfig.
        Used when filter engine needs specific thresholds.
        """
        # Map filter_presets.py keys to TradingConfig attributes
        if 'vwap_proximity' in preset_config and preset_config['vwap_proximity']:
            self.config.VWAP_PROXIMITY_MAX_PCT = preset_config['vwap_proximity']
        
        if 'volume_multiplier' in preset_config and preset_config['volume_multiplier']:
            self.config.VOLUME_CONFIRMATION_MULTIPLIER = preset_config['volume_multiplier']
        
        if 'min_confirmation' in preset_config:
            self.config.MIN_CONFIRMATION_RATE = preset_config['min_confirmation']
        
        # Boolean flags
        self.config.QUALITY_FILTERS_ON = preset_config.get('use_filters', False)
        self.config.SR_REQUIRED = preset_config.get('sr_required', False)
        self.config.TREND_ALIGN_REQUIRED = preset_config.get('trend_align', False)
