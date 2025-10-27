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
    # Pattern Detection
    DECLINE_THRESHOLD = 1.0      # % decline from recent high (Step 1)
    RECOVERY_THRESHOLD = 0.5     # Fraction of decline to recover (Step 2)
    RETRACEMENT_THRESHOLD = 0.5  # Fraction of recovery to retrace (Step 3)
    ENTRY_THRESHOLD = 0.5        # % climb from pattern low to trigger entry (Step 4)
    
    # Exit Targets
    TARGET_1 = 0.75              # First profit target (+0.75%)
    TARGET_2 = 1.75              # Final profit target (+1.75%)
    
    # Decision Points (not exits)
    CROSS_THRESHOLD = 1.00       # Intermediate floor if crossed (+1.00%)
    MOMENTUM_CONFIRMATION = 1.25 # Momentum confirmation to continue to T2 (+1.25%)
    
    # Risk Controls
    STOP_LOSS = -0.5             # Stop loss if immediate crash
    
    # Tiered Dead Zone Timeouts (seconds)
    DEAD_ZONE_TIMEOUT_BELOW_T1 = 180   # 3 minutes - no profit locked
    DEAD_ZONE_TIMEOUT_AT_T1 = 240      # 4 minutes - T1 locked (+0.75%)
    DEAD_ZONE_TIMEOUT_AT_CROSS = 240   # 4 minutes - CROSS locked (+1.00%)
    DEAD_ZONE_TIMEOUT_MOMENTUM = 360   # 6 minutes - momentum confirmed
    DEAD_ZONE_RANGE = 0.6              # % range to detect stall (±0.6%)
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
        'default': {
            # Strategy 1 baseline - NO FILTERS
            # Pure 3-step geometric pattern
            'ALL_ENHANCEMENTS_ON': False,
            'QUALITY_FILTERS_ON': False,
            'TIMING_FILTERS_ON': False,
            'CONFLUENCE_FILTERS_ON': False
        },
        'vwap_breakout': {
            # Strategy 2 - VWAP crossover required
            # Different pattern detection entirely
            'STRATEGY_TYPE': 'vwap_breakout',
            'VWAP_CROSSOVER_REQUIRED': True,
            'VWAP_PROXIMITY_MAX_PCT': 1.0,  # Must be within 1% of VWAP
            'VOLUME_CONFIRMATION_ENABLED': True,
            'VOLUME_CONFIRMATION_MULTIPLIER': 1.5,
            'STABILIZATION_REQUIRED': True  # Must stabilize near VWAP first
        },
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


class IBKRConfig:
    """IBKR-specific configuration."""
    
    # === Connection ===
    GATEWAY_URL = "https://localhost:8000"  # IBKR Client Portal Gateway
    ACCOUNT_ID = None  # Set via .env (IBKR_ACCOUNT_ID)
    PAPER_TRADING = True  # Paper trading mode
    TIMEOUT = 30  # Request timeout (seconds)
    
    # === Real-Time Data ===
    REALTIME_UPDATE_INTERVAL_MS = 100  # 100ms updates (intraminute)
    WEBSOCKET_ENABLED = False  # Toggle WebSocket streaming (future)
    MARKET_DATA_FIELDS = ['31', '84', '86']  # Last, Bid, Ask
    
    # === Historical Data ===
    HISTORICAL_BARS_PERIOD = "20d"  # 20 days lookback
    HISTORICAL_BARS_BAR_SIZE = "1min"  # 1-minute bars
    HISTORICAL_BARS_WHAT_TO_SHOW = "TRADES"  # Price data type
    
    # === Rate Limits ===
    API_RATE_LIMIT_DELAY = 0.5  # Seconds between API calls
    MAX_CONCURRENT_SYMBOLS = 20  # Max symbols for market data
    
    @classmethod
    def load_from_env(cls):
        """Load IBKR configuration from environment variables."""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        cls.ACCOUNT_ID = os.getenv('IBKR_ACCOUNT_ID')
        cls.GATEWAY_URL = os.getenv('IBKR_GATEWAY_URL', cls.GATEWAY_URL)
        cls.PAPER_TRADING = os.getenv('IBKR_PAPER_TRADING', 'True').lower() == 'true'
        
        if not cls.ACCOUNT_ID:
            raise ValueError("IBKR_ACCOUNT_ID not found in .env file")



# ═══════════════════════════════════════════════════════════════
# ADAPTIVE DEAD ZONES CONFIGURATION
# ═══════════════════════════════════════════════════════════════

