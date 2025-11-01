"""
VWAP Breakout Pattern Detector - Phase 0

Detects VWAP breakout patterns using real-time tick data.
Matches pattern_detector.py architecture for consistency.

Pattern Algorithm:
1. BELOW VWAP: Price drops below VWAP
2. STABILIZE: Price stays below/near VWAP for 2-5 bars (10-25 seconds)
3. BREAKOUT: Price crosses back above VWAP
4. ENTRY SIGNAL: Price climbs +0.5% above VWAP with volume confirmation

Used by Morning Report (historicals) AND Railyard (real-time).

Author: The Luggage Room Boys Fund
Date: October 2025 - Phase 0
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class VWAPBreakoutPattern:
    """
    Data class for VWAP breakout pattern.
    """
    ticker: str
    pattern_id: str
    
    # Pattern detection
    below_vwap_time: datetime
    below_vwap_price: float
    stabilization_bars: int
    breakout_time: datetime
    breakout_price: float
    vwap_at_breakout: float
    
    # Entry confirmation
    entry_confirmed: bool
    entry_time: Optional[datetime] = None
    entry_price: Optional[float] = None
    volume_ratio: Optional[float] = None  # Actual volume / avg volume
    
    # Metadata
    total_duration_seconds: float = 0


class VWAPBreakoutDetector:
    """
    Detects VWAP breakout patterns in real-time tick data.
    
    Architecture matches pattern_detector.py for consistency.
    
    Usage:
        detector = VWAPBreakoutDetector()
        patterns = detector.detect_patterns(tick_data, 'AAPL')
    """
    
    def __init__(
        self,
        entry_threshold_pct: float = 0.5,  # Entry signal: +0.5% above VWAP
        stabilization_min_bars: int = 2,  # Min bars for stabilization
        stabilization_max_bars: int = 5,  # Max bars for stabilization
        volume_multiplier: float = 1.5,  # Volume must be 1.5x recent average
        aggregation_seconds: int = 5  # 5-second micro-bars (same as pattern_detector.py)
    ):
        """
        Initialize VWAP breakout pattern detector.
        
        Args:
            entry_threshold_pct: % above VWAP to trigger entry (default 0.5%)
            stabilization_min_bars: Minimum bars below VWAP (default 2)
            stabilization_max_bars: Maximum bars to wait (default 5)
            volume_multiplier: Volume confirmation multiplier (default 1.5x)
            aggregation_seconds: Tick aggregation window (default 5s)
        """
        self.entry_threshold_pct = entry_threshold_pct
        self.stabilization_min_bars = stabilization_min_bars
        self.stabilization_max_bars = stabilization_max_bars
        self.volume_multiplier = volume_multiplier
        self.aggregation_seconds = aggregation_seconds
    
    def detect_patterns(
        self,
        tick_data: pd.DataFrame,
        ticker: str
    ) -> List[VWAPBreakoutPattern]:
        """
        Detect all VWAP breakout patterns in tick data.
        
        Args:
            tick_data: DataFrame with columns: timestamp, last, volume
                      Optional: vwap (if not provided, calculated)
            ticker: Stock symbol
        
        Returns:
            List of VWAPBreakoutPattern objects
        """
        if tick_data.empty or len(tick_data) < 100:
            return []
        
        # Aggregate ticks into micro-bars (same as pattern_detector.py)
        micro_bars = self._aggregate_to_microbars(tick_data)
        
        if micro_bars.empty or len(micro_bars) < 20:
            return []
        
        # Ensure VWAP column exists
        if 'vwap' not in micro_bars.columns:
            micro_bars = self._calculate_vwap(micro_bars)
        
        patterns = []
        data_len = len(micro_bars)
        
        # Scan for patterns
        i = 0
        while i < data_len - 10:
            pattern = self._scan_for_pattern(
                micro_bars=micro_bars,
                current_idx=i,
                ticker=ticker
            )
            
            if pattern:
                patterns.append(pattern)
                # Skip ahead past this pattern
                i = micro_bars.index.get_loc(pattern.breakout_time) + 1
            else:
                i += 1
        
        return patterns
    
    def _aggregate_to_microbars(self, tick_data: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate tick data into micro-bars (5-second windows).
        IDENTICAL to pattern_detector.py for consistency.
        
        Args:
            tick_data: Raw tick data
        
        Returns:
            DataFrame with OHLC + volume for each micro-bar
        """
        # Ensure timestamp column
        if 'timestamp' not in tick_data.columns:
            return pd.DataFrame()
        
        # Set timestamp as index
        df = tick_data.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Resample to micro-bars
        micro_bars = df.resample(f'{self.aggregation_seconds}S').agg({
            'last': ['first', 'max', 'min', 'last'],  # OHLC
            'volume': 'sum'
        })
        
        # Flatten column names
        micro_bars.columns = ['open', 'high', 'low', 'close', 'volume']
        micro_bars = micro_bars.reset_index()
        micro_bars.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        # Drop rows with NaN (no ticks in that window)
        micro_bars = micro_bars.dropna()
        
        return micro_bars
    
    def _calculate_vwap(self, micro_bars: pd.DataFrame) -> pd.DataFrame:
        """Calculate VWAP from micro-bars."""
        df = micro_bars.copy()
        
        # Typical price
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        
        # VWAP = cumulative(typical_price * volume) / cumulative(volume)
        df['vwap'] = (
            (df['typical_price'] * df['volume']).cumsum() / 
            df['volume'].cumsum()
        )
        
        return df
    
    def _scan_for_pattern(
        self,
        micro_bars: pd.DataFrame,
        current_idx: int,
        ticker: str
    ) -> Optional[VWAPBreakoutPattern]:
        """
        Scan for VWAP breakout pattern starting at current index.
        
        Returns:
            VWAPBreakoutPattern if found, None otherwise
        """
        if current_idx >= len(micro_bars) - 10:
            return None
        
        # STEP 1: Price drops BELOW VWAP
        current_bar = micro_bars.iloc[current_idx]
        
        if current_bar['close'] >= current_bar['vwap']:
            return None  # Not below VWAP
        
        below_vwap_time = current_bar['timestamp']
        below_vwap_price = current_bar['close']
        
        # STEP 2: STABILIZATION (stay below/near VWAP for 2-5 bars)
        stabilization_bars = 0
        j = current_idx + 1
        
        while j < len(micro_bars) and stabilization_bars < self.stabilization_max_bars:
            bar = micro_bars.iloc[j]
            
            # Check if still below or within 0.3% of VWAP
            if bar['close'] <= bar['vwap'] * 1.003:
                stabilization_bars += 1
                j += 1
            else:
                break
        
        # Need at least min_bars of stabilization
        if stabilization_bars < self.stabilization_min_bars:
            return None
        
        # STEP 3: BREAKOUT (price crosses back above VWAP)
        breakout_idx = None
        breakout_bar = None
        
        for k in range(j, min(j + 10, len(micro_bars))):
            bar = micro_bars.iloc[k]
            if bar['close'] > bar['vwap']:
                breakout_idx = k
                breakout_bar = bar
                break
        
        if breakout_idx is None:
            return None
        
        breakout_time = breakout_bar['timestamp']
        breakout_price = breakout_bar['close']
        vwap_at_breakout = breakout_bar['vwap']
        
        # STEP 4: ENTRY SIGNAL (+0.5% above VWAP with volume)
        entry_threshold = vwap_at_breakout * (1 + self.entry_threshold_pct / 100)
        
        entry_confirmed = False
        entry_time = None
        entry_price = None
        volume_ratio = None
        
        for m in range(breakout_idx, min(breakout_idx + 5, len(micro_bars))):
            bar = micro_bars.iloc[m]
            
            if bar['close'] >= entry_threshold:
                # Check volume confirmation
                recent_vol = micro_bars.iloc[max(0, m-20):m]['volume'].mean()
                
                if recent_vol > 0 and bar['volume'] >= recent_vol * self.volume_multiplier:
                    entry_confirmed = True
                    entry_time = bar['timestamp']
                    entry_price = bar['close']
                    volume_ratio = bar['volume'] / recent_vol if recent_vol > 0 else 0
                    break
        
        # Calculate duration
        if entry_time:
            total_duration = (entry_time - below_vwap_time).total_seconds()
        else:
            total_duration = (breakout_time - below_vwap_time).total_seconds()
        
        # Generate unique pattern ID
        pattern_id = f"{ticker}_vwap_{int(breakout_time.timestamp())}"
        
        # Create pattern object
        pattern = VWAPBreakoutPattern(
            ticker=ticker,
            pattern_id=pattern_id,
            below_vwap_time=below_vwap_time,
            below_vwap_price=below_vwap_price,
            stabilization_bars=stabilization_bars,
            breakout_time=breakout_time,
            breakout_price=breakout_price,
            vwap_at_breakout=vwap_at_breakout,
            entry_confirmed=entry_confirmed,
            entry_time=entry_time,
            entry_price=entry_price,
            volume_ratio=volume_ratio,
            total_duration_seconds=total_duration
        )
        
        return pattern


