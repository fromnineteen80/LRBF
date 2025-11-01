"""
Entry Signal Detector - Phase 0

Monitors real-time tick data and detects when entry threshold is crossed.

Entry Signals (from trading_strategy_explainer.md):
- 3-Step Geometric: +0.5% climb from pattern low
- VWAP Breakout: +0.5% above VWAP (with volume confirmation)

Returns entry confirmation with precise timestamp and price.

Author: The Luggage Room Boys Fund
Date: October 2025 - Phase 0
"""

from typing import Optional, Dict, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd


@dataclass
class EntrySignal:
    """
    Data class for entry signal confirmation.
    """
    confirmed: bool
    pattern_type: str  # '3-step' or 'vwap-breakout'
    ticker: str
    pattern_id: str
    
    # Entry details
    entry_time: Optional[datetime] = None
    entry_price: Optional[float] = None
    threshold_price: float = 0.0
    
    # Pattern reference
    pattern_low: float = 0.0
    vwap_at_pattern: Optional[float] = None
    
    # Volume (for VWAP breakout)
    volume_ratio: Optional[float] = None
    
    # Failure reason if not confirmed
    failure_reason: Optional[str] = None


class EntrySignalDetector:
    """
    Detects entry signals from real-time tick data.
    
    Monitors price after pattern completion and confirms when
    entry threshold (+0.5%) is crossed.
    
    Usage:
        detector = EntrySignalDetector()
        signal = detector.check_entry_signal(
            pattern=three_step_pattern,
            tick_stream=live_ticks,
            timeout_seconds=180
        )
    """
    
    def __init__(
        self,
        entry_threshold_pct: float = 0.5,  # +0.5% from pattern low/VWAP
        volume_multiplier: float = 1.5,  # For VWAP breakout volume confirmation
        timeout_seconds: int = 180  # 3 minutes max to confirm entry
    ):
        """
        Initialize entry signal detector.
        
        Args:
            entry_threshold_pct: Entry threshold percentage (default 0.5%)
            volume_multiplier: Volume confirmation for VWAP (default 1.5x)
            timeout_seconds: Max time to wait for entry signal (default 180s)
        """
        self.entry_threshold_pct = entry_threshold_pct
        self.volume_multiplier = volume_multiplier
        self.timeout_seconds = timeout_seconds
    
    def check_entry_signal_3step(
        self,
        pattern,  # ThreeStepPattern object
        tick_stream: pd.DataFrame,
        start_time: Optional[datetime] = None
    ) -> EntrySignal:
        """
        Check for entry signal on 3-Step Geometric pattern.
        
        Entry Rule: Price climbs +0.5% from pattern low
        
        Args:
            pattern: ThreeStepPattern object from pattern_detector.py
            tick_stream: DataFrame with columns: timestamp, last, volume
            start_time: Start monitoring from this time (default: pattern completion)
        
        Returns:
            EntrySignal object
        """
        if tick_stream.empty:
            return EntrySignal(
                confirmed=False,
                pattern_type='3-step',
                ticker=pattern.ticker,
                pattern_id=pattern.pattern_id,
                pattern_low=pattern.pattern_low,
                threshold_price=pattern.pattern_low * (1 + self.entry_threshold_pct / 100),
                failure_reason='no_tick_data'
            )
        
        # Calculate entry threshold
        threshold_price = pattern.pattern_low * (1 + self.entry_threshold_pct / 100)
        
        # Start monitoring from pattern completion
        if start_time is None:
            start_time = pattern.pattern_complete_time
        
        # Filter ticks after pattern completion
        tick_stream['timestamp'] = pd.to_datetime(tick_stream['timestamp'])
        future_ticks = tick_stream[tick_stream['timestamp'] >= start_time].copy()
        
        if future_ticks.empty:
            return EntrySignal(
                confirmed=False,
                pattern_type='3-step',
                ticker=pattern.ticker,
                pattern_id=pattern.pattern_id,
                pattern_low=pattern.pattern_low,
                threshold_price=threshold_price,
                failure_reason='no_future_ticks'
            )
        
        # Check for entry signal within timeout window
        timeout_time = start_time + timedelta(seconds=self.timeout_seconds)
        
        for idx, row in future_ticks.iterrows():
            tick_time = row['timestamp']
            tick_price = row['last']
            
            # Check timeout
            if tick_time > timeout_time:
                return EntrySignal(
                    confirmed=False,
                    pattern_type='3-step',
                    ticker=pattern.ticker,
                    pattern_id=pattern.pattern_id,
                    pattern_low=pattern.pattern_low,
                    threshold_price=threshold_price,
                    failure_reason='timeout'
                )
            
            # Check if threshold crossed
            if tick_price >= threshold_price:
                return EntrySignal(
                    confirmed=True,
                    pattern_type='3-step',
                    ticker=pattern.ticker,
                    pattern_id=pattern.pattern_id,
                    entry_time=tick_time,
                    entry_price=tick_price,
                    threshold_price=threshold_price,
                    pattern_low=pattern.pattern_low,
                    failure_reason=None
                )
        
        # No entry signal found in available data
        return EntrySignal(
            confirmed=False,
            pattern_type='3-step',
            ticker=pattern.ticker,
            pattern_id=pattern.pattern_id,
            pattern_low=pattern.pattern_low,
            threshold_price=threshold_price,
            failure_reason='not_confirmed_yet'
        )
    
    def check_entry_signal_vwap(
        self,
        pattern,  # VWAPBreakoutPattern object
        tick_stream: pd.DataFrame,
        start_time: Optional[datetime] = None
    ) -> EntrySignal:
        """
        Check for entry signal on VWAP Breakout pattern.
        
        Entry Rule: Price climbs +0.5% above VWAP with volume confirmation
        
        Args:
            pattern: VWAPBreakoutPattern object from vwap_breakout_detector.py
            tick_stream: DataFrame with columns: timestamp, last, volume
            start_time: Start monitoring from this time (default: breakout time)
        
        Returns:
            EntrySignal object
        """
        if tick_stream.empty:
            return EntrySignal(
                confirmed=False,
                pattern_type='vwap-breakout',
                ticker=pattern.ticker,
                pattern_id=pattern.pattern_id,
                vwap_at_pattern=pattern.vwap_at_breakout,
                threshold_price=pattern.vwap_at_breakout * (1 + self.entry_threshold_pct / 100),
                failure_reason='no_tick_data'
            )
        
        # Calculate entry threshold
        threshold_price = pattern.vwap_at_breakout * (1 + self.entry_threshold_pct / 100)
        
        # Start monitoring from breakout
        if start_time is None:
            start_time = pattern.breakout_time
        
        # Filter ticks after breakout
        tick_stream['timestamp'] = pd.to_datetime(tick_stream['timestamp'])
        future_ticks = tick_stream[tick_stream['timestamp'] >= start_time].copy()
        
        if future_ticks.empty:
            return EntrySignal(
                confirmed=False,
                pattern_type='vwap-breakout',
                ticker=pattern.ticker,
                pattern_id=pattern.pattern_id,
                vwap_at_pattern=pattern.vwap_at_breakout,
                threshold_price=threshold_price,
                failure_reason='no_future_ticks'
            )
        
        # Check for entry signal within timeout window
        timeout_time = start_time + timedelta(seconds=self.timeout_seconds)
        
        for idx, row in future_ticks.iterrows():
            tick_time = row['timestamp']
            tick_price = row['last']
            tick_volume = row.get('volume', 0)
            
            # Check timeout
            if tick_time > timeout_time:
                return EntrySignal(
                    confirmed=False,
                    pattern_type='vwap-breakout',
                    ticker=pattern.ticker,
                    pattern_id=pattern.pattern_id,
                    vwap_at_pattern=pattern.vwap_at_breakout,
                    threshold_price=threshold_price,
                    failure_reason='timeout'
                )
            
            # Check if threshold crossed
            if tick_price >= threshold_price:
                # Check volume confirmation
                recent_ticks = future_ticks[future_ticks['timestamp'] < tick_time].tail(20)
                
                if not recent_ticks.empty and 'volume' in recent_ticks.columns:
                    avg_volume = recent_ticks['volume'].mean()
                    volume_ratio = tick_volume / avg_volume if avg_volume > 0 else 0
                    
                    if volume_ratio >= self.volume_multiplier:
                        return EntrySignal(
                            confirmed=True,
                            pattern_type='vwap-breakout',
                            ticker=pattern.ticker,
                            pattern_id=pattern.pattern_id,
                            entry_time=tick_time,
                            entry_price=tick_price,
                            threshold_price=threshold_price,
                            vwap_at_pattern=pattern.vwap_at_breakout,
                            volume_ratio=volume_ratio,
                            failure_reason=None
                        )
                else:
                    # No volume data, accept price threshold only
                    return EntrySignal(
                        confirmed=True,
                        pattern_type='vwap-breakout',
                        ticker=pattern.ticker,
                        pattern_id=pattern.pattern_id,
                        entry_time=tick_time,
                        entry_price=tick_price,
                        threshold_price=threshold_price,
                        vwap_at_pattern=pattern.vwap_at_breakout,
                        volume_ratio=None,
                        failure_reason=None
                    )
        
        # No entry signal found in available data
        return EntrySignal(
            confirmed=False,
            pattern_type='vwap-breakout',
            ticker=pattern.ticker,
            pattern_id=pattern.pattern_id,
            vwap_at_pattern=pattern.vwap_at_breakout,
            threshold_price=threshold_price,
            failure_reason='not_confirmed_yet'
        )
    
    def check_entry_signal(
        self,
        pattern: Union[object, object],
        tick_stream: pd.DataFrame,
        pattern_type: str,
        start_time: Optional[datetime] = None
    ) -> EntrySignal:
        """
        Universal entry signal checker - works with both pattern types.
        
        Args:
            pattern: Pattern object (ThreeStepPattern or VWAPBreakoutPattern)
            tick_stream: Real-time tick data
            pattern_type: '3-step' or 'vwap-breakout'
            start_time: Optional start time for monitoring
        
        Returns:
            EntrySignal object
        """
        if pattern_type == '3-step':
            return self.check_entry_signal_3step(pattern, tick_stream, start_time)
        elif pattern_type == 'vwap-breakout':
            return self.check_entry_signal_vwap(pattern, tick_stream, start_time)
        else:
            raise ValueError(f"Unknown pattern type: {pattern_type}")


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import numpy as np
    from dataclasses import dataclass
    from datetime import datetime, timedelta
    
    print("Testing EntrySignalDetector...")
    print("=" * 60)
    
    # Mock pattern object for 3-Step
    @dataclass
    class MockThreeStepPattern:
        ticker: str
        pattern_id: str
        pattern_low: float
        pattern_complete_time: datetime
    
    # Create synthetic tick data
    base_time = datetime(2025, 10, 31, 10, 0, 0)
    timestamps = [base_time + timedelta(seconds=i) for i in range(200)]
    
    # Simulate price climbing from pattern low
    pattern_low = 150.0
    entry_threshold = pattern_low * 1.005  # +0.5%
    
    prices = []
    for i in range(len(timestamps)):
        if i < 100:
            # Before entry - hovering around pattern low
            price = pattern_low + np.random.normal(0, 0.05)
        elif i < 120:
            # Climbing toward entry
            progress = (i - 100) / 20
            price = pattern_low + (entry_threshold - pattern_low) * progress
        else:
            # After entry
            price = entry_threshold + np.random.normal(0.2, 0.1)
        
        prices.append(price)
    
    tick_data = pd.DataFrame({
        'timestamp': timestamps,
        'last': prices,
        'volume': np.random.randint(100, 300, len(timestamps))
    })
    
    # Create mock pattern
    pattern = MockThreeStepPattern(
        ticker='AAPL',
        pattern_id='test_pattern_1',
        pattern_low=pattern_low,
        pattern_complete_time=base_time
    )
    
    # Test detector
    detector = EntrySignalDetector()
    signal = detector.check_entry_signal_3step(pattern, tick_data)
    
    print(f"\nPattern Type: 3-Step Geometric")
    print(f"Pattern Low: ${pattern.pattern_low:.2f}")
    print(f"Entry Threshold: ${signal.threshold_price:.2f}")
    print(f"\nEntry Signal Confirmed: {signal.confirmed}")
    
    if signal.confirmed:
        print(f"Entry Time: {signal.entry_time}")
        print(f"Entry Price: ${signal.entry_price:.2f}")
        print(f"Above Threshold: +${signal.entry_price - signal.threshold_price:.2f}")
    else:
        print(f"Failure Reason: {signal.failure_reason}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete")
