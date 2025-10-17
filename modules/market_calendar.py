"""
Market Calendar Module

Provides NYSE trading day detection and market hours information.
Uses pandas_market_calendars for accurate holiday schedules.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import pandas_market_calendars as mcal
import pandas as pd
from datetime import datetime, date, time
import pytz


class MarketCalendar:
    """NYSE market calendar with trading day detection."""
    
    def __init__(self):
        """Initialize with NYSE calendar."""
        self.calendar = mcal.get_calendar('NYSE')
        self.eastern = pytz.timezone('US/Eastern')
    
    def is_trading_day(self, check_date: date = None) -> bool:
        """
        Check if a given date is a trading day.
        
        Args:
            check_date: Date to check (default: today)
        
        Returns:
            True if trading day, False otherwise
        
        Example:
            >>> calendar = MarketCalendar()
            >>> calendar.is_trading_day()  # Is today a trading day?
            True
        """
        if check_date is None:
            check_date = datetime.now(self.eastern).date()
        
        # Get schedule for the day
        schedule = self.calendar.schedule(
            start_date=check_date,
            end_date=check_date
        )
        
        return len(schedule) > 0
    
    def next_trading_day(self, from_date: date = None) -> date:
        """
        Get the next trading day after a given date.
        
        Args:
            from_date: Starting date (default: today)
        
        Returns:
            Next trading day as date object
        """
        if from_date is None:
            from_date = datetime.now(self.eastern).date()
        
        # Get next 10 days of schedule
        schedule = self.calendar.schedule(
            start_date=from_date,
            end_date=from_date + pd.Timedelta(days=10)
        )
        
        if len(schedule) == 0:
            return None
        
        # Return first date after from_date
        return schedule.index[0].date()
    
    def get_market_hours(self, check_date: date = None) -> dict:
        """
        Get market hours for a trading day.
        
        Args:
            check_date: Date to check (default: today)
        
        Returns:
            Dictionary with open/close times or None if not trading day
        """
        if check_date is None:
            check_date = datetime.now(self.eastern).date()
        
        if not self.is_trading_day(check_date):
            return None
        
        schedule = self.calendar.schedule(
            start_date=check_date,
            end_date=check_date
        )
        
        if len(schedule) == 0:
            return None
        
        row = schedule.iloc[0]
        
        return {
            'open': row['market_open'].to_pydatetime(),
            'close': row['market_close'].to_pydatetime(),
            'pre_market': row['market_open'].to_pydatetime().replace(hour=4, minute=0),
            'after_hours': row['market_close'].to_pydatetime().replace(hour=20, minute=0)
        }
    
    def get_market_status(self) -> dict:
        """
        Get current market status.
        
        Returns:
            Dictionary with status, times, and market info
        """
        now = datetime.now(self.eastern)
        today = now.date()
        
        result = {
            'status': 'closed',
            'is_trading_day': False,
            'current_time': now,
            'next_trading_day': self.next_trading_day(today)
        }
        
        # Check if today is a trading day
        if not self.is_trading_day(today):
            return result
        
        result['is_trading_day'] = True
        hours = self.get_market_hours(today)
        result['market_open'] = hours['open']
        result['market_close'] = hours['close']
        
        # Determine status based on current time
        current_time = now.time()
        
        if current_time < time(4, 0):
            result['status'] = 'closed'
        elif current_time < time(9, 30):
            result['status'] = 'pre_market'
        elif current_time < time(16, 0):
            result['status'] = 'open'
            result['time_until_close'] = hours['close'] - now
        elif current_time < time(20, 0):
            result['status'] = 'after_hours'
        else:
            result['status'] = 'closed'
        
        return result


# Convenience functions
def is_trading_day(check_date: date = None) -> bool:
    """Quick check if date is a trading day."""
    calendar = MarketCalendar()
    return calendar.is_trading_day(check_date)


def get_market_status() -> dict:
    """Quick access to current market status."""
    calendar = MarketCalendar()
    return calendar.get_market_status()


if __name__ == "__main__":
    print("=" * 80)
    print("MARKET CALENDAR TEST")
    print("=" * 80)
    
    calendar = MarketCalendar()
    
    # Test 1: Is today a trading day?
    today = datetime.now(calendar.eastern).date()
    is_trading = calendar.is_trading_day(today)
    print(f"Today ({today}): {'TRADING DAY' if is_trading else 'NOT TRADING'}")
    
    # Test 2: Market status
    status = calendar.get_market_status()
    print(f"Current Status: {status['status'].upper()}")
    print(f"Next trading day: {status['next_trading_day']}")
    print("=" * 80)
