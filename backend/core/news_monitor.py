"""
News & Event Monitoring System

3-Layer Defense:
1. Pre-market screening (morning report) - Exclude high-risk events
2. Real-time monitoring (during trading) - Exit on breaking news
3. Post-trade analysis (EOD report) - Track intervention effectiveness
"""

from typing import Dict, List
from datetime import datetime, timedelta
import logging
from backend.data.news_providers import (
    get_earnings_calendar,
    get_economic_calendar,
    get_breaking_news,
    get_analyst_changes,
    is_trading_halted,
    has_earnings_today,
    has_fda_decision,
    detect_volume_spike,
    detect_price_gap
)

logger = logging.getLogger(__name__)


def screen_for_news_events(ticker: str, date: datetime) -> Dict:
    """
    Pre-market screening for news/events that invalidate patterns.
    
    Called by morning report BEFORE analyzing stocks.
    Filters out stocks with extreme risk events.
    
    Args:
        ticker: Stock symbol
        date: Target date (typically today)
    
    Returns:
        {
            'tradeable': True/False,
            'risk_level': 'NONE' | 'ELEVATED' | 'EXTREME',
            'reason': str or None,
            'adjustments': {
                'dead_zone_multiplier': 0.5,
                'position_size_multiplier': 0.5
            } or None
        }
    """
    issues = []
    risk_level = 'NONE'
    adjustments = {}
    
    # ═══════════════════════════════════════════════════════════════
    # TIER 1: EXTREME RISK (Auto-exclude from trading)
    # ═══════════════════════════════════════════════════════════════
    
    # Earnings announcement today
    if has_earnings_today(ticker, date):
        return {
            'tradeable': False,
            'risk_level': 'EXTREME',
            'reason': 'Earnings announcement today',
            'adjustments': None
        }
    
    # FDA decision expected today
    if has_fda_decision(ticker, date):
        return {
            'tradeable': False,
            'risk_level': 'EXTREME',
            'reason': 'FDA decision expected today',
            'adjustments': None
        }
    
    # ═══════════════════════════════════════════════════════════════
    # TIER 2: ELEVATED RISK (Tradeable but with adjustments)
    # ═══════════════════════════════════════════════════════════════
    
    # Major economic events today
    econ_events = get_economic_calendar(date)
    if econ_events:
        risk_level = 'ELEVATED'
        issues.append(f"Economic events: {', '.join(econ_events)}")
        adjustments['dead_zone_multiplier'] = 0.5   # Shorter timeouts
        adjustments['position_size_multiplier'] = 0.5  # Smaller positions
    
    # Recent analyst changes (last 24 hours)
    analyst_changes = get_analyst_changes(ticker, hours=24)
    if analyst_changes:
        risk_level = 'ELEVATED'
        issues.append(f"Analyst action: {analyst_changes['summary']}")
        adjustments['dead_zone_multiplier'] = 0.7   # Slightly shorter timeouts
    
    # ═══════════════════════════════════════════════════════════════
    # RETURN RESULT
    # ═══════════════════════════════════════════════════════════════
    
    return {
        'tradeable': True,
        'risk_level': risk_level,
        'reason': '; '.join(issues) if issues else None,
        'adjustments': adjustments if adjustments else None
    }


