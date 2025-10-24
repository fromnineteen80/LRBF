"""
Filter Engine - Strategy Enhancement Filters
Checks all toggle conditions before allowing pattern entries
"""

from datetime import datetime, time
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from config.config import TradingConfig


class FilterEngine:
    """
    Evaluates whether a detected pattern should be traded based on
    active strategy enhancement filters.
    """
    
    def __init__(self, config: TradingConfig = None):
        """Initialize filter engine with configuration."""
        self.config = config or TradingConfig
        self.filter_log = []  # Track all filter checks
    
    def should_trade_pattern(
        self,
        ticker: str,
        pattern_data: Dict,
        market_data: pd.DataFrame,
        current_time: datetime = None
    ) -> Tuple[bool, str, Dict]:
        """
        Determine if a pattern should be traded based on active filters.
        
        Args:
            ticker: Stock symbol
            pattern_data: Pattern detection results
            market_data: OHLCV DataFrame with VWAP
            current_time: Current market time (for testing)
        
        Returns:
            (should_trade, reason, filter_results)
        """
        if current_time is None:
            current_time = datetime.now()
        
        filter_results = {
            'ticker': ticker,
            'timestamp': current_time.isoformat(),
            'pattern_price': pattern_data.get('entry_price', 0),
            'filters_checked': [],
            'filters_passed': [],
            'filters_failed': []
        }
        
        # If no filters enabled, trade immediately
        if not self._any_filters_enabled():
            return True, "No filters enabled", filter_results
        
        # Check each filter category
        passed = True
        reason = "All filters passed"
        
        # === Quality Filters ===
        if self._quality_filters_active():
            vwap_pass, vwap_reason = self._check_vwap_proximity(
                ticker, pattern_data, market_data
            )
            filter_results['filters_checked'].append('VWAP Proximity')
            if vwap_pass:
                filter_results['filters_passed'].append('VWAP Proximity')
            else:
                filter_results['filters_failed'].append(f'VWAP Proximity: {vwap_reason}')
                passed = False
                reason = vwap_reason
            
            vol_pass, vol_reason = self._check_volume_confirmation(
                ticker, pattern_data, market_data
            )
            filter_results['filters_checked'].append('Volume Confirmation')
            if vol_pass:
                filter_results['filters_passed'].append('Volume Confirmation')
            else:
                filter_results['filters_failed'].append(f'Volume Confirmation: {vol_reason}')
                if passed:  # Only update if not already failed
                    passed = False
                    reason = vol_reason
        
        # === Timing Filters ===
        if self._timing_filters_active():
            time_pass, time_reason = self._check_time_window(
                current_time
            )
            filter_results['filters_checked'].append('Time Window')
            if time_pass:
                filter_results['filters_passed'].append('Time Window')
            else:
                filter_results['filters_failed'].append(f'Time Window: {time_reason}')
                if passed:
                    passed = False
                    reason = time_reason
            
            macro_pass, macro_reason = self._check_macro_events(
                current_time
            )
            filter_results['filters_checked'].append('Macro Events')
            if macro_pass:
                filter_results['filters_passed'].append('Macro Events')
            else:
                filter_results['filters_failed'].append(f'Macro Events: {macro_reason}')
                if passed:
                    passed = False
                    reason = macro_reason
        
        # === Confluence Filters ===
        if self._confluence_filters_active():
            sr_pass, sr_reason = self._check_support_resistance(
                ticker, pattern_data, market_data
            )
            filter_results['filters_checked'].append('Support/Resistance')
            if sr_pass:
                filter_results['filters_passed'].append('Support/Resistance')
            else:
                filter_results['filters_failed'].append(f'S/R: {sr_reason}')
                if passed:
                    passed = False
                    reason = sr_reason
            
            trend_pass, trend_reason = self._check_trend_alignment(
                ticker, pattern_data, market_data
            )
            filter_results['filters_checked'].append('Trend Alignment')
            if trend_pass:
                filter_results['filters_passed'].append('Trend Alignment')
            else:
                filter_results['filters_failed'].append(f'Trend: {trend_reason}')
                if passed:
                    passed = False
                    reason = trend_reason
        
        # Log filter check
        self.filter_log.append(filter_results)
        
        return passed, reason, filter_results
    
    # =========================================
    # Filter Activation Checks
    # =========================================
    
    def _any_filters_enabled(self) -> bool:
        """Check if any filters are enabled."""
        return (
            self.config.ALL_ENHANCEMENTS_ON or
            self.config.QUALITY_FILTERS_ON or
            self.config.TIMING_FILTERS_ON or
            self.config.CONFLUENCE_FILTERS_ON
        )
    
    def _quality_filters_active(self) -> bool:
        """Check if quality filters should run."""
        return (
            self.config.ALL_ENHANCEMENTS_ON or
            self.config.QUALITY_FILTERS_ON
        )
    
    def _timing_filters_active(self) -> bool:
        """Check if timing filters should run."""
        return (
            self.config.ALL_ENHANCEMENTS_ON or
            self.config.TIMING_FILTERS_ON
        )
    
    def _confluence_filters_active(self) -> bool:
        """Check if confluence filters should run."""
        return (
            self.config.ALL_ENHANCEMENTS_ON or
            self.config.CONFLUENCE_FILTERS_ON
        )
    
    # =========================================
    # Quality Filters
    # =========================================
    
    def _check_vwap_proximity(
        self,
        ticker: str,
        pattern_data: Dict,
        market_data: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Check if entry price is within acceptable distance from VWAP.
        
        Returns:
            (passed, reason)
        """
        if not self.config.VWAP_PROXIMITY_ENABLED:
            return True, "VWAP proximity filter disabled"
        
        try:
            entry_price = pattern_data.get('entry_price', 0)
            if entry_price == 0:
                return False, "No entry price available"
            
            # Get current VWAP
            if 'vwap' not in market_data.columns:
                return False, "VWAP data not available"
            
            current_vwap = market_data['vwap'].iloc[-1]
            
            # Calculate distance
            distance_pct = abs((entry_price - current_vwap) / current_vwap * 100)
            max_distance = self.config.VWAP_PROXIMITY_MAX_PCT
            
            passed = distance_pct <= max_distance
            reason = (
                f"Price ${entry_price:.2f} is {distance_pct:.1f}% from VWAP ${current_vwap:.2f} "
                f"({'within' if passed else 'exceeds'} {max_distance}% limit)"
            )
            
            return passed, reason
            
        except Exception as e:
            return False, f"VWAP proximity check error: {str(e)}"
    
    def _check_volume_confirmation(
        self,
        ticker: str,
        pattern_data: Dict,
        market_data: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Check if breakout volume exceeds average by required multiplier.
        
        Returns:
            (passed, reason)
        """
        if not self.config.VOLUME_CONFIRMATION_ENABLED:
            return True, "Volume confirmation filter disabled"
        
        try:
            # Get breakout volume (last bar where pattern confirmed)
            breakout_volume = market_data['volume'].iloc[-1]
            
            # Calculate average volume (last 20 bars, excluding current)
            avg_volume = market_data['volume'].iloc[-21:-1].mean()
            
            # Calculate multiplier
            volume_multiplier = breakout_volume / avg_volume
            required_multiplier = self.config.VOLUME_CONFIRMATION_MULTIPLIER
            
            passed = volume_multiplier >= required_multiplier
            reason = (
                f"Breakout volume {breakout_volume:,.0f} is {volume_multiplier:.1f}x average "
                f"{avg_volume:,.0f} ({'meets' if passed else 'below'} {required_multiplier}x requirement)"
            )
            
            return passed, reason
            
        except Exception as e:
            return False, f"Volume confirmation check error: {str(e)}"
    
    # =========================================
    # Timing Filters
    # =========================================
    
    def _check_time_window(self, current_time: datetime) -> Tuple[bool, str]:
        """
        Check if current time is within acceptable trading windows.
        
        Returns:
            (passed, reason)
        """
        if not self.config.TIME_FILTER_ENABLED:
            return True, "Time window filter disabled"
        
        try:
            current_time_only = current_time.time()
            windows = self.config.TIME_FILTER_WINDOWS
            
            # Full day - always pass
            if 'full_day' in windows:
                return True, "Full day trading enabled"
            
            # Check custom window
            if 'custom' in windows:
                start_time = datetime.strptime(
                    self.config.CUSTOM_TIME_START, "%H:%M"
                ).time()
                end_time = datetime.strptime(
                    self.config.CUSTOM_TIME_END, "%H:%M"
                ).time()
                
                if start_time <= current_time_only <= end_time:
                    return True, f"Within custom window {self.config.CUSTOM_TIME_START}-{self.config.CUSTOM_TIME_END}"
                else:
                    return False, f"Outside custom window {self.config.CUSTOM_TIME_START}-{self.config.CUSTOM_TIME_END}"
            
            # Check first hour (09:31-10:30)
            if 'first_hour' in windows:
                first_hour_start = time(9, 31)
                first_hour_end = time(10, 30)
                if first_hour_start <= current_time_only <= first_hour_end:
                    return True, "Within first hour (09:31-10:30)"
            
            # Check last hour (15:00-16:00)
            if 'last_hour' in windows:
                last_hour_start = time(15, 0)
                last_hour_end = time(16, 0)
                if last_hour_start <= current_time_only <= last_hour_end:
                    return True, "Within last hour (15:00-16:00)"
            
            # If we get here, not in any enabled window
            return False, f"Outside enabled windows: {', '.join(windows)}"
            
        except Exception as e:
            return False, f"Time window check error: {str(e)}"
    
    def _check_macro_events(self, current_time: datetime) -> Tuple[bool, str]:
        """
        Check if today is a macro event day (FOMC, NFP, etc.).
        
        Returns:
            (passed, reason)
        """
        if not self.config.MACRO_EVENT_FILTER_ENABLED:
            return True, "Macro event filter disabled"
        
        # TODO: Integrate with economic calendar API
        # For now, placeholder logic
        # In production, check against FOMC dates, NFP dates, etc.
        
        # Example FOMC dates (hardcoded for now)
        fomc_dates = [
            datetime(2025, 1, 29).date(),
            datetime(2025, 3, 19).date(),
            datetime(2025, 5, 7).date(),
            datetime(2025, 6, 18).date(),
            datetime(2025, 7, 30).date(),
            datetime(2025, 9, 17).date(),
            datetime(2025, 11, 5).date(),
            datetime(2025, 12, 17).date(),
        ]
        
        current_date = current_time.date()
        
        if current_date in fomc_dates:
            return False, f"FOMC meeting day - trading suspended"
        
        # NFP is first Friday of each month
        if current_date.weekday() == 4:  # Friday
            if 1 <= current_date.day <= 7:  # First week
                return False, f"Non-Farm Payrolls day - trading suspended"
        
        return True, "No macro events today"
    
    # =========================================
    # Confluence Filters
    # =========================================
    
    def _check_support_resistance(
        self,
        ticker: str,
        pattern_data: Dict,
        market_data: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Check if entry is near support/resistance levels.
        
        Returns:
            (passed, reason)
        """
        if not self.config.SUPPORT_RESISTANCE_ENABLED:
            return True, "Support/resistance filter disabled"
        
        try:
            entry_price = pattern_data.get('entry_price', 0)
            if entry_price == 0:
                return False, "No entry price available"
            
            # Calculate support/resistance from recent highs/lows
            lookback = 20
            recent_highs = market_data['high'].iloc[-lookback:].nlargest(3)
            recent_lows = market_data['low'].iloc[-lookback:].nsmallest(3)
            
            # Combine into S/R levels
            sr_levels = list(recent_highs) + list(recent_lows)
            
            # Check if entry is near any S/R level
            tolerance = self.config.SUPPORT_RESISTANCE_TOLERANCE_PCT / 100
            
            for level in sr_levels:
                distance_pct = abs(entry_price - level) / level
                if distance_pct <= tolerance:
                    return True, f"Entry ${entry_price:.2f} near S/R level ${level:.2f} (within {tolerance*100:.1f}%)"
            
            return False, f"Entry ${entry_price:.2f} not near any S/R levels (tolerance {tolerance*100:.1f}%)"
            
        except Exception as e:
            return False, f"S/R check error: {str(e)}"
    
    def _check_trend_alignment(
        self,
        ticker: str,
        pattern_data: Dict,
        market_data: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Check if pattern aligns with required trend direction.
        
        Returns:
            (passed, reason)
        """
        if not self.config.TREND_ALIGNMENT_ENABLED:
            return True, "Trend alignment filter disabled"
        
        try:
            required_trend = self.config.TREND_ALIGNMENT_TYPE
            
            # If 'any' trend allowed, always pass
            if required_trend == 'any':
                return True, "Any trend allowed"
            
            # Calculate current trend using 20-period moving average
            if len(market_data) < 20:
                return False, "Insufficient data for trend calculation"
            
            ma_20 = market_data['close'].rolling(window=20).mean().iloc[-1]
            current_price = market_data['close'].iloc[-1]
            
            # Determine trend
            if current_price > ma_20:
                current_trend = 'uptrend'
            elif current_price < ma_20:
                current_trend = 'downtrend'
            else:
                current_trend = 'neutral'
            
            # Check alignment
            passed = (
                (required_trend == 'uptrend' and current_trend == 'uptrend') or
                (required_trend == 'downtrend' and current_trend == 'downtrend')
            )
            
            reason = (
                f"Current trend: {current_trend} (price ${current_price:.2f} vs MA ${ma_20:.2f}) "
                f"{'matches' if passed else 'does not match'} required {required_trend}"
            )
            
            return passed, reason
            
        except Exception as e:
            return False, f"Trend alignment check error: {str(e)}"
    
    # =========================================
    # Logging & Reporting
    # =========================================
    
    def get_filter_summary(self) -> Dict:
        """Get summary of all filter checks."""
        if not self.filter_log:
            return {
                'total_checks': 0,
                'total_passed': 0,
                'total_failed': 0,
                'failure_reasons': {}
            }
        
        total = len(self.filter_log)
        passed = sum(1 for log in self.filter_log if log['filters_failed'] == [])
        failed = total - passed
        
        # Count failure reasons
        failure_reasons = {}
        for log in self.filter_log:
            for failure in log['filters_failed']:
                filter_name = failure.split(':')[0]
                failure_reasons[filter_name] = failure_reasons.get(filter_name, 0) + 1
        
        return {
            'total_checks': total,
            'total_passed': passed,
            'total_failed': failed,
            'failure_reasons': failure_reasons
        }
    
    def clear_log(self):
        """Clear filter log."""
        self.filter_log = []
    
    def get_recent_filters(self, n: int = 10) -> List[Dict]:
        """Get last N filter checks."""
        return self.filter_log[-n:]


# Convenience function for pattern_detector.py integration
def check_pattern_filters(
    ticker: str,
    pattern_data: Dict,
    market_data: pd.DataFrame,
    config: TradingConfig = None
) -> Tuple[bool, str, Dict]:
    """
    Convenience function to check if pattern should be traded.
    
    Returns:
        (should_trade, reason, filter_results)
    """
    engine = FilterEngine(config)
    return engine.should_trade_pattern(ticker, pattern_data, market_data)
