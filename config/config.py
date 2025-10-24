"""
Trading Configuration
Single source of truth for all trading parameters
"""

class TradingConfig:
    """User-configurable trading parameters."""
    
    # === Capital Management ===
    DEPLOYMENT_RATIO = 0.80  # 80% of account deployed
    RESERVE_RATIO = 0.20     # 20% held in reserve
    NUM_STOCKS = 8           # Number of stocks to trade (8 or 16)
    
    # === Entry & Exit Rules ===
    DECLINE_THRESHOLD = 1.0      # % decline to start pattern (Step 1)
    ENTRY_THRESHOLD = 1.5        # % climb to confirm entry (test 1.5 or 2.0)
    TARGET_1 = 0.75             # % profit target 1
    TARGET_2 = 2.0              # % profit target 2
    STOP_LOSS = -0.5            # % stop loss
    
    # === Risk Limits ===
    DAILY_LOSS_LIMIT = -1.5     # % max daily loss before shutdown
    
    # === Pattern Detection ===
    ANALYSIS_PERIOD_DAYS = 20   # Historical days to analyze
    BAR_INTERVAL = "1m"         # Price bar interval
    
    # === Quality Filters ===
    MIN_CONFIRMATION_RATE = 0.25  # 25% minimum
    MIN_EXPECTED_VALUE = 0.0      # Must be profitable
    MIN_ENTRIES_PER_DAY = 3.0     # Minimum activity
    
    # === Execution ===
    COOLDOWN_MINUTES = 1        # Wait after closing position
    MARKET_OPEN = "09:31"       # Eastern Time
    MARKET_CLOSE = "16:00"      # Eastern Time
    ENTRY_CUTOFF = "15:50"      # Stop new entries
    
    # === Stock Selection ===
    NUM_CONSERVATIVE = 2        # For 8-stock portfolio
    NUM_MEDIUM = 4
    NUM_AGGRESSIVE = 2
    
    # === Backup Stocks ===
    NUM_BACKUP = 4              # Backup stocks (N+4 feature)
    
    # =========================================
    # === STRATEGY ENHANCEMENT TOGGLES ===
    # =========================================
    
    # === Master Toggle ===
    ALL_ENHANCEMENTS_ON = False  # Quick toggle for all filters (default OFF per user)
    
    # === Category Toggles ===
    QUALITY_FILTERS_ON = False    # VWAP proximity + volume confirmation
    TIMING_FILTERS_ON = False     # Time-of-day + market conditions
    CONFLUENCE_FILTERS_ON = False # Support/resistance + trend alignment
    
    # === Quality Filters ===
    VWAP_PROXIMITY_ENABLED = False
    VWAP_PROXIMITY_MAX_PCT = 3.0  # Options: 2.0, 3.0, 5.0, 10.0
    VOLUME_CONFIRMATION_ENABLED = False
    VOLUME_CONFIRMATION_MULTIPLIER = 2.0  # Options: 1.5, 2.0, 2.5, 3.0
    
    # === Timing Filters ===
    TIME_FILTER_ENABLED = False
    TIME_FILTER_WINDOWS = ['full_day']  # Options: 'first_hour', 'last_hour', 'full_day', 'custom'
    CUSTOM_TIME_START = "09:31"
    CUSTOM_TIME_END = "16:00"
    MACRO_EVENT_FILTER_ENABLED = False  # Skip FOMC/NFP days
    
    # === Confluence Filters ===
    SUPPORT_RESISTANCE_ENABLED = False
    SUPPORT_RESISTANCE_TOLERANCE_PCT = 1.0  # Options: 0.5, 1.0, 2.0
    TREND_ALIGNMENT_ENABLED = False
    TREND_ALIGNMENT_TYPE = 'any'  # Options: 'uptrend', 'any', 'downtrend'
    
    # === Performance Tracking ===
    TRACK_FILTER_IMPACT = False  # Log all filtered trades
    AB_TEST_MODE = False  # Track parallel performance with/without filters
    
    # === Expert Level Toggles (User Question 6) ===
    RECOVERY_PCT = 50.0  # % of decline that must be recovered (default 50%)
    RETRACEMENT_PCT = 50.0  # % of recovery that retraces (default 50%)
    
    # === Preset Configurations ===
    PRESETS = {
        'conservative': {
            'ALL_ENHANCEMENTS_ON': True,
            'QUALITY_FILTERS_ON': True,
            'TIMING_FILTERS_ON': True,
            'CONFLUENCE_FILTERS_ON': True,
            'VWAP_PROXIMITY_MAX_PCT': 3.0,
            'VOLUME_CONFIRMATION_MULTIPLIER': 2.0,
            'TIME_FILTER_WINDOWS': ['first_hour', 'last_hour'],
            'TREND_ALIGNMENT_TYPE': 'uptrend'
        },
        'aggressive': {
            'ALL_ENHANCEMENTS_ON': False
        },
        'choppy_market': {
            'QUALITY_FILTERS_ON': True,
            'TIMING_FILTERS_ON': True,
            'VWAP_PROXIMITY_MAX_PCT': 2.0,
            'VOLUME_CONFIRMATION_MULTIPLIER': 2.5,
            'TIME_FILTER_WINDOWS': ['first_hour']
        },
        'trending_market': {
            'CONFLUENCE_FILTERS_ON': True,
            'TREND_ALIGNMENT_TYPE': 'uptrend',
            'SUPPORT_RESISTANCE_ENABLED': False,
            'TIME_FILTER_WINDOWS': ['full_day']
        },
        'ab_test': {
            'AB_TEST_MODE': True,
            'TRACK_FILTER_IMPACT': True
        }
    }
    
    @classmethod
    def get_portfolio_counts(cls):
        """Get portfolio stock counts as a dictionary."""
        return {
            'conservative': cls.NUM_CONSERVATIVE,
            'medium': cls.NUM_MEDIUM,
            'aggressive': cls.NUM_AGGRESSIVE
        }
    
    @classmethod
    def load_preset(cls, preset_name):
        """Load a preset configuration."""
        if preset_name not in cls.PRESETS:
            raise ValueError(f"Unknown preset: {preset_name}")
        
        preset = cls.PRESETS[preset_name]
        for key, value in preset.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
    
    @classmethod
    def get_active_filters(cls):
        """Return a list of currently active filters."""
        active = []
        
        if cls.ALL_ENHANCEMENTS_ON or cls.QUALITY_FILTERS_ON:
            if cls.VWAP_PROXIMITY_ENABLED:
                active.append(f"VWAP ({cls.VWAP_PROXIMITY_MAX_PCT}%)")
            if cls.VOLUME_CONFIRMATION_ENABLED:
                active.append(f"Volume ({cls.VOLUME_CONFIRMATION_MULTIPLIER}x)")
        
        if cls.ALL_ENHANCEMENTS_ON or cls.TIMING_FILTERS_ON:
            if cls.TIME_FILTER_ENABLED:
                windows = ', '.join(cls.TIME_FILTER_WINDOWS)
                active.append(f"Time ({windows})")
            if cls.MACRO_EVENT_FILTER_ENABLED:
                active.append("Macro Events")
        
        if cls.ALL_ENHANCEMENTS_ON or cls.CONFLUENCE_FILTERS_ON:
            if cls.SUPPORT_RESISTANCE_ENABLED:
                active.append(f"S/R ({cls.SUPPORT_RESISTANCE_TOLERANCE_PCT}%)")
            if cls.TREND_ALIGNMENT_ENABLED:
                active.append(f"Trend ({cls.TREND_ALIGNMENT_TYPE})")
        
        return active if active else ["None"]
    
    @classmethod
    def get_filter_status(cls):
        """Return a dictionary with filter status."""
        return {
            'master': cls.ALL_ENHANCEMENTS_ON,
            'quality': cls.QUALITY_FILTERS_ON,
            'timing': cls.TIMING_FILTERS_ON,
            'confluence': cls.CONFLUENCE_FILTERS_ON,
            'tracking': cls.TRACK_FILTER_IMPACT,
            'ab_test': cls.AB_TEST_MODE,
            'active_filters': cls.get_active_filters()
        }
    
    # === API Configuration ===
    # Note: API keys should be in environment variables, not here
    RAPIDAPI_ENABLED = False    # Set to True when ready for production
    YFINANCE_DELAY = 15         # Minutes delay for free tier
    
    # === Forecast Settings ===
    FORECAST_CONFIDENCE = 0.85      # Confidence level for forecast ranges (0-1)
    
    # === Simulation Settings ===
    SIMULATION_MODE = True      # Use mock data for testing
    SIMULATION_SEED = 42        # Random seed for reproducible tests