class NewsMonitor:
    """
    Real-time news monitoring during trading hours.
    
    Checks every 60 seconds for:
    - Trading halts
    - Volume spikes (3x normal)
    - Price gaps (2% in 1 minute)
    - Breaking news
    
    Returns action recommendations:
    - NORMAL: Continue trading
    - TIGHTEN_STOPS: Reduce stop loss
    - EXIT_IMMEDIATELY: Close position now
    - HALT_TRADING: Exchange halted stock
    """
    
    def __init__(self):
        self.last_check = {}
        self.interventions = []
    
    def monitor_tickers(self, tickers: List[str]) -> Dict[str, str]:
        """
        Check all active positions for breaking news/events.
        
        Run every 60 seconds during trading.
        
        Args:
            tickers: List of stock symbols currently in positions
        
        Returns:
            {
                'AAPL': 'EXIT_IMMEDIATELY',
                'TSLA': 'TIGHTEN_STOPS',
                'MSFT': 'NORMAL',
                ...
            }
        """
        actions = {}
        
        for ticker in tickers:
            # ═══════════════════════════════════════════════════════════════
            # CRITICAL: TRADING HALT
            # ═══════════════════════════════════════════════════════════════
            if is_trading_halted(ticker):
                actions[ticker] = 'HALT_TRADING'
                self.log_intervention(ticker, 'HALT_DETECTED')
                continue
            
            # ═══════════════════════════════════════════════════════════════
            # CRITICAL: VOLUME SPIKE (3x normal)
            # ═══════════════════════════════════════════════════════════════
            if detect_volume_spike(ticker, threshold=3.0):
                actions[ticker] = 'EXIT_IMMEDIATELY'
                self.log_intervention(ticker, 'VOLUME_SPIKE_3X')
                continue
            
            # ═══════════════════════════════════════════════════════════════
            # CRITICAL: PRICE GAP (2% in 1 minute)
            # ═══════════════════════════════════════════════════════════════
            if detect_price_gap(ticker, threshold_pct=2.0):
                actions[ticker] = 'EXIT_IMMEDIATELY'
                self.log_intervention(ticker, 'PRICE_GAP_2PCT')
                continue
            
            # ═══════════════════════════════════════════════════════════════
            # CRITICAL: BREAKING NEWS
            # ═══════════════════════════════════════════════════════════════
            breaking = get_breaking_news(ticker, minutes=5)
            if breaking and breaking['severity'] == 'CRITICAL':
                actions[ticker] = 'EXIT_IMMEDIATELY'
                self.log_intervention(ticker, f"NEWS: {breaking['headline']}")
                continue
            
            # ═══════════════════════════════════════════════════════════════
            # ELEVATED: HIGH SEVERITY NEWS
            # ═══════════════════════════════════════════════════════════════
            if breaking and breaking['severity'] == 'HIGH':
                actions[ticker] = 'TIGHTEN_STOPS'
                self.log_intervention(ticker, f"NEWS_HIGH: {breaking['headline']}")
                continue
            
            # ═══════════════════════════════════════════════════════════════
            # NORMAL: NO ISSUES DETECTED
            # ═══════════════════════════════════════════════════════════════
            actions[ticker] = 'NORMAL'
        
        return actions
    
    def log_intervention(self, ticker: str, reason: str):
        """
        Log intervention for EOD analysis.
        
        Args:
            ticker: Stock symbol
            reason: Why intervention occurred
        """
        self.interventions.append({
            'timestamp': datetime.now(),
            'ticker': ticker,
            'reason': reason
        })
        
        logger.warning(f"News intervention: {ticker} - {reason}")
    
    def get_interventions(self) -> List[Dict]:
        """
        Return all interventions for the day.
        
        Used by EOD reporter to calculate:
        - How many times news monitoring saved capital
        - Which types of events most common
        - Effectiveness of screening vs real-time
        
        Returns:
            List of intervention dicts
        """
        return self.interventions
    
    def reset_interventions(self):
        """Clear interventions log (call at start of new day)."""
        self.interventions = []


def generate_morning_screening_report(excluded_stocks: List[Dict]) -> str:
    """
    Generate human-readable summary of pre-market screening.
    
    Args:
        excluded_stocks: List of stocks excluded by screening
                        [{'ticker': 'AAPL', 'reason': '...'}, ...]
    
    Returns:
        Formatted string summary
    """
    if not excluded_stocks:
        return "âœ… No stocks excluded - all clear for trading"
    
    lines = [
        f"âš ï¸ {len(excluded_stocks)} stocks excluded from morning report:",
        ""
    ]
    
    # Group by reason
    by_reason = {}
    for stock in excluded_stocks:
        reason = stock['reason']
        if reason not in by_reason:
            by_reason[reason] = []
        by_reason[reason].append(stock['ticker'])
    
    # Format grouped output
    for reason, tickers in sorted(by_reason.items()):
        lines.append(f"  {reason}:")
        lines.append(f"    {', '.join(tickers)}")
        lines.append("")
    
    return "\n".join(lines)


def generate_realtime_summary(interventions: List[Dict]) -> str:
    """
    Generate human-readable summary of real-time interventions.
    
    Args:
        interventions: List from NewsMonitor.get_interventions()
    
    Returns:
        Formatted string summary
    """
    if not interventions:
        return "âœ… No real-time interventions - clean trading day"
    
    lines = [
        f"âš ï¸ {len(interventions)} real-time interventions:",
        ""
    ]
    
    for intervention in interventions:
        timestamp = intervention['timestamp'].strftime('%H:%M:%S')
        ticker = intervention['ticker']
        reason = intervention['reason']
        lines.append(f"  [{timestamp}] {ticker}: {reason}")
    
    return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Test pre-market screening
    print("=== PRE-MARKET SCREENING ===")
    result = screen_for_news_events('AAPL', datetime.now())
    print(f"AAPL: {result}")
    
    # Test real-time monitoring
    print("\n=== REAL-TIME MONITORING ===")
    monitor = NewsMonitor()
    actions = monitor.monitor_tickers(['AAPL', 'TSLA', 'MSFT'])
    print(f"Actions: {actions}")
    
    # Test intervention logging
    print("\n=== INTERVENTIONS LOG ===")
    print(generate_realtime_summary(monitor.get_interventions()))
