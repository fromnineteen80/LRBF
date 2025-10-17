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
    
    # === API Configuration ===
    # Note: API keys should be in environment variables, not here
    RAPIDAPI_ENABLED = False    # Set to True when ready for production
    YFINANCE_DELAY = 15         # Minutes delay for free tier
    
    # === Simulation Settings ===
    SIMULATION_MODE = True      # Use mock data for testing
    SIMULATION_SEED = 42        # Random seed for reproducible tests


# Convenience function to get config as dict
def get_config_dict():
    """Return all config values as a dictionary."""
    return {
        key: value for key, value in vars(TradingConfig).items()
        if not key.startswith('_')
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
        'Stock Selection': ['NUM_CONSERVATIVE', 'NUM_MEDIUM', 'NUM_AGGRESSIVE', 'NUM_BACKUP']
    }
    
    for section, keys in sections.items():
        print(f"\n{section}:")
        for key in keys:
            if key in config:
                print(f"  {key:25} = {config[key]}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    print_config()