# Convenience function to get config as dict
def get_config_dict():
    """Return all config values as a dictionary."""
    return {
        key: value for key, value in vars(TradingConfig).items()
        if not key.startswith('_') and not callable(value)
    }


# Convenience function to print current config
def print_config():
    """Print current configuration."""
    print("=" * 60)
    print("TRADING CONFIGURATION")
    print("=" * 60)
    
    config = get_config_dict()
    
    sections = {
        'Capital Management': ['DEPLOYMENT_RATIO', 'RESERVE_RATIO', 'NUM_STOCKS'],
        'Entry & Exit Rules': ['DECLINE_THRESHOLD', 'ENTRY_THRESHOLD', 'TARGET_1', 'TARGET_2', 'STOP_LOSS'],
        'Risk Limits': ['DAILY_LOSS_LIMIT'],
        'Pattern Detection': ['ANALYSIS_PERIOD_DAYS', 'BAR_INTERVAL'],
        'Quality Filters': ['MIN_CONFIRMATION_RATE', 'MIN_EXPECTED_VALUE', 'MIN_ENTRIES_PER_DAY'],
        'Execution': ['COOLDOWN_MINUTES', 'MARKET_OPEN', 'MARKET_CLOSE', 'ENTRY_CUTOFF'],
        'Stock Selection': ['NUM_CONSERVATIVE', 'NUM_MEDIUM', 'NUM_AGGRESSIVE', 'NUM_BACKUP'],
        'Strategy Enhancements': ['ALL_ENHANCEMENTS_ON', 'QUALITY_FILTERS_ON', 'TIMING_FILTERS_ON', 'CONFLUENCE_FILTERS_ON']
    }
    
    for section, keys in sections.items():
        print(f"\n{section}:")
        for key in keys:
            if key in config:
                print(f"  {key:35} = {config[key]}")
    
    # Show active filters
    print(f"\nActive Filters: {', '.join(TradingConfig.get_active_filters())}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    print_config()
