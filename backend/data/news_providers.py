"""
News Data Providers

Integrates with IBKR and external APIs to fetch:
- Earnings calendars (via IBKR fundamental data)
- Economic event calendars
- Breaking news
- Analyst changes
- Trading halts
- Volume spikes (via IBKR real-time data)
- Price gaps (via IBKR real-time data)

Production requires:
- IBKR connection for fundamental data
- API keys for news services (NewsAPI, Benzinga, etc.)
- Error handling and rate limiting
- Caching to avoid redundant API calls
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

# Import IBKR connector for fundamental data
try:
    from backend.data.ibkr_connector import IBKRConnector
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False
    logging.warning("IBKRConnector not available - falling back to stub implementations")

logger = logging.getLogger(__name__)


def get_earnings_calendar(date: datetime, ibkr: Optional['IBKRConnector'] = None) -> List[Dict]:
    """
    Get earnings announcements for a specific date using IBKR fundamental data.
    
    Args:
        date: Target date
        ibkr: Optional IBKRConnector instance (if None, creates new connection)
    
    Returns:
        List of stocks with earnings:
        [
            {
                'ticker': 'AAPL',
                'earnings_date': '2025-10-28',
                'time': 'after_close',  # or 'before_open' (estimated based on typical patterns)
                'has_earnings_today': True/False
            },
            ...
        ]
    
    Note: IBKR provides earnings dates but not always the specific time (BMO/AMC).
    Time is estimated based on historical patterns.
    """
    if not IBKR_AVAILABLE:
        logger.warning("IBKR not available - get_earnings_calendar() returning empty")
        return []
    
    try:
        # Use provided connection or create new one
        close_connection = False
        if ibkr is None:
            ibkr = IBKRConnector()
            if not ibkr.connect():
                logger.error("Failed to connect to IBKR for earnings calendar")
                return []
            close_connection = True
        
        # Get top stocks and check each for earnings
        # In production, you'd want to check a broader universe
        # For now, this is a placeholder showing the integration pattern
        earnings_stocks = []
        
        # TODO: Iterate through your stock universe and check each
        # Example for a single ticker:
        # fundamental = ibkr.get_fundamental_data('AAPL')
        # if fundamental and fundamental.get('has_earnings_today'):
        #     earnings_stocks.append(fundamental)
        
        if close_connection:
            ibkr.disconnect()
        
        return earnings_stocks
        
    except Exception as e:
        logger.error(f"Error getting earnings calendar: {e}")
        return []


def has_earnings_today(ticker: str, date: datetime, ibkr: Optional['IBKRConnector'] = None) -> bool:
    """
    Check if stock has earnings announcement today using IBKR fundamental data.
    
    Args:
        ticker: Stock symbol
        date: Date to check
        ibkr: Optional IBKRConnector instance
    
    Returns:
        True if earnings today, False otherwise
    """
    if not IBKR_AVAILABLE:
        logger.warning(f"IBKR not available - has_earnings_today({ticker}) returning False")
        return False
    
    try:
        # Use provided connection or create new one
        close_connection = False
        if ibkr is None:
            ibkr = IBKRConnector()
            if not ibkr.connect():
                logger.error("Failed to connect to IBKR")
                return False
            close_connection = True
        
        # Get fundamental data which includes earnings info
        fundamental = ibkr.get_fundamental_data(ticker)
        
        if close_connection:
            ibkr.disconnect()
        
        if fundamental:
            return fundamental.get('has_earnings_today', False)
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking earnings for {ticker}: {e}")
        return False


def get_economic_calendar(date: datetime) -> List[str]:
    """
    Get major economic events for a specific date.
    
    Args:
        date: Target date
    
    Returns:
        List of event names:
        ['FOMC Rate Decision', 'CPI Report', 'NFP', ...]
    
    TODO: Integrate with:
    - Trading Economics API
    - Forex Factory calendar
    - Federal Reserve announcements
    """
    logger.warning("get_economic_calendar() is stubbed - no real API integration")
    return []


def get_breaking_news(ticker: str, minutes: int = None, hours: int = None) -> Optional[Dict]:
    """
    Get breaking news for a specific stock within last X minutes or hours.
    
    Args:
        ticker: Stock symbol
        minutes: Lookback period in minutes (default 5 minutes if neither specified)
        hours: Lookback period in hours (converted to minutes internally)
    
    Returns:
        {
            'headline': 'Apple announces new product',
            'summary': 'Apple Inc. today announced...',
            'timestamp': datetime(2025, 10, 27, 14, 30),
            'source': 'Reuters',
            'sentiment': 'positive' | 'negative' | 'neutral'
        }
    
    TODO: Integrate with:
    - NewsAPI
    - Benzinga News API
    - Twitter/X API
    """
    logger.warning("get_breaking_news() is stubbed - no real API integration")
    return None


def get_analyst_changes(ticker: str, hours: int = 24) -> Optional[Dict]:
    """
    Get analyst rating changes within last X hours.
    
    Args:
        ticker: Stock symbol
        hours: Lookback period in hours
    
    Returns:
        {
            'action': 'upgrade' | 'downgrade' | 'initiate' | 'reiterate',
            'firm': 'Goldman Sachs',
            'old_rating': 'Neutral',
            'new_rating': 'Buy',
            'old_target': 150.0,
            'new_target': 175.0,
            'summary': 'Goldman Sachs upgraded...'
        }
    
    TODO: Integrate with:
    - Benzinga API
    - StreetInsider
    - Analyst ratings aggregators
    """
    logger.warning("get_analyst_changes() is stubbed - no real API integration")
    return None


def has_fda_decision(ticker: str, date: datetime) -> bool:
    """
    Check if FDA decision expected today for biotech/pharma stock.
    
    Args:
        ticker: Stock symbol
        date: Date to check
    
    Returns:
        True if FDA decision expected today
    
    TODO: Integrate with:
    - FDA calendar
    - BioPharma Catalyst calendar
    """
    logger.warning("has_fda_decision() is stubbed - no real API integration")
    return False


def detect_volume_spike(ticker: str, ibkr: Optional['IBKRConnector'] = None, 
                        threshold: float = 3.0, lookback_minutes: int = 5) -> bool:
    """
    Detect if volume spike occurred (Xx normal volume) using IBKR real-time data.
    
    Args:
        ticker: Stock symbol
        ibkr: Optional IBKRConnector instance
        threshold: Spike threshold (e.g., 3.0 = 3x normal)
        lookback_minutes: Minutes to compare (default 5 minutes)
    
    Returns:
        True if volume spike detected
    """
    if not IBKR_AVAILABLE:
        logger.warning(f"IBKR not available - detect_volume_spike({ticker}) returning False")
        return False
    
    try:
        # Use provided connection or create new one
        close_connection = False
        if ibkr is None:
            ibkr = IBKRConnector()
            if not ibkr.connect():
                logger.error("Failed to connect to IBKR")
                return False
            close_connection = True
        
        # Get recent bar data to calculate volume
        # Using 1-minute bars for the last hour
        hist = ibkr.get_historical_data(
            ticker=ticker,
            period_days=1,
            bar_size='1 min'
        )
        
        if close_connection:
            ibkr.disconnect()
        
        if hist is None or len(hist) < lookback_minutes + 20:
            logger.warning(f"Insufficient data for volume spike detection: {ticker}")
            return False
        
        # Calculate average volume over previous 20 minutes (baseline)
        baseline_volume = hist['volume'].iloc[-(lookback_minutes + 20):-lookback_minutes].mean()
        
        # Calculate recent volume (last lookback_minutes)
        recent_volume = hist['volume'].iloc[-lookback_minutes:].mean()
        
        # Check if recent volume exceeds threshold
        if baseline_volume > 0 and recent_volume >= baseline_volume * threshold:
            logger.info(f"Volume spike detected for {ticker}: {recent_volume:.0f} vs baseline {baseline_volume:.0f} ({recent_volume/baseline_volume:.2f}x)")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error detecting volume spike for {ticker}: {e}")
        return False


def detect_price_gap(ticker: str, ibkr: Optional['IBKRConnector'] = None, 
                     threshold_pct: float = 2.0, lookback_minutes: int = 1) -> bool:
    """
    Detect if price gap occurred (X% move in Y minutes) using IBKR real-time data.
    
    Args:
        ticker: Stock symbol
        ibkr: Optional IBKRConnector instance
        threshold_pct: Gap threshold percentage (default 2.0%)
        lookback_minutes: Minutes to check (default 1 minute)
    
    Returns:
        True if price gap detected
    """
    if not IBKR_AVAILABLE:
        logger.warning(f"IBKR not available - detect_price_gap({ticker}) returning False")
        return False
    
    try:
        # Use provided connection or create new one
        close_connection = False
        if ibkr is None:
            ibkr = IBKRConnector()
            if not ibkr.connect():
                logger.error("Failed to connect to IBKR")
                return False
            close_connection = True
        
        # Get recent 1-minute bars
        hist = ibkr.get_historical_data(
            ticker=ticker,
            period_days=1,
            bar_size='1 min'
        )
        
        if close_connection:
            ibkr.disconnect()
        
        if hist is None or len(hist) < lookback_minutes + 1:
            logger.warning(f"Insufficient data for gap detection: {ticker}")
            return False
        
        # Calculate price change over lookback period
        start_price = hist['close'].iloc[-(lookback_minutes + 1)]
        end_price = hist['close'].iloc[-1]
        
        price_change_pct = abs((end_price - start_price) / start_price * 100)
        
        if price_change_pct >= threshold_pct:
            logger.info(f"Price gap detected for {ticker}: {price_change_pct:.2f}% in {lookback_minutes} min")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error detecting price gap for {ticker}: {e}")
        return False


def check_halt_risk(ticker: str, ibkr: Optional['IBKRConnector'] = None) -> Dict:
    """
    Comprehensive halt risk assessment using multiple signals.
    
    Args:
        ticker: Stock symbol
        ibkr: Optional IBKRConnector instance
    
    Returns:
        {
            'has_earnings_today': bool,
            'volume_spike': bool,
            'price_gap': bool,
            'halt_risk_score': float,  # 0-100 scale
            'recommendation': 'avoid' | 'caution' | 'normal'
        }
    """
    result = {
        'has_earnings_today': False,
        'volume_spike': False,
        'price_gap': False,
        'halt_risk_score': 0.0,
        'recommendation': 'normal'
    }
    
    try:
        # Use provided connection or create new one
        close_connection = False
        if ibkr is None and IBKR_AVAILABLE:
            ibkr = IBKRConnector()
            if not ibkr.connect():
                logger.error("Failed to connect to IBKR")
                return result
            close_connection = True
        
        # Check earnings
        result['has_earnings_today'] = has_earnings_today(ticker, datetime.now(), ibkr)
        
        # Check volume spike
        result['volume_spike'] = detect_volume_spike(ticker, ibkr, threshold=3.0)
        
        # Check price gap
        result['price_gap'] = detect_price_gap(ticker, ibkr, threshold_pct=2.0)
        
        if close_connection and ibkr:
            ibkr.disconnect()
        
        # Calculate halt risk score
        risk_score = 0.0
        if result['has_earnings_today']:
            risk_score += 40.0  # Earnings day = high risk
        if result['volume_spike']:
            risk_score += 30.0  # Volume spike = moderate risk
        if result['price_gap']:
            risk_score += 30.0  # Price gap = moderate risk
        
        result['halt_risk_score'] = min(risk_score, 100.0)
        
        # Recommendation
        if risk_score >= 70:
            result['recommendation'] = 'avoid'
        elif risk_score >= 40:
            result['recommendation'] = 'caution'
        else:
            result['recommendation'] = 'normal'
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking halt risk for {ticker}: {e}")
        return result
