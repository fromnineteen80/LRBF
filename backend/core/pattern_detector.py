"""
VWAP Recovery Pattern Detector V3 - True Intraminute (Tick Data)
Detects patterns using IBKR tick data for sub-second precision

Enhanced capabilities:
- Pure tick data analysis (bid/ask/last/volume per tick)
- Pattern detection at tick level
- Sub-second entry confirmation timing
- Execution cycle tracking at millisecond precision

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import uuid
from backend.core.filter_engine import FilterEngine


class PatternDetector:
    """
    Enhanced pattern detector with true intraminute (tick-level) analysis.
    """
    
    def __init__(
        self,
        decline_threshold_pct: float = 1.0,
        entry_confirmation_pct: float = 1.5,
        target_1_pct: float = 0.75,
        target_2_pct: float = 2.0,
        stop_loss_pct: float = 0.5,
        filter_engine: FilterEngine = None,
        aggregation_window_seconds: int = 5
    ):
        """
        Initialize pattern detector for tick-level analysis.
        
        Args:
            decline_threshold_pct: Minimum decline to detect (Step 1)
            entry_confirmation_pct: % climb to confirm entry
            target_1_pct: First profit target
            target_2_pct: Second profit target
            stop_loss_pct: Stop loss threshold
            filter_engine: Optional filter engine for enhanced strategy
            aggregation_window_seconds: Window for aggregating ticks into micro-bars (default 5s)
        """
        self.decline_threshold = decline_threshold_pct
        self.entry_confirmation = entry_confirmation_pct
        self.target_1 = target_1_pct
        self.target_2 = target_2_pct
        self.stop_loss = stop_loss_pct
        self.filter_engine = filter_engine
        self.aggregation_window = aggregation_window_seconds
        
        # Pattern detection windows (in seconds)
        self.lookback_window_seconds = 180  # 3 minutes lookback for recent high
        self.pattern_completion_window_seconds = 120  # 2 minutes max for pattern
        self.entry_confirmation_window_seconds = 180  # 3 minutes max for entry
    
    def detect_all_patterns(
        self,
        tick_df: pd.DataFrame,
        ticker: str,
        analysis_date: datetime
    ) -> List[Dict]:
        """
        Detect all VWAP recovery patterns in tick data.
        
        Args:
            tick_df: DataFrame with tick data (timestamp, bid, ask, last, volume)
            ticker: Stock symbol
            analysis_date: Date of analysis
        
        Returns:
            List of pattern dictionaries with sub-second timing precision
        """
        if tick_df.empty or len(tick_df) < 100:
            return []
        
        # First, aggregate ticks into micro-bars for pattern scanning
        # This creates rolling windows we can analyze
        micro_bars = self._aggregate_ticks_to_bars(
            tick_df, 
            window_seconds=self.aggregation_window
        )
        
        if micro_bars.empty or len(micro_bars) < 50:
            return []
        
        patterns = []
        data_len = len(micro_bars)
        
        # Calculate lookback in bars
        bars_per_lookback = int(self.lookback_window_seconds / self.aggregation_window)
        bars_per_pattern_window = int(self.pattern_completion_window_seconds / self.aggregation_window)
        bars_per_entry_window = int(self.entry_confirmation_window_seconds / self.aggregation_window)
        
        # Scan for 3-step patterns
        for i in range(bars_per_lookback, data_len - bars_per_entry_window):
            
            # STEP 1: DECLINE (scan recent window for high)
            lookback_slice = micro_bars.iloc[i-bars_per_lookback:i+1]
            recent_high = lookback_slice['high'].max()
            current_low = micro_bars['low'].iloc[i]
            
            decline_amount = recent_high - current_low
            decline_pct = (decline_amount / recent_high) * 100
            
            if decline_pct < self.decline_threshold:
                continue
            
            decline_bar_idx = i
            decline_timestamp = micro_bars['timestamp'].iloc[i]
            
            # STEP 2: 50% RECOVERY
            recovery_target = current_low + (decline_amount * 0.5)
            
            recovery_found = False
            recovery_window = micro_bars.iloc[i+1:min(i+bars_per_pattern_window, data_len)]
            
            for j, row in recovery_window.iterrows():
                if row['high'] >= recovery_target:
                    recovery_high = row['high']
                    recovery_bar_idx = j
                    recovery_timestamp = row['timestamp']
                    recovery_amount = recovery_high - current_low
                    recovery_found = True
                    break
            
            if not recovery_found:
                continue
            
            # STEP 3: 50% RETRACEMENT
            retracement_target = recovery_high - (recovery_amount * 0.5)
            
            retracement_found = False
            retracement_window = micro_bars.iloc[recovery_bar_idx+1:min(recovery_bar_idx+bars_per_pattern_window, data_len)]
            
            for k, row in retracement_window.iterrows():
                if row['low'] <= retracement_target:
                    last_low = row['low']
                    pattern_complete_idx = k
                    pattern_complete_timestamp = row['timestamp']
                    retracement_found = True
                    break
            
            if not retracement_found:
                continue
            
            # PATTERN COMPLETE - Calculate detection time with millisecond precision
            detection_time_ms = (pattern_complete_timestamp - decline_timestamp).total_seconds() * 1000
            
            # ENTRY CONFIRMATION (check tick data for precise entry)
            entry_window_start = pattern_complete_timestamp
            entry_window_end = pattern_complete_timestamp + timedelta(seconds=self.entry_confirmation_window_seconds)
            
            entry_result = self._check_entry_confirmation_tick_level(
                tick_df,
                last_low,
                self.entry_confirmation,
                entry_window_start,
                entry_window_end
            )
            
            if not entry_result['confirmed']:
                # Pattern detected but no entry
                pattern = {
                    'pattern_id': f"{ticker}_{analysis_date.isoformat()}_{uuid.uuid4().hex[:8]}",
                    'ticker': ticker,
                    'date': analysis_date.isoformat(),
                    'timestamp': pattern_complete_timestamp,
                    'detection_time_ms': detection_time_ms,
                    'entry_confirmed': False,
                    'outcome': 'no_entry',
                    'failure_reason': entry_result.get('reason', 'no_confirmation')
                }
                patterns.append(pattern)
                continue
            
            # === FILTER CHECK (Enhanced Strategy Only) ===
            if self.filter_engine:
                pattern_data_for_filter = {
                    'entry_price': entry_result['entry_price'],
                    'target_1': entry_result['entry_price'] * (1 + self.target_1 / 100),
                    'target_2': entry_result['entry_price'] * (1 + self.target_2 / 100),
                    'stop_loss': entry_result['entry_price'] * (1 - self.stop_loss / 100)
                }
                
                filter_passed, filter_reason, filter_results = self.filter_engine.should_trade_pattern(
                    ticker=ticker,
                    pattern_data=pattern_data_for_filter,
                    market_data=micro_bars,
                    current_time=entry_result['entry_timestamp']
                )
                
                if not filter_passed:
                    # Pattern confirmed but blocked by filters
                    pattern = {
                        'pattern_id': f"{ticker}_{analysis_date.isoformat()}_{uuid.uuid4().hex[:8]}",
                        'ticker': ticker,
                        'date': analysis_date.isoformat(),
                        'timestamp': pattern_complete_timestamp,
                        'detection_time_ms': detection_time_ms,
                        'entry_confirmed': True,
                        'entry_price': entry_result['entry_price'],
                        'filter_checked': True,
                        'filter_passed': False,
                        'filter_reason': filter_reason,
                        'filter_results': filter_results,
                        'outcome': 'filtered_out',
                        'failure_reason': f"Blocked by filter: {filter_reason}"
                    }
                    patterns.append(pattern)
                    continue
            
            # ENTRY CONFIRMED - Simulate trade execution with tick-level precision
            entry_price = entry_result['entry_price']
            entry_timestamp = entry_result['entry_timestamp']
            entry_latency_ms = np.random.normal(50, 15)  # Simulated IBKR latency
            
            # SIMULATE TRADE OUTCOME (using tick data for maximum precision)
            trade_result = self._simulate_trade_outcome_tick_level(
                tick_df,
                entry_price,
                entry_timestamp,
                self.target_1,
                self.target_2,
                self.stop_loss
            )
            
            # Calculate total cycle time (milliseconds)
            total_cycle_ms = (
                detection_time_ms +  # Pattern detection
                entry_latency_ms +  # Entry execution
                (entry_result['confirmation_time_ms']) +  # Time to confirm entry
                trade_result['hold_time_ms'] +  # Hold time
                trade_result['exit_latency_ms'] +  # Exit execution
                (trade_result['settlement_lag_minutes'] * 60 * 1000)  # Settlement
            )
            
            # Calculate dead zone if applicable
            dead_zone_duration_ms = 0
            opportunity_cost = 0
            if trade_result['outcome'] == 'win' and trade_result.get('dead_zone_ms', 0) > 0:
                dead_zone_duration_ms = trade_result['dead_zone_ms']
                opportunity_cost = self._calculate_opportunity_cost(
                    entry_price,
                    dead_zone_duration_ms / 1000 / 60  # Convert to minutes
                )
            
            # Build complete pattern record with millisecond precision
            pattern = {
                # Identification
                'pattern_id': f"{ticker}_{analysis_date.isoformat()}_{uuid.uuid4().hex[:8]}",
                'ticker': ticker,
                'date': analysis_date.isoformat(),
                'timestamp': pattern_complete_timestamp,
                
                # Pattern geometry
                'recent_high': recent_high,
                'decline_low': current_low,
                'decline_pct': decline_pct,
                'recovery_high': recovery_high,
                'last_low': last_low,
                
                # Timing - Category #14 (Execution Cycle) - MILLISECOND PRECISION
                'detection_time_ms': detection_time_ms,
                'entry_confirmation_time_ms': entry_result['confirmation_time_ms'],
                'entry_latency_ms': entry_latency_ms,
                'hold_time_ms': trade_result['hold_time_ms'],
                'exit_latency_ms': trade_result['exit_latency_ms'],
                'settlement_lag_minutes': trade_result['settlement_lag_minutes'],
                'total_cycle_ms': total_cycle_ms,
                'total_cycle_seconds': total_cycle_ms / 1000,
                'total_cycle_minutes': total_cycle_ms / 1000 / 60,
                
                # Entry/Exit
                'entry_confirmed': True,
                'entry_price': entry_price,
                'entry_time': entry_timestamp,
                'exit_price': trade_result['exit_price'],
                'exit_time': trade_result['exit_time'],
                
                # Outcome
                'outcome': trade_result['outcome'],
                'pnl': trade_result['pnl'],
                'pnl_pct': trade_result['pnl_pct'],
                
                # Dead Zone (Category #3)
                'dead_zone_duration_ms': dead_zone_duration_ms,
                'opportunity_cost': opportunity_cost,
                
                # Additional metrics
                'exit_reason': trade_result['exit_reason'],
                
                # Intraminute metadata
                'data_source': 'ibkr_tick_data',
                'aggregation_window_seconds': self.aggregation_window
            }
            
            patterns.append(pattern)
        
        return patterns
    
    def _aggregate_ticks_to_bars(
        self,
        tick_df: pd.DataFrame,
        window_seconds: int = 5
    ) -> pd.DataFrame:
        """
        Aggregate tick data into micro-bars for pattern scanning.
        
        Args:
            tick_df: DataFrame with tick data
            window_seconds: Aggregation window in seconds
        
        Returns:
            DataFrame with OHLCV micro-bars
        """
        if tick_df.empty or 'timestamp' not in tick_df.columns:
            return pd.DataFrame()
        
        df = tick_df.copy()
        df.set_index('timestamp', inplace=True)
        
        # Create OHLCV bars from ticks
        bars = pd.DataFrame()
        bars['open'] = df['last'].resample(f'{window_seconds}S').first()
        bars['high'] = df['last'].resample(f'{window_seconds}S').max()
        bars['low'] = df['last'].resample(f'{window_seconds}S').min()
        bars['close'] = df['last'].resample(f'{window_seconds}S').last()
        bars['volume'] = df['volume'].resample(f'{window_seconds}S').sum()
        
        # Calculate VWAP for each bar
        df['pv'] = df['last'] * df['volume']
        bars['vwap'] = (
            df['pv'].resample(f'{window_seconds}S').sum() /
            df['volume'].resample(f'{window_seconds}S').sum()
        )
        
        bars.reset_index(inplace=True)
        bars.dropna(inplace=True)
        
        return bars
    
    def _check_entry_confirmation_tick_level(
        self,
        tick_df: pd.DataFrame,
        last_low: float,
        confirmation_pct: float,
        window_start: datetime,
        window_end: datetime
    ) -> Dict:
        """
        Check if price climbs enough to confirm entry using tick data.
        
        Args:
            tick_df: Tick data
            last_low: Pattern completion price
            confirmation_pct: % climb required
            window_start: Start of confirmation window
            window_end: End of confirmation window
        
        Returns:
            Dict with confirmation status and millisecond timing
        """
        confirmation_target = last_low * (1 + confirmation_pct / 100)
        
        # Filter ticks to confirmation window
        window_ticks = tick_df[
            (tick_df['timestamp'] >= window_start) &
            (tick_df['timestamp'] <= window_end)
        ]
        
        if window_ticks.empty:
            return {'confirmed': False, 'reason': 'no_data'}
        
        # Find first tick that hits confirmation target
        for idx, row in window_ticks.iterrows():
            if row['last'] >= confirmation_target:
                confirmation_time_ms = (row['timestamp'] - window_start).total_seconds() * 1000
                
                return {
                    'confirmed': True,
                    'entry_price': confirmation_target,
                    'entry_timestamp': row['timestamp'],
                    'entry_time': row['timestamp'],
                    'confirmation_time_ms': confirmation_time_ms
                }
        
        return {'confirmed': False, 'reason': 'no_confirmation'}
    
    def _simulate_trade_outcome_tick_level(
        self,
        tick_df: pd.DataFrame,
        entry_price: float,
        entry_timestamp: datetime,
        target_1_pct: float,
        target_2_pct: float,
        stop_loss_pct: float
    ) -> Dict:
        """
        Simulate trade from entry to exit using tick data.
        
        Args:
            tick_df: Tick data
            entry_price: Entry price
            entry_timestamp: Entry timestamp
            target_1_pct: First profit target %
            target_2_pct: Second profit target %
            stop_loss_pct: Stop loss %
        
        Returns:
            Dict with trade outcome and millisecond timing
        """
        target_1_price = entry_price * (1 + target_1_pct / 100)
        target_2_price = entry_price * (1 + target_2_pct / 100)
        stop_price = entry_price * (1 - stop_loss_pct / 100)
        
        # Filter ticks after entry
        future_ticks = tick_df[tick_df['timestamp'] > entry_timestamp]
        
        if future_ticks.empty:
            return {
                'outcome': 'timeout',
                'exit_price': entry_price,
                'exit_time': entry_timestamp,
                'pnl': 0,
                'pnl_pct': 0,
                'hold_time_ms': 0,
                'exit_latency_ms': 0,
                'settlement_lag_minutes': 0.5,
                'exit_reason': 'no_data'
            }
        
        hit_target_1 = False
        target_1_timestamp = None
        
        for idx, row in future_ticks.iterrows():
            # Check stop loss
            if row['last'] <= stop_price:
                hold_time_ms = (row['timestamp'] - entry_timestamp).total_seconds() * 1000
                
                return {
                    'outcome': 'loss',
                    'exit_price': stop_price,
                    'exit_time': row['timestamp'],
                    'pnl': stop_price - entry_price,
                    'pnl_pct': -stop_loss_pct,
                    'hold_time_ms': hold_time_ms,
                    'exit_latency_ms': np.random.normal(55, 15),
                    'settlement_lag_minutes': 0.5,
                    'exit_reason': 'stop_loss',
                    'dead_zone_ms': 0
                }
            
            # Check target 1
            if not hit_target_1 and row['last'] >= target_1_price:
                hit_target_1 = True
                target_1_timestamp = row['timestamp']
            
            # If hit target 1, look for target 2 or return to target 1
            if hit_target_1:
                if row['last'] >= target_2_price:
                    # Hit target 2 - exit
                    hold_time_ms = (row['timestamp'] - entry_timestamp).total_seconds() * 1000
                    
                    return {
                        'outcome': 'win',
                        'exit_price': target_2_price,
                        'exit_time': row['timestamp'],
                        'pnl': target_2_price - entry_price,
                        'pnl_pct': target_2_pct,
                        'hold_time_ms': hold_time_ms,
                        'exit_latency_ms': np.random.normal(50, 15),
                        'settlement_lag_minutes': 0.5,
                        'exit_reason': 'target_2',
                        'dead_zone_ms': 0
                    }
                
                if row['last'] <= target_1_price:
                    # Returned to target 1 - exit with dead zone
                    hold_time_ms = (row['timestamp'] - entry_timestamp).total_seconds() * 1000
                    dead_zone_ms = (row['timestamp'] - target_1_timestamp).total_seconds() * 1000
                    
                    return {
                        'outcome': 'win',
                        'exit_price': target_1_price,
                        'exit_time': row['timestamp'],
                        'pnl': target_1_price - entry_price,
                        'pnl_pct': target_1_pct,
                        'hold_time_ms': hold_time_ms,
                        'exit_latency_ms': np.random.normal(50, 15),
                        'settlement_lag_minutes': 0.5,
                        'exit_reason': 'target_1_return',
                        'dead_zone_ms': dead_zone_ms
                    }
        
        # Timed out
        last_tick = future_ticks.iloc[-1]
        hold_time_ms = (last_tick['timestamp'] - entry_timestamp).total_seconds() * 1000
        
        return {
            'outcome': 'timeout',
            'exit_price': last_tick['last'],
            'exit_time': last_tick['timestamp'],
            'pnl': last_tick['last'] - entry_price,
            'pnl_pct': ((last_tick['last'] - entry_price) / entry_price) * 100,
            'hold_time_ms': hold_time_ms,
            'exit_latency_ms': np.random.normal(50, 15),
            'settlement_lag_minutes': 0.5,
            'exit_reason': 'timeout',
            'dead_zone_ms': 0
        }
    
    def _calculate_opportunity_cost(
        self,
        entry_price: float,
        dead_zone_minutes: float
    ) -> float:
        """
        Calculate opportunity cost of capital idle in dead zone.
        """
        hourly_expected_return = 0.005
        position_size = 3000
        opportunity_cost = position_size * hourly_expected_return * (dead_zone_minutes / 60)
        return opportunity_cost


# =============================================================================
# MAIN INTERFACE FUNCTION FOR MORNING REPORT (TICK DATA VERSION)
# =============================================================================

def analyze_vwap_patterns(
    tick_df: pd.DataFrame,
    decline_threshold: float = 1.0,
    entry_threshold: float = 1.5,
    target_1: float = 0.75,
    target_2: float = 2.0,
    stop_loss: float = 0.5,
    analysis_period_days: int = 20,
    aggregation_window_seconds: int = 5
) -> Dict:
    """
    Analyze VWAP recovery patterns using IBKR tick data.
    
    This is the main interface function used by morning_report.py.
    NOW SUPPORTS TRUE INTRAMINUTE (TICK-LEVEL) DATA FOR MILLISECOND PRECISION.
    
    Args:
        tick_df: DataFrame with tick data (timestamp, bid, ask, last, volume)
        decline_threshold: Minimum decline % to detect
        entry_threshold: % climb to confirm entry
        target_1: First profit target %
        target_2: Second profit target %
        stop_loss: Stop loss threshold %
        analysis_period_days: Number of days in analysis window
        aggregation_window_seconds: Window for aggregating ticks (default 5s)
    
    Returns:
        Dictionary with comprehensive pattern analysis and Priority 2 metrics
    """
    # Initialize detector with tick-level capabilities
    detector = PatternDetector(
        decline_threshold_pct=decline_threshold,
        entry_confirmation_pct=entry_threshold,
        target_1_pct=target_1,
        target_2_pct=target_2,
        stop_loss_pct=stop_loss,
        aggregation_window_seconds=aggregation_window_seconds
    )
    
    # Detect all patterns
    analysis_date = datetime.now()
    ticker = 'UNKNOWN'
    
    all_patterns = detector.detect_all_patterns(tick_df, ticker, analysis_date)
    
    # Separate patterns by outcome
    confirmed_entries = [p for p in all_patterns if p.get('entry_confirmed', False)]
    wins = [p for p in confirmed_entries if p.get('outcome') == 'win']
    losses = [p for p in confirmed_entries if p.get('outcome') == 'loss']
    
    # Calculate statistics
    total_patterns = len(all_patterns)
    total_confirmed = len(confirmed_entries)
    total_wins = len(wins)
    total_losses = len(losses)
    
    # Win/loss percentages
    avg_win_pct = np.mean([p.get('pnl_pct', 0) for p in wins]) if wins else 0
    avg_loss_pct = abs(np.mean([p.get('pnl_pct', 0) for p in losses])) if losses else stop_loss
    
    # Expected value calculation
    win_rate = total_wins / total_confirmed if total_confirmed > 0 else 0
    loss_rate = 1 - win_rate
    expected_value = (win_rate * avg_win_pct) - (loss_rate * avg_loss_pct)
    
    # Priority 2 Metrics: Pattern frequency and entry rate
    patterns_per_day = total_patterns / analysis_period_days if analysis_period_days > 0 else 0
    confirmation_rate = total_confirmed / total_patterns if total_patterns > 0 else 0
    expected_daily_entries = patterns_per_day * confirmation_rate
    
    # Signal frequency and success rate (20-day normalized)
    signal_frequency_20d = patterns_per_day
    signal_success_rate_20d = win_rate
    
    # Return comprehensive analysis
    return {
        # Lists for detailed analysis
        'all_patterns': all_patterns,
        'confirmed_entries': confirmed_entries,
        'wins': wins,
        'losses': losses,
        
        # Summary statistics
        'expected_value': expected_value,
        'avg_win_pct': avg_win_pct,
        'avg_loss_pct': avg_loss_pct,
        
        # Priority 2 Metrics
        'total_patterns_found': total_patterns,
        'confirmed_entries_count': total_confirmed,
        'patterns_per_day': patterns_per_day,
        'expected_daily_entries': expected_daily_entries,
        'signal_frequency_20d': signal_frequency_20d,
        'signal_success_rate_20d': signal_success_rate_20d,
        
        # Additional metrics
        'win_rate': win_rate,
        'confirmation_rate': confirmation_rate,
        'total_wins': total_wins,
        'total_losses': total_losses,
        
        # Intraminute metadata
        'data_source': 'ibkr_tick_data',
        'aggregation_window_seconds': aggregation_window_seconds
    }
