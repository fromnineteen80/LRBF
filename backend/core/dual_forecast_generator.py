"""
Dual-Forecast System Implementation
Generates forecasts for ALL preset configurations in one morning report run.
"""

import json
from typing import Dict, List
from config.config import TradingConfig
from backend.core.filter_engine import FilterEngine
from backend.core.vwap_breakout_detector import analyze_vwap_breakout_patterns

class DualForecastGenerator:
    """
    Generates multiple forecasts using different filter presets.
    Run pattern detection ONCE, apply different filters to same patterns.
    """
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.presets = list(TradingConfig.PRESETS.keys())
        
    def generate_all_forecasts(
        self, 
        pattern_results: Dict, 
        selected_stocks: List[str],
        market_data: Dict
    ) -> Dict[str, Dict]:
        """
        Generate forecasts for ALL presets.
        
        Args:
            pattern_results: Raw pattern detection results (unfiltered)
            selected_stocks: List of selected tickers
            market_data: Historical market data
            
        Returns:
            Dict with forecasts for each preset:
            {
                'default': {...forecast...},
                'conservative': {...forecast...},
                'aggressive': {...forecast...},
                'choppy_market': {...forecast...},
                'trending_market': {...forecast...},
                'ab_test': {...forecast...}
            }
        """
        all_forecasts = {}
        
        # 1. DEFAULT FORECAST (no filters)
        print("   Generating DEFAULT forecast (no filters)...")
        all_forecasts['default'] = self._generate_preset_forecast(
            pattern_results, 
            selected_stocks, 
            market_data,
            preset_name='default',
            use_filters=False
        )
        
        # 2. PRESET FORECASTS (with filters)
        for preset_name in self.presets:
            print(f"   Generating {preset_name.upper()} forecast...")
            all_forecasts[preset_name] = self._generate_preset_forecast(
                pattern_results,
                selected_stocks,
                market_data,
                preset_name=preset_name,
                use_filters=True
            )
        
        # 3. VWAP BREAKOUT FORECAST (Strategy 2)
        print("   Generating VWAP BREAKOUT forecast (Strategy 2)...")
        all_forecasts['vwap_breakout'] = self._generate_vwap_forecast(
            selected_stocks,
            market_data
        )
        
        return all_forecasts
    
    def _generate_vwap_forecast(
        self,
        selected_stocks: List[str],
        market_data: Dict
    ) -> Dict:
        """
        Generate forecast for VWAP Breakout strategy.
        Different pattern detection than 3-Step Geometric.
        """
        vwap_results = {}
        
        for ticker in selected_stocks:
            if ticker not in market_data:
                continue
            
            df = market_data[ticker]
            
            # Run VWAP breakout pattern detection
            result = analyze_vwap_breakout_patterns(ticker, df, self.config)
            vwap_results[ticker] = result
        
        # Calculate aggregate forecast
        total_patterns = sum(r['total_patterns'] for r in vwap_results.values())
        total_entries = sum(r['confirmed_entries'] for r in vwap_results.values())
        
        if total_entries > 0:
            avg_win_rate = sum(
                r['win_rate'] * r['confirmed_entries'] 
                for r in vwap_results.values()
            ) / total_entries
            
            expected_pl = sum(r['expected_daily_pl'] for r in vwap_results.values())
        else:
            avg_win_rate = 0.0
            expected_pl = 0.0
        
        return {
            'strategy': 'vwap_breakout',
            'total_patterns': total_patterns,
            'total_entries': total_entries,
            'win_rate': avg_win_rate,
            'expected_daily_trades_low': int(total_entries * 0.8),
            'expected_daily_trades_high': int(total_entries * 1.2),
            'expected_pl_low': expected_pl * 0.8,
            'expected_pl_high': expected_pl * 1.2,
            'stock_results': vwap_results
        }
    
    def _generate_preset_forecast(
        self,
        pattern_results: Dict,
        selected_stocks: List[str],
        market_data: Dict,
        preset_name: str,
        use_filters: bool
    ) -> Dict:
        """
        Generate forecast for a specific preset.
        
        Returns:
            Forecast dict with:
            - expected_trades (low/high)
            - expected_pl (low/high)
            - win_rate
            - filter_impact (patterns filtered out)
            - per_stock_breakdown
        """
        # Load preset configuration
        if preset_name != 'default':
            original_config = self._save_current_config()
            TradingConfig.load_preset(preset_name)
        
        try:
            # Initialize filter engine
            filter_engine = FilterEngine(TradingConfig) if use_filters else None
            
            # Calculate filtered patterns per stock
            per_stock_metrics = {}
            total_patterns = 0
            total_filtered = 0
            
            for ticker in selected_stocks:
                stock_patterns = pattern_results.get(ticker, {})
                raw_patterns = stock_patterns.get('patterns', [])
                
                if use_filters and filter_engine:
                    # Apply filters
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
                    filtered_count = len(raw_patterns) - len(filtered_patterns)
                else:
                    patterns_used = raw_patterns
                    filtered_count = 0
                
                # Calculate metrics for this stock
                confirmation_rate = stock_patterns.get('confirmation_rate', 0)
                win_rate = stock_patterns.get('win_rate', 0)
                expected_value = stock_patterns.get('expected_value', 0)
                
                # Adjust for filtered patterns
                daily_patterns = len(patterns_used) / self.config.ANALYSIS_PERIOD_DAYS
                daily_entries = daily_patterns * confirmation_rate
                
                per_stock_metrics[ticker] = {
                    'raw_patterns': len(raw_patterns),
                    'filtered_patterns': len(patterns_used),
                    'patterns_removed': filtered_count,
                    'daily_entries': daily_entries,
                    'win_rate': win_rate,
                    'expected_value': expected_value
                }
                
                total_patterns += len(patterns_used)
                total_filtered += filtered_count
            
            # Aggregate forecast
            total_daily_entries = sum(m['daily_entries'] for m in per_stock_metrics.values())
            avg_win_rate = sum(m['win_rate'] for m in per_stock_metrics.values()) / len(per_stock_metrics)
            
            # Calculate P&L range
            position_size = (self.config.DEPLOYMENT_RATIO / self.config.NUM_STOCKS)
            avg_win = (self.config.TARGET_1 + self.config.TARGET_2) / 2
            avg_loss = abs(self.config.STOP_LOSS)
            
            expected_pl_per_trade = (avg_win_rate * avg_win) - ((1 - avg_win_rate) * avg_loss)
            expected_pl_low = total_daily_entries * 0.8 * expected_pl_per_trade * position_size
            expected_pl_high = total_daily_entries * 1.2 * expected_pl_per_trade * position_size
            
            return {
                'preset': preset_name,
                'filters_applied': use_filters,
                'active_filters': TradingConfig.get_active_filters() if use_filters else [],
                'expected_trades': {
                    'low': int(total_daily_entries * 0.8),
                    'high': int(total_daily_entries * 1.2),
                    'mean': total_daily_entries
                },
                'expected_pl': {
                    'low': expected_pl_low,
                    'high': expected_pl_high,
                    'mean': (expected_pl_low + expected_pl_high) / 2
                },
                'win_rate': avg_win_rate,
                'filter_impact': {
                    'total_patterns': total_patterns,
                    'patterns_filtered': total_filtered,
                    'filter_rate': (total_filtered / (total_patterns + total_filtered) * 100) if (total_patterns + total_filtered) > 0 else 0
                },
                'per_stock': per_stock_metrics
            }
            
        finally:
            # Restore original config
            if preset_name != 'default':
                self._restore_config(original_config)
    
    def _save_current_config(self) -> Dict:
        """Save current config state."""
        return {
            'ALL_ENHANCEMENTS_ON': TradingConfig.ALL_ENHANCEMENTS_ON,
            'QUALITY_FILTERS_ON': TradingConfig.QUALITY_FILTERS_ON,
            'TIMING_FILTERS_ON': TradingConfig.TIMING_FILTERS_ON,
            'CONFLUENCE_FILTERS_ON': TradingConfig.CONFLUENCE_FILTERS_ON,
            'VWAP_PROXIMITY_ENABLED': TradingConfig.VWAP_PROXIMITY_ENABLED,
            'VOLUME_CONFIRMATION_ENABLED': TradingConfig.VOLUME_CONFIRMATION_ENABLED,
            'TIME_FILTER_ENABLED': TradingConfig.TIME_FILTER_ENABLED,
            'SUPPORT_RESISTANCE_ENABLED': TradingConfig.SUPPORT_RESISTANCE_ENABLED,
            'TREND_ALIGNMENT_ENABLED': TradingConfig.TREND_ALIGNMENT_ENABLED
        }
    
    def _restore_config(self, saved_config: Dict):
        """Restore config state."""
        for key, value in saved_config.items():
            setattr(TradingConfig, key, value)


# Database schema update needed
DATABASE_MIGRATION = """
-- Add preset forecasts column to morning_forecasts table
ALTER TABLE morning_forecasts ADD COLUMN preset_forecasts_json TEXT;
ALTER TABLE morning_forecasts ADD COLUMN active_preset TEXT DEFAULT 'default';

-- Structure of preset_forecasts_json:
-- {
--   "default": { ...forecast... },
--   "conservative": { ...forecast... },
--   "aggressive": { ...forecast... },
--   "choppy_market": { ...forecast... },
--   "trending_market": { ...forecast... }
-- }
"""
