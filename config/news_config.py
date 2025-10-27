"""
News API Configuration

Stores API keys, endpoints, and provider settings for news monitoring system.

SECURITY NOTE: Never commit actual API keys to GitHub!
- Load from .env file using python-dotenv
- Store secrets in Railway/production environment variables
"""

import os
from dotenv import load_dotenv

load_dotenv()


class NewsAPIConfig:
    """Configuration for external news APIs."""
    
    # ═══════════════════════════════════════════════════════════════
    # EARNINGS CALENDAR API
    # ═══════════════════════════════════════════════════════════════
    
    EARNINGS_PROVIDER = os.getenv('EARNINGS_PROVIDER', 'earnings_whispers')
    
    # Earnings Whispers (paid, most accurate)
    EARNINGS_WHISPERS_API_KEY = os.getenv('EARNINGS_WHISPERS_API_KEY', None)
    EARNINGS_WHISPERS_URL = "https://api.earningswhispers.com/v2"
    
    # NASDAQ Earnings Calendar (free alternative)
    NASDAQ_EARNINGS_URL = "https://api.nasdaq.com/api/calendar/earnings"
    
    # ═══════════════════════════════════════════════════════════════
    # ECONOMIC CALENDAR API
    # ═══════════════════════════════════════════════════════════════
    
    ECONOMIC_PROVIDER = os.getenv('ECONOMIC_PROVIDER', 'trading_economics')
    
    # Trading Economics (paid)
    TRADING_ECONOMICS_API_KEY = os.getenv('TRADING_ECONOMICS_API_KEY', None)
    TRADING_ECONOMICS_URL = "https://api.tradingeconomics.com"
    
    # Forex Factory (free, requires scraping)
    FOREX_FACTORY_URL = "https://www.forexfactory.com/calendar"
    
    # ═══════════════════════════════════════════════════════════════
    # BREAKING NEWS API
    # ═══════════════════════════════════════════════════════════════
    
    NEWS_PROVIDER = os.getenv('NEWS_PROVIDER', 'newsapi')
    
    # NewsAPI.org (free tier: 100 requests/day)
    NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', None)
    NEWSAPI_URL = "https://newsapi.org/v2/everything"
    
    # Benzinga News API (paid, real-time)
    BENZINGA_API_KEY = os.getenv('BENZINGA_API_KEY', None)
    BENZINGA_URL = "https://api.benzinga.com/api/v2"
    
    # Alpha Vantage News Sentiment (free tier)
    ALPHAVANTAGE_API_KEY = os.getenv('ALPHAVANTAGE_API_KEY', None)
    ALPHAVANTAGE_NEWS_URL = "https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
    
    # ═══════════════════════════════════════════════════════════════
    # ANALYST RATINGS API
    # ═══════════════════════════════════════════════════════════════
    
    ANALYST_PROVIDER = os.getenv('ANALYST_PROVIDER', 'benzinga')
    
    # Benzinga Analyst Ratings (paid)
    BENZINGA_RATINGS_URL = "https://api.benzinga.com/api/v2.1/calendar/ratings"
    
    # TipRanks (paid)
    TIPRANKS_API_KEY = os.getenv('TIPRANKS_API_KEY', None)
    TIPRANKS_URL = "https://api.tipranks.com"
    
    # ═══════════════════════════════════════════════════════════════
    # TRADING HALTS
    # ═══════════════════════════════════════════════════════════════
    
    # NASDAQ TradeHalts (free)
    NASDAQ_HALTS_URL = "https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts"
    
    # NYSE Halt Feed (free)
    NYSE_HALTS_URL = "https://www.nyse.com/api/regulatory/halts"
    
    # ═══════════════════════════════════════════════════════════════
    # RATE LIMITS & CACHING
    # ═══════════════════════════════════════════════════════════════
    
    # Request delays (seconds)
    EARNINGS_CACHE_HOURS = 24       # Cache earnings calendar for 24h
    ECONOMIC_CACHE_HOURS = 24       # Cache economic calendar for 24h
    NEWS_CACHE_MINUTES = 0          # No cache for breaking news (real-time)
    ANALYST_CACHE_HOURS = 1         # Cache analyst changes for 1h
    
    # Rate limits
    NEWSAPI_FREE_TIER_DAILY_LIMIT = 100
    BENZINGA_BASIC_MONTHLY_LIMIT = 1000
    
    # Request timeout (seconds)
    API_TIMEOUT = 10
    
    # ═══════════════════════════════════════════════════════════════
    # FDA DECISION CALENDAR
    # ═══════════════════════════════════════════════════════════════
    
    FDA_PROVIDER = os.getenv('FDA_PROVIDER', 'biopharmcatalyst')
    
    # BiopharmCatalyst (free)
    BIOPHARMCATALYST_URL = "https://www.biopharmcatalyst.com/calendars/fda-calendar"
    
    # ClinicalTrials.gov (free)
    CLINICALTRIALS_URL = "https://clinicaltrials.gov/api/v2"
    
    # ═══════════════════════════════════════════════════════════════
    # EVENT PRIORITY & THRESHOLDS
    # ═══════════════════════════════════════════════════════════════
    
    # Events that trigger EXTREME risk (auto-exclude)
    EXTREME_RISK_EVENTS = [
        'EARNINGS_TODAY',
        'FDA_DECISION_TODAY',
        'ACQUISITION_ANNOUNCEMENT',
        'BANKRUPTCY_FILING'
    ]
    
    # Events that trigger ELEVATED risk (trade with caution)
    ELEVATED_RISK_EVENTS = [
        'FOMC_RATE_DECISION',
        'CPI_REPORT',
        'NFP_REPORT',
        'EARNINGS_TOMORROW',
        'ANALYST_DOWNGRADE',
        'SECTOR_NEWS'
    ]
    
    # News sentiment thresholds
    CRITICAL_NEWS_KEYWORDS = [
        'bankruptcy', 'fraud', 'investigation', 'recall',
        'delisting', 'halt', 'suspended', 'emergency',
        'fda rejects', 'class action', 'criminal charges'
    ]
    
    HIGH_NEWS_KEYWORDS = [
        'downgrade', 'miss', 'disappoints', 'concern',
        'warning', 'delay', 'postpone', 'lower guidance'
    ]