# ============================================================================
# MAIN INTERFACE FUNCTION FOR MORNING REPORT
# ============================================================================

def analyze_vwap_breakout_patterns(
    tick_df: pd.DataFrame,
    ticker: str,
    entry_threshold: float = 0.5,
    volume_multiplier: float = 1.5,
    aggregation_window_seconds: int = 5
) -> Dict:
    """
    Analyze VWAP breakout patterns using IBKR tick data.
    
    This is the main interface function used by morning_report.py.
    Matches pattern_detector.py interface for consistency.
    
    Args:
        tick_df: DataFrame with tick data (timestamp, last, volume)
        ticker: Stock symbol
        entry_threshold: % above VWAP to confirm entry (default 0.5%)
        volume_multiplier: Volume confirmation multiplier (default 1.5x)
        aggregation_window_seconds: Window for aggregating ticks (default 5s)
    
    Returns:
        Dictionary with comprehensive pattern analysis
    """
    # Initialize detector
    detector = VWAPBreakoutDetector(
        entry_threshold_pct=entry_threshold,
        volume_multiplier=volume_multiplier,
        aggregation_seconds=aggregation_window_seconds
    )
    
    # Detect all patterns
    all_patterns = detector.detect_patterns(tick_df, ticker)
    
    # Separate confirmed entries
    confirmed_entries = [p for p in all_patterns if p.entry_confirmed]
    
    # Calculate statistics (simplified - exit simulation done elsewhere)
    total_patterns = len(all_patterns)
    total_confirmed = len(confirmed_entries)
    
    confirmation_rate = total_confirmed / total_patterns if total_patterns > 0 else 0
    
    return {
        'ticker': ticker,
        'all_patterns': all_patterns,
        'confirmed_entries': confirmed_entries,
        'total_patterns_found': total_patterns,
        'confirmed_entries_count': total_confirmed,
        'confirmation_rate': confirmation_rate,
        'data_source': 'ibkr_tick_data',
        'aggregation_window_seconds': aggregation_window_seconds
    }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("Testing VWAPBreakoutDetector...")
    print("=" * 60)
    
    # Create synthetic tick data
    timestamps = pd.date_range(start='2025-10-31 10:00:00', periods=500, freq='1S')
    
    # Simulate VWAP breakout pattern
    prices = []
    volumes = []
    base_price = 150.0
    
    for i in range(len(timestamps)):
        if i < 100:  # Above VWAP
            price = base_price + np.random.normal(0, 0.1)
            volume = np.random.randint(100, 200)
        elif i < 110:  # Drop below VWAP
            price = base_price - 0.5 - np.random.normal(0, 0.05)
            volume = np.random.randint(150, 250)
        elif i < 125:  # Stabilize below VWAP
            price = base_price - 0.5 + np.random.normal(0, 0.03)
            volume = np.random.randint(80, 150)
        elif i < 135:  # Breakout above VWAP
            price = base_price + (i - 125) * 0.05 + np.random.normal(0, 0.02)
            volume = np.random.randint(200, 400)  # Higher volume
        else:  # Post-breakout
            price = base_price + 0.5 + np.random.normal(0, 0.1)
            volume = np.random.randint(100, 200)
        
        prices.append(price)
        volumes.append(volume)
    
    tick_data = pd.DataFrame({
        'timestamp': timestamps,
        'last': prices,
        'volume': volumes
    })
    
    # Test detector
    result = analyze_vwap_breakout_patterns(tick_data, 'AAPL')
    
    print(f"\nDetected {result['total_patterns_found']} pattern(s)")
    print(f"Confirmed entries: {result['confirmed_entries_count']}")
    print(f"Confirmation rate: {result['confirmation_rate']*100:.1f}%")
    
    for i, pattern in enumerate(result['confirmed_entries'], 1):
        print(f"\nPattern {i}:")
        print(f"  ID: {pattern.pattern_id}")
        print(f"  Below VWAP: ${pattern.below_vwap_price:.2f} at {pattern.below_vwap_time}")
        print(f"  Stabilization: {pattern.stabilization_bars} bars")
        print(f"  Breakout: ${pattern.breakout_price:.2f} (VWAP: ${pattern.vwap_at_breakout:.2f})")
        print(f"  Entry: ${pattern.entry_price:.2f} (volume: {pattern.volume_ratio:.1f}x avg)")
        print(f"  Duration: {pattern.total_duration_seconds:.1f} seconds")
    
    print("\n" + "=" * 60)
    print("✅ Test complete")
