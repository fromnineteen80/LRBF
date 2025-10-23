"""
Simulation Helper Module

Handles intelligent simulation using real historical data from the last completed trading day.
This allows testing the full workflow (Morning → Live → EOD) when markets are closed.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

from datetime import datetime, timedelta, date
from typing import Optional, Tuple
import pandas as pd


def get_last_trading_day(reference_date: Optional[date] = None) -> date:
    """
    Get the last completed trading day.
    
    Accounts for:
    - Weekends (Saturday/Sunday → Friday)
    - After-hours (before 4 PM → previous day)
    - Holidays (uses simple weekend logic for now)
    
    Args:
        reference_date: Date to check from (defaults to today)
    
    Returns:
        Date of last completed trading day
    
    Examples:
        >>> # If today is Saturday Oct 14, 2025
        >>> get_last_trading_day()
        datetime.date(2025, 10, 10)  # Friday
        
        >>> # If today is Monday Oct 16, 2025 at 10 AM
        >>> get_last_trading_day()
        datetime.date(2025, 10, 10)  # Friday (Monday not complete yet)
    """
    if reference_date is None:
        reference_date = date.today()
    
    current_datetime = datetime.now()
    
    # If it's currently a trading day but before 4 PM ET, use previous day
    # (because today isn't complete yet)
    if reference_date == date.today():
        market_close = current_datetime.replace(hour=16, minute=0, second=0, microsecond=0)
        if current_datetime < market_close:
            # Market hasn't closed yet, use previous day
            reference_date = reference_date - timedelta(days=1)
    
    # Walk backwards until we find a weekday
    checking_date = reference_date
    
    while True:
        # Check if it's a weekend
        if checking_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            checking_date = checking_date - timedelta(days=1)
            continue
        
        # TODO: Check against holiday calendar
        # For now, just return the weekday
        return checking_date


def get_simulation_date_range(last_trading_day: date, analysis_days: int = 20) -> Tuple[date, date]:
    """
    Get date range for simulation analysis.
    
    Args:
        last_trading_day: The day we're simulating
        analysis_days: Number of trading days to analyze before
    
    Returns:
        Tuple of (start_date, end_date) for analysis
    
    Example:
        >>> last_day = date(2025, 10, 10)  # Friday
        >>> get_simulation_date_range(last_day, 20)
        (date(2025, 9, 12), date(2025, 10, 9))  # ~20 trading days before
    """
    # Go back approximately analysis_days trading days
    # Rough estimate: 20 trading days ≈ 28 calendar days (accounts for weekends)
    calendar_days_back = int(analysis_days * 1.4)
    
    end_date = last_trading_day - timedelta(days=1)  # Day before simulation day
    start_date = last_trading_day - timedelta(days=calendar_days_back)
    
    return start_date, end_date


def is_market_open(current_time: Optional[datetime] = None) -> bool:
    """
    Check if market is currently open.
    
    Args:
        current_time: Time to check (defaults to now)
    
    Returns:
        True if market is open, False otherwise
    """
    if current_time is None:
        current_time = datetime.now()
    
    # Check if weekday
    if current_time.weekday() >= 5:
        return False
    
    # Check if within trading hours (9:31 AM - 4:00 PM ET)
    market_open = current_time.replace(hour=9, minute=31, second=0, microsecond=0)
    market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= current_time <= market_close


def get_simulation_status() -> dict:
    """
    Get current simulation status information.
    
    Returns:
        Dictionary with simulation status details
    """
    last_trading_day = get_last_trading_day()
    is_open = is_market_open()
    start_date, end_date = get_simulation_date_range(last_trading_day)
    
    return {
        'last_trading_day': last_trading_day.isoformat(),
        'market_currently_open': is_open,
        'simulation_analysis_start': start_date.isoformat(),
        'simulation_analysis_end': end_date.isoformat(),
        'reason': 'Market closed' if not is_open else 'Testing mode'
    }


def should_use_simulation() -> bool:
    """
    Determine if simulation mode should be active.
    
    This can be based on:
    - User setting (from session or database)
    - Whether market is currently open
    - Time of day
    
    Returns:
        True if simulation should be active
    """
    # For now, just check if market is closed
    # Later: combine with user preference from settings
    return not is_market_open()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("Simulation Helper - Status")
    print("=" * 60)
    
    status = get_simulation_status()
    print(f"Last Trading Day: {status['last_trading_day']}")
    print(f"Market Currently Open: {status['market_currently_open']}")
    print(f"Analysis Period: {status['simulation_analysis_start']} to {status['simulation_analysis_end']}")
    print(f"Reason: {status['reason']}")
    print()
    
    # Example: Get last trading day
    last_day = get_last_trading_day()
    print(f"Last completed trading day: {last_day.strftime('%A, %B %d, %Y')}")
    
    # Example: Get date range for morning analysis
    start, end = get_simulation_date_range(last_day, analysis_days=20)
    print(f"Morning analysis would use: {start} to {end}")
    
    # Example: Check if market is open
    if is_market_open():
        print("✅ Market is OPEN - Use live data")
    else:
        print("⏸️  Market is CLOSED - Use simulation with last trading day")