class NewsMonitoringDefaults:
    """Default settings for news monitoring behavior."""
    
    # Pre-market screening
    SCREEN_BEFORE_MORNING_REPORT = True
    EXCLUDE_EARNINGS_DAY = True
    EXCLUDE_FDA_DAY = True
    EXCLUDE_EARNINGS_TOMORROW = False  # Optional: exclude day before earnings
    
    # Real-time monitoring
    ENABLE_REALTIME_MONITORING = True
    CHECK_INTERVAL_SECONDS = 60
    
    # Intervention thresholds
    VOLUME_SPIKE_THRESHOLD = 3.0    # 3x normal = auto-exit
    PRICE_GAP_THRESHOLD_PCT = 2.0   # 2% move in 1 min = auto-exit
    
    # Risk adjustments
    ELEVATED_RISK_DEAD_ZONE_MULT = 0.5      # Reduce timeouts by 50%
    ELEVATED_RISK_POSITION_SIZE_MULT = 0.5  # Reduce position by 50%


def validate_api_keys() -> Dict[str, bool]:
    """
    Check which API keys are configured.
    
    Returns:
        {
            'earnings_whispers': True/False,
            'trading_economics': True/False,
            'newsapi': True/False,
            'benzinga': True/False,
            ...
        }
    """
    return {
        'earnings_whispers': bool(NewsAPIConfig.EARNINGS_WHISPERS_API_KEY),
        'trading_economics': bool(NewsAPIConfig.TRADING_ECONOMICS_API_KEY),
        'newsapi': bool(NewsAPIConfig.NEWSAPI_KEY),
        'benzinga': bool(NewsAPIConfig.BENZINGA_API_KEY),
        'alphavantage': bool(NewsAPIConfig.ALPHAVANTAGE_API_KEY),
        'tipranks': bool(NewsAPIConfig.TIPRANKS_API_KEY)
    }


def print_api_status():
    """Print which news APIs are configured."""
    print("═" * 60)
    print("NEWS API CONFIGURATION STATUS")
    print("═" * 60)
    
    keys = validate_api_keys()
    
    for api_name, configured in keys.items():
        status = "âœ… Configured" if configured else "âš ï¸ Not configured"
        print(f"{api_name:25} {status}")
    
    print("\nâ„¹ï¸  To configure missing APIs:")
    print("   1. Get API keys from provider websites")
    print("   2. Add to .env file (e.g., NEWSAPI_KEY=your_key_here)")
    print("   3. Restart application")
    print("═" * 60)


if __name__ == '__main__':
    print_api_status()
