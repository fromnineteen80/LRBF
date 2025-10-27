"""
Filter Preset Configurations for 6 Strategies

Each preset defines filter thresholds for the enhanced strategy.
Default strategy uses no filters.
"""

FILTER_PRESETS = {
    'default': {
        # No filters - baseline performance
        'use_filters': False,
        'vwap_proximity': None,
        'volume_multiplier': None,
        'time_filter': None,
        'sr_required': False,
        'trend_align': False,
        'description': 'Baseline performance with no filters',
        'expected_win_rate': 0.68,
        'expected_trades_per_day': (15, 25)
    },
    
    'conservative': {
        # All filters ON, tight thresholds
        'use_filters': True,
        'vwap_proximity': 0.02,      # ±2%
        'volume_multiplier': 2.0,     # 2x average
        'time_filter': 'avoid_edges', # Skip first/last hour
        'sr_required': True,          # Must be near S/R
        'trend_align': True,          # Must align with trend
        'min_confirmation': 0.40,     # 40%+ confirmation rate
        'description': 'Risk-averse with all filters, tight thresholds',
        'expected_win_rate': 0.81,
        'expected_trades_per_day': (8, 15)
    },
    
    'aggressive': {
        # Minimal filters, high frequency
        'use_filters': True,
        'vwap_proximity': 0.10,      # ±10% (loose)
        'volume_multiplier': 1.5,     # 1.5x average
        'time_filter': None,          # All hours
        'sr_required': False,
        'trend_align': False,
        'min_confirmation': 0.20,     # 20%+ confirmation rate
        'description': 'High frequency with minimal filtering',
        'expected_win_rate': 0.65,
        'expected_trades_per_day': (20, 30)
    },
    
    'choppy': {
        # Range-bound market focus
        'use_filters': True,
        'vwap_proximity': 0.03,      # ±3%
        'volume_multiplier': 2.5,     # High volume for support
        'time_filter': None,
        'sr_required': True,          # MUST be near S/R levels
        'trend_align': False,         # Neutral/range OK
        'range_bound': True,          # Prefer sideways
        'min_confirmation': 0.30,
        'description': 'Optimized for range-bound, choppy markets',
        'expected_win_rate': 0.75,
        'expected_trades_per_day': (10, 18)
    },
    
    'trending': {
        # Directional market focus
        'use_filters': True,
        'vwap_proximity': 0.05,      # ±5%
        'volume_multiplier': 1.5,
        'time_filter': 'favor_midday', # 10:30-2:30
        'sr_required': False,
        'trend_align': True,          # MUST align with trend
        'momentum_required': True,
        'min_confirmation': 0.30,
        'description': 'Optimized for trending, directional markets',
        'expected_win_rate': 0.72,
        'expected_trades_per_day': (12, 20)
    },
    
    'abtest': {
        # Experimental combinations
        'use_filters': True,
        'vwap_proximity': 0.04,      # ±4%
        'volume_multiplier': 1.8,
        'time_filter': 'custom',      # Test different hours
        'sr_required': True,
        'trend_align': True,
        'min_confirmation': 0.35,
        'experimental': True,          # Flag for testing
        'description': 'Experimental filter combinations for testing',
        'expected_win_rate': None,  # TBD
        'expected_trades_per_day': None  # TBD
    }
}

# VWAP Breakout strategy (separate from 3-step)
VWAP_BREAKOUT_CONFIG = {
    'strategy_type': 'vwap_breakout',
    'vwap_proximity_entry': 0.005,   # Enter within 0.5% of VWAP
    'volume_confirmation': 1.5,       # 1.5x volume on breakout
    'breakout_threshold': 0.005,      # 0.5% above VWAP to confirm
    'entry_threshold': 0.005,         # +0.5% from breakout
    'target_1': 0.0075,               # +0.75%
    'target_2': 0.0175,               # +1.75%
    'stop_loss': -0.005,              # -0.5%
    'description': 'VWAP crossover breakout strategy',
    'expected_win_rate': 0.82,
    'expected_trades_per_day': (8, 12)
}


def get_preset_config(preset_name: str) -> dict:
    """
    Get configuration for a specific preset.
    
    Args:
        preset_name: Name of preset ('default', 'conservative', etc.)
        
    Returns:
        Dictionary with preset configuration
        
    Raises:
        ValueError: If preset name not found
    """
    if preset_name not in FILTER_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(FILTER_PRESETS.keys())}")
    
    return FILTER_PRESETS[preset_name].copy()


def get_all_preset_names() -> list:
    """Get list of all available preset names."""
    return list(FILTER_PRESETS.keys())


def is_filter_preset(preset_name: str) -> bool:
    """Check if a preset uses filters (vs default which doesn't)."""
    config = get_preset_config(preset_name)
    return config.get('use_filters', False)
