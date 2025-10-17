"""
Trading Configuration
Central configuration file for all trading parameters.

Author: The Luggage Room Boys Fund
Date: October 2025
"""


class TradingConfig:
    """
    User-configurable trading parameters.
    
    All hardcoded values should be moved here. Modules import from this
    single source of truth.
    """

    # === RAPIDAPI YAHOO FINANCE ===
    RAPIDAPI_KEY = "97b31186b2msh4a897ce25410ffbp119fa8jsnd8661cc1bab0"
    RAPIDAPI_HOST = "yahoo-finance166.p.rapidapi.com"
    RAPIDAPI_REGION = "US"  # Market region for data requests

    
    # ========================================================================
    # CAPITAL MANAGEMENT
    # ========================================================================
    
    DEPLOYMENT_RATIO = 0.80      # 80% of account deployed in trades
    RESERVE_RATIO = 0.20         # 20% held in reserve
    NUM_STOCKS = 8               # Number of stocks to trade simultaneously
    
    # Position sizing
    # When NUM_STOCKS = 8:  each position is 10% of deployed capital
    # When NUM_STOCKS = 16: each position is 5% of deployed capital
    
    # ========================================================================
    # PATTERN DETECTION
    # ========================================================================
    
    DECLINE_THRESHOLD = 1.0      # % decline to start pattern (Step 1)
    RECOVERY_PCT = 50.0          # % recovery of decline (Step 2) - typically 50%
    RETRACEMENT_PCT = 50.0       # % retracement of recovery (Step 3) - typically 50%
    
    # ========================================================================
    # ENTRY & EXIT RULES
    # ========================================================================
    
    ENTRY_THRESHOLD = 1.5        # % climb from last low to confirm entry
                                 # Test values: 1.5% or 2.0%
    
    TARGET_1 = 0.75             # % profit target 1 (first exit level)
    TARGET_2 = 2.0              # % profit target 2 (maximum profit)
    STOP_LOSS = -0.5            # % stop loss (maximum loss per trade)
    
    # ========================================================================
    # RISK LIMITS
    # ========================================================================
    
    DAILY_LOSS_LIMIT = -1.5     # % max daily loss before auto-pause
                                 # If losses exceed this, stop all new entries
    
    MAX_POSITION_SIZE_PCT = 0.15  # 15% max per position (safety limit)
    
    # ========================================================================
    # ANALYSIS PARAMETERS
    # ========================================================================
    
    ANALYSIS_PERIOD_DAYS = 20    # Historical days to analyze for patterns
    BAR_INTERVAL = "1m"          # Price bar interval (1 minute)
    
    # ========================================================================
    # QUALITY FILTERS (Stock Selection)
    # ========================================================================
    
    MIN_CONFIRMATION_RATE = 0.25  # 25% minimum confirmation rate
    MIN_EXPECTED_VALUE = 0.0      # Must have positive expected value
    MIN_ENTRIES_PER_DAY = 3.0     # Minimum expected entries per day
    
    # ========================================================================
    # EXECUTION TIMING
    # ========================================================================
    
    COOLDOWN_MINUTES = 1         # Wait time after closing position before re-entry
    MARKET_OPEN = "09:31"        # Market open time (Eastern)
    MARKET_CLOSE = "16:00"       # Market close time (Eastern)
    ENTRY_CUTOFF = "15:50"       # Stop new entries time (10 min before close)
    
    # ========================================================================
    # PORTFOLIO SELECTION
    # ========================================================================
    
    # For 8-stock portfolio (2/4/2 strategy)
    NUM_CONSERVATIVE = 2         # Low volatility, stable
    NUM_MEDIUM = 4               # Balanced risk/reward
    NUM_AGGRESSIVE = 2           # Higher volatility, higher potential
    
    # For 16-stock portfolio (when scaling)
    NUM_CONSERVATIVE_16 = 4      # Low volatility, stable
    NUM_MEDIUM_16 = 8            # Balanced risk/reward
    NUM_AGGRESSIVE_16 = 4        # Higher volatility, higher potential
    
    # ========================================================================
    # FORECAST PARAMETERS
    # ========================================================================
    
    FORECAST_CONFIDENCE = 0.94   # 94% confidence level for ranges
    FORECAST_VARIANCE = 0.20     # ±20% for conservative/optimistic ranges
    
    # ========================================================================
    # SIMULATION PARAMETERS (for testing without real IBKR connection)
    # ========================================================================
    
    USE_SIMULATION = False  # PRODUCTION: Set to False to use real yfinance data
                            # DEVELOPMENT: Set to True for testing with historical data
                            # 
                            # NOTE: yfinance is blocked in Claude container (403 errors)
                            # but will work correctly in production deployment (Railway)
    
    # Simulation data source
    SIMULATION_MODE = "last_trading_day"  # Options:
                                          # "last_trading_day" - Use real data from last completed trading day
                                          # "synthetic" - Generate fake data (old behavior)
                                          
    SIMULATION_STARTING_BALANCE = 30000.0  # Starting balance for simulation mode
    
    # Simulation playback speed (for Live Monitor)
    SIMULATION_SPEED = 1.0  # 1.0 = real-time, 10.0 = 10x speed, 0.1 = slow motion
    
    # ========================================================================
    # PHASE 5 ENHANCEMENT FLAGS (Future Features - Not Yet Implemented)
    # ========================================================================
    
    # Feature toggles - Set to False for baseline behavior (Phase 1-4)
    ENABLE_ADAPTIVE_THRESHOLDS = False    # Use different entry thresholds per stock volatility
    ENABLE_STOCK_ROTATION = False         # Swap cold stocks mid-day with backups
    ENABLE_TIME_BASED_SIZING = False      # Adjust position size by time of day
    ENABLE_CORRELATION_FILTER = False     # Ensure low correlation in stock selection
    
    # Adaptive threshold settings (used when ENABLE_ADAPTIVE_THRESHOLDS = True)
    ENTRY_THRESHOLD_LOW_VOL = 1.0         # Entry threshold for low volatility stocks
    ENTRY_THRESHOLD_HIGH_VOL = 2.0        # Entry threshold for high volatility stocks
    VOLATILITY_LOW_THRESHOLD = 1.0        # Below this = low volatility
    VOLATILITY_HIGH_THRESHOLD = 2.0       # Above this = high volatility
    
    # Stock rotation settings (used when ENABLE_STOCK_ROTATION = True)
    NUM_BACKUP_STOCKS = 4                 # Number of backup stocks to select
    ROTATION_CHECK_INTERVAL = 60          # Minutes between rotation checks
    ROTATION_INACTIVITY_THRESHOLD = 60    # Minutes of no activity = cold stock
    
    # Time-based sizing settings (used when ENABLE_TIME_BASED_SIZING = True)
    POSITION_SIZE_MORNING = 0.08          # 8% during opening volatility
    POSITION_SIZE_PRIME = 0.11            # 11% during prime hours
    POSITION_SIZE_CLOSING = 0.08          # 8% near market close
    
    # Correlation settings (used when ENABLE_CORRELATION_FILTER = True)
    MAX_CORRELATION = 0.70                # Maximum acceptable correlation between stocks
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    @classmethod
    def get_position_size(cls, account_balance: float) -> float:
        """
        Calculate position size based on account balance.
        
        Args:
            account_balance: Current account balance from IBKR API
        
        Returns:
            Position size per stock in dollars
        
        Example:
            >>> config = TradingConfig()
            >>> position_size = config.get_position_size(30000)
            >>> print(position_size)
            3000.0  # For 8 stocks: $30K × 0.80 / 8 = $3K per position
        """
        deployed = account_balance * cls.DEPLOYMENT_RATIO
        return deployed / cls.NUM_STOCKS
    
    @classmethod
    def get_deployed_capital(cls, account_balance: float) -> float:
        """
        Calculate deployed capital from account balance.
        
        Args:
            account_balance: Current account balance from IBKR API
        
        Returns:
            Amount of capital deployed in trading
        """
        return account_balance * cls.DEPLOYMENT_RATIO
    
    @classmethod
    def get_reserve_capital(cls, account_balance: float) -> float:
        """
        Calculate reserve capital from account balance.
        
        Args:
            account_balance: Current account balance from IBKR API
        
        Returns:
            Amount of capital held in reserve
        """
        return account_balance * cls.RESERVE_RATIO
    
    @classmethod
    def get_portfolio_counts(cls) -> dict:
        """
        Get portfolio stock counts based on NUM_STOCKS setting.
        
        Returns:
            Dictionary with conservative, medium, aggressive counts
        """
        if cls.NUM_STOCKS == 8:
            return {
                'conservative': cls.NUM_CONSERVATIVE,
                'medium': cls.NUM_MEDIUM,
                'aggressive': cls.NUM_AGGRESSIVE
            }
        elif cls.NUM_STOCKS == 16:
            return {
                'conservative': cls.NUM_CONSERVATIVE_16,
                'medium': cls.NUM_MEDIUM_16,
                'aggressive': cls.NUM_AGGRESSIVE_16
            }
        else:
            # Default to 8-stock strategy
            return {
                'conservative': cls.NUM_CONSERVATIVE,
                'medium': cls.NUM_MEDIUM,
                'aggressive': cls.NUM_AGGRESSIVE
            }