class AdaptiveDeadZoneConfig:
    """Configuration for adaptive dead zone timeouts based on time-of-day analysis."""
    
    # === Feature Toggle ===
    ENABLED = True  # Enable adaptive dead zones
    
    # === Base Timeouts (minutes) ===
    # These are starting points - actual timeouts calculated per stock + time window
    BASE_TIMEOUT_ENTRY = 8.0       # After entry, waiting for price movement
    BASE_TIMEOUT_TARGET_1 = 5.6    # After hitting T1 (70% of base)
    BASE_TIMEOUT_TARGET_2 = 4.0    # After hitting T2 (50% of base)
    
    # === Timeout Bounds (minutes) ===
    MIN_TIMEOUT = 3.0   # Minimum allowed timeout
    MAX_TIMEOUT = 15.0  # Maximum allowed timeout
    
    # === Pattern Strength Multipliers ===
    # Strong patterns get more time, weak patterns get less
    PATTERN_STRENGTH_MIN = 0.5   # Weakest multiplier
    PATTERN_STRENGTH_MAX = 1.5   # Strongest multiplier
    
    # === Time-of-Day Analysis ===
    MIN_PATTERNS_PER_WINDOW = 5  # Minimum patterns to consider window viable
    LOOKBACK_DAYS = 20           # Days of history to analyze
    
    # === Dead Zone Detection ===
    DEAD_ZONE_RANGE_PCT = 0.6    # ±0.6% range for dead zone
    DEAD_ZONE_TIMEOUT_MINUTES = 8.0  # Default if no time profile available


# ═══════════════════════════════════════════════════════════════
# NEWS MONITORING CONFIGURATION
# ═══════════════════════════════════════════════════════════════

class NewsMonitoringConfig:
    """Configuration for 3-tier news monitoring system."""
    
    # === Feature Toggle ===
    ENABLED = True  # Enable news monitoring
    
    # === Pre-Market Screening (Tier 1: Auto-Exclude) ===
    EXCLUDE_ON_EARNINGS = True        # Auto-exclude earnings day
    EXCLUDE_ON_FDA_DECISION = True    # Auto-exclude FDA decision day
    EXCLUDE_ON_EARNINGS_TOMORROW = False  # Exclude day before earnings
    
    # === Real-Time Monitoring (During Trading) ===
    CHECK_INTERVAL_SECONDS = 60       # Check news every 60 seconds
    
    # === Volume Spike Detection ===
    VOLUME_SPIKE_THRESHOLD = 3.0      # 3x normal volume = spike
    VOLUME_SPIKE_ACTION = "EXIT_IMMEDIATELY"
    
    # === Price Gap Detection ===
    PRICE_GAP_THRESHOLD_PCT = 2.0     # 2% move in 1 minute
    PRICE_GAP_ACTION = "EXIT_IMMEDIATELY"
    
    # === Trading Halt Detection ===
    CHECK_HALTS = True
    HALT_ACTION = "HALT_TRADING"      # Pause all trading in halted stock
    
    # === Elevated Risk Adjustments (Tier 2) ===
    # When news presents elevated (but not extreme) risk
    ELEVATED_RISK_DEAD_ZONE_MULT = 0.5     # Reduce dead zone timeout by 50%
    ELEVATED_RISK_POSITION_SIZE_MULT = 0.5  # Reduce position size by 50%
    
    # === News API Configuration ===
    EARNINGS_CALENDAR_PROVIDER = "earnings_whispers"  # or "nasdaq", "finviz"
    ECONOMIC_CALENDAR_PROVIDER = "trading_economics"  # or "forexfactory"
    BREAKING_NEWS_PROVIDER = "newsapi"               # or "benzinga", "alphavantage"
    
    # === Analyst Changes ===
    TRACK_ANALYST_CHANGES = True
    ANALYST_LOOKBACK_HOURS = 24       # Check last 24 hours of analyst activity


# ═══════════════════════════════════════════════════════════════
# TIME-OF-DAY CONFIGURATION
# ═══════════════════════════════════════════════════════════════

class TimeOfDayConfig:
    """Configuration for time-of-day performance analysis."""
    
    # === Time Windows (Eastern Time) ===
    MARKET_OPEN_START = "09:31"
    MARKET_OPEN_END = "10:00"
    
    MID_MORNING_START = "10:00"
    MID_MORNING_END = "11:30"
    
    LUNCH_START = "11:30"
    LUNCH_END = "13:30"
    
    AFTERNOON_START = "13:30"
    AFTERNOON_END = "15:30"
    
    MARKET_CLOSE_START = "15:30"
    MARKET_CLOSE_END = "16:00"
    
    # === Position Sizing by Time ===
    ADJUST_POSITION_SIZE_BY_TIME = True
    
    # Position size multipliers per window quality
    EXCELLENT_WINDOW_MULTIPLIER = 1.5  # High win rate, low dead zones
    AVERAGE_WINDOW_MULTIPLIER = 1.0    # Moderate performance
    POOR_WINDOW_MULTIPLIER = 0.5       # Low win rate, high dead zones
    
    # Quality thresholds
    EXCELLENT_QUALITY_THRESHOLD = 0.6  # win_rate * (1 - dead_zone_rate)
    POOR_QUALITY_THRESHOLD = 0.4