# Create singleton instance for easy importing
config = TradingConfig()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example usage
    print("Trading Configuration")
    print("=" * 60)
    print(f"Deployment Ratio: {config.DEPLOYMENT_RATIO:.0%}")
    print(f"Number of Stocks: {config.NUM_STOCKS}")
    print(f"Entry Threshold: {config.ENTRY_THRESHOLD}%")
    print(f"Target 1: {config.TARGET_1}%")
    print(f"Target 2: {config.TARGET_2}%")
    print(f"Stop Loss: {config.STOP_LOSS}%")
    print(f"Daily Loss Limit: {config.DAILY_LOSS_LIMIT}%")
    print()
    
    # Example with $30,000 account
    account_balance = 30000
    print(f"Example with ${account_balance:,} account:")
    print(f"  Deployed Capital: ${config.get_deployed_capital(account_balance):,.0f}")
    print(f"  Reserve Capital: ${config.get_reserve_capital(account_balance):,.0f}")
    print(f"  Position Size: ${config.get_position_size(account_balance):,.0f} per stock")
    print()
    
    # Portfolio breakdown
    counts = config.get_portfolio_counts()
    print(f"Portfolio Breakdown ({config.NUM_STOCKS} stocks):")
    print(f"  Conservative: {counts['conservative']}")
    print(f"  Medium: {counts['medium']}")
    print(f"  Aggressive: {counts['aggressive']}")
