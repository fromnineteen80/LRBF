"""
VWAP Recovery Pattern Detector V2 - With Execution Cycle Tracking

Detects patterns AND tracks all timing components for execution cycle analysis.

Timing tracked per pattern:
- Pattern detection time (bars to confirmation)
- Entry execution latency (simulated order fill)
- Hold time (entry to exit)
- Exit execution latency (simulated liquidation)
- Settlement lag (cash back in account)
- Total cycle time (full round trip)

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
    Enhanced pattern detector with execution cycle tracking.
    """
    
    def __init__(
        self,
        decline_threshold_pct: float = 1.0,
        entry_confirmation_pct: float = 1.5,
        target_1_pct: float = 0.75,
        target_2_pct: float = 2.0,
        stop_loss_pct: float = 0.5,
        filter_engine: FilterEngine = None
    ):
        """
        Initialize pattern detector.
        
        Args:
            decline_threshold_pct: Minimum decline to detect (Step 1)
            entry_confirmation_pct: % climb to confirm entry
            target_1_pct: First profit target
            target_2_pct: Second profit target
            stop_loss_pct: Stop loss threshold
        """
        self.decline_threshold = decline_threshold_pct
        self.entry_confirmation = entry_confirmation_pct
        self.target_1 = target_1_pct
        self.target_2 = target_2_pct
        self.stop_loss = stop_loss_pct
        self.filter_engine = filter_engine
    
    def detect_all_patterns(
        self,
        df: pd.DataFrame,
        ticker: str,
        analysis_date: datetime
    ) -> List[Dict]:
        """
        Detect all VWAP recovery patterns in historical data.
        
        Args:
            df: DataFrame with OHLCV data (1-minute bars)
            ticker: Stock symbol
            analysis_date: Date of analysis
        
        Returns:
            List of pattern dictionaries with full timing data
        """
        if df.empty or len(df) < 50:
            return []
        
        patterns = []
        data_len = len(df)
        lookback_bars = 20
        
        # Ensure timestamp column
        if 'timestamp' not in df.columns and isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            df.rename(columns={'index': 'timestamp'}, inplace=True)
        
        # Scan for 3-step patterns
        for i in range(lookback_bars, data_len - 30):  # Leave room for confirmation
            
            # STEP 1: DECLINE
            recent_high = df['high'][i-lookback_bars:i+1].max()
            current_low = df['low'].iloc[i]
            
            decline_amount = recent_high - current_low
            decline_pct = (decline_amount / recent_high) * 100
            
            if decline_pct < self.decline_threshold:
                continue
            
            decline_bar_idx = i
            decline_timestamp = df['timestamp'].iloc[i]
            
            # STEP 2: 50% RECOVERY
            recovery_target = current_low + (decline_amount * 0.5)
            
            recovery_found = False
            for j in range(i+1, min(i+lookback_bars, data_len)):
                if df['high'].iloc[j] >= recovery_target:
                    recovery_high = df['high'].iloc[j]
                    recovery_bar_idx = j
                    recovery_timestamp = df['timestamp'].iloc[j]
                    recovery_amount = recovery_high - current_low
                    recovery_found = True
                    break
            
            if not recovery_found:
                continue
            
            # STEP 3: 50% RETRACEMENT
            retracement_target = recovery_high - (recovery_amount * 0.5)
            
            retracement_found = False
            for k in range(j+1, min(j+lookback_bars, data_len)):
                if df['low'].iloc[k] <= retracement_target:
                    last_low = df['low'].iloc[k]
                    pattern_complete_idx = k
                    pattern_complete_timestamp = df['timestamp'].iloc[k]
                    retracement_found = True
                    break
            
            if not retracement_found:
                continue
            
            # PATTERN COMPLETE - Track timing from here
            detection_time_bars = k - i  # Bars from decline to pattern complete
            
            # ENTRY CONFIRMATION
            entry_result = self._check_entry_confirmation(
                df[k:k+30],
                last_low,
                self.entry_confirmation
            )
            
            if not entry_result['confirmed']:
                # Pattern detected but no entry
                pattern = {
                    'pattern_id': f"{ticker}_{analysis_date.isoformat()}_{uuid.uuid4().hex[:8]}",
                    'ticker': ticker,
                    'date': analysis_date.isoformat(),
                    'timestamp': pattern_complete_timestamp,
                    'detection_time_bars': detection_time_bars,
                    'entry_confirmed': False,
                    'outcome': 'no_entry',
                    'failure_reason': entry_result.get('reason', 'no_confirmation')
                }
                patterns.append(pattern)
                continue
            
            # === FILTER CHECK ===
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
                    market_data=df,
                    current_time=entry_result['entry_timestamp']
                )
                
                if not filter_passed:
                    # Pattern detected and confirmed, but blocked by filters
                    pattern = {
                        'pattern_id': f"{ticker}_{analysis_date.isoformat()}_{uuid.uuid4().hex[:8]}",
                        'ticker': ticker,
                        'date': analysis_date.isoformat(),
                        'timestamp': pattern_complete_timestamp,
                        'detection_time_bars': detection_time_bars,
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
            
            # ENTRY CONFIRMED - Simulate trade execution
            entry_bar_idx = pattern_complete_idx + entry_result['bars_to_entry']
            entry_price = entry_result['entry_price']
            entry_timestamp = entry_result['entry_time']
            entry_latency_ms = np.random.normal(50, 15)  # Simulated latency
            
            # SIMULATE TRADE OUTCOME
            trade_result = self._simulate_trade_outcome(
                df[entry_bar_idx:],
                entry_price,
                self.target_1,
                self.target_2,
                self.stop_loss
            )
            
            # Calculate total cycle time
            total_cycle_minutes = (
                detection_time_bars +  # Pattern detection
                (entry_latency_ms / 1000 / 60) +  # Entry execution
                trade_result['hold_time_minutes'] +  # Hold time
                (trade_result['exit_latency_ms'] / 1000 / 60) +  # Exit execution
                trade_result['settlement_lag_minutes']  # Settlement
            )
            
            # Calculate dead zone if applicable
            dead_zone_duration = 0
            opportunity_cost = 0
            if trade_result['outcome'] == 'win' and trade_result.get('dead_zone_bars', 0) > 0:
                dead_zone_duration = trade_result['dead_zone_bars']
                opportunity_cost = self._calculate_opportunity_cost(
                    entry_price,
                    dead_zone_duration
                )
            
            # Build complete pattern record
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
                
                # Timing - Category #14 (Execution Cycle)
                'detection_time_bars': detection_time_bars,
                'entry_latency_ms': entry_latency_ms,
                'hold_time_minutes': trade_result['hold_time_minutes'],
                'exit_latency_ms': trade_result['exit_latency_ms'],
                'settlement_lag_minutes': trade_result['settlement_lag_minutes'],
                'total_cycle_minutes': total_cycle_minutes,
                
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
                'dead_zone_duration': dead_zone_duration,
                'opportunity_cost': opportunity_cost,
                
                # Additional metrics
                'bars_to_entry': entry_result['bars_to_entry'],
                'exit_reason': trade_result['exit_reason']
            }
            
            patterns.append(pattern)
        
        return patterns
    
    def _check_entry_confirmation(
        self,
        future_df: pd.DataFrame,
        last_low: float,
        confirmation_pct: float
    ) -> Dict:
        """
        Check if price climbs enough to confirm entry.
        
        Args:
            future_df: Price data after pattern completion
            last_low: Pattern completion price
            confirmation_pct: % climb required
        
        Returns:
            Dict with confirmation status
        """
        if future_df.empty:
            return {'confirmed': False, 'reason': 'no_data'}
        
        confirmation_target = last_low * (1 + confirmation_pct / 100)
        
        for idx, row in future_df.iterrows():
            if row['high'] >= confirmation_target:
                return {
                    'confirmed': True,
                    'entry_price': confirmation_target,
                    'entry_time': row['timestamp'],
                    'bars_to_entry': idx - future_df.index[0]
                }
        
        return {'confirmed': False, 'reason': 'no_confirmation'}
    
    def _simulate_trade_outcome(
        self,
        future_df: pd.DataFrame,
        entry_price: float,
        target_1_pct: float,
        target_2_pct: float,
        stop_loss_pct: float
    ) -> Dict:
        """
        Simulate trade from entry to exit.
        
        Args:
            future_df: Price data after entry
            entry_price: Entry price
            target_1_pct: First profit target %
            target_2_pct: Second profit target %
            stop_loss_pct: Stop loss %
        
        Returns:
            Dict with trade outcome and timing
        """
        target_1_price = entry_price * (1 + target_1_pct / 100)
        target_2_price = entry_price * (1 + target_2_pct / 100)
        stop_price = entry_price * (1 - stop_loss_pct / 100)
        
        hit_target_1 = False
        dead_zone_bars = 0
        
        for idx, row in future_df.iterrows():
            bars_held = idx - future_df.index[0]
            
            # Check stop loss
            if row['low'] <= stop_price:
                return {
                    'outcome': 'loss',
                    'exit_price': stop_price,
                    'exit_time': row['timestamp'],
                    'pnl': stop_price - entry_price,
                    'pnl_pct': -stop_loss_pct,
                    'hold_time_minutes': bars_held,
                    'exit_latency_ms': np.random.normal(55, 15),
                    'settlement_lag_minutes': 0.5,
                    'exit_reason': 'stop_loss',
                    'dead_zone_bars': 0
                }
            
            # Check target 1
            if not hit_target_1 and row['high'] >= target_1_price:
                hit_target_1 = True
                target_1_bar = bars_held
            
            # If hit target 1, look for target 2 or return to target 1
            if hit_target_1:
                if row['high'] >= target_2_price:
                    # Hit target 2 - exit
                    return {
                        'outcome': 'win',
                        'exit_price': target_2_price,
                        'exit_time': row['timestamp'],
                        'pnl': target_2_price - entry_price,
                        'pnl_pct': target_2_pct,
                        'hold_time_minutes': bars_held,
                        'exit_latency_ms': np.random.normal(50, 15),
                        'settlement_lag_minutes': 0.5,
                        'exit_reason': 'target_2',
                        'dead_zone_bars': 0  # No dead zone on target 2
                    }
                
                if row['low'] <= target_1_price:
                    # Returned to target 1 - exit with dead zone
                    dead_zone_bars = bars_held - target_1_bar
                    return {
                        'outcome': 'win',
                        'exit_price': target_1_price,
                        'exit_time': row['timestamp'],
                        'pnl': target_1_price - entry_price,
                        'pnl_pct': target_1_pct,
                        'hold_time_minutes': bars_held,
                        'exit_latency_ms': np.random.normal(50, 15),
                        'settlement_lag_minutes': 0.5,
                        'exit_reason': 'target_1_return',
                        'dead_zone_bars': dead_zone_bars
                    }
        
        # Timed out (shouldn't happen with intraday, but safety)
        return {
            'outcome': 'timeout',
            'exit_price': future_df['close'].iloc[-1],
            'exit_time': future_df['timestamp'].iloc[-1],
            'pnl': future_df['close'].iloc[-1] - entry_price,
            'pnl_pct': ((future_df['close'].iloc[-1] - entry_price) / entry_price) * 100,
            'hold_time_minutes': len(future_df),
            'exit_latency_ms': np.random.normal(50, 15),
            'settlement_lag_minutes': 0.5,
            'exit_reason': 'timeout',
            'dead_zone_bars': 0
        }
    
    def _calculate_opportunity_cost(
        self,
        entry_price: float,
        dead_zone_minutes: int
    ) -> float:
        """
        Calculate opportunity cost of capital idle in dead zone.
        
        Args:
            entry_price: Trade entry price
            dead_zone_minutes: Minutes capital was idle
        
        Returns:
            Opportunity cost in dollars
        """
        # Assume 0.5% expected return per hour
        hourly_expected_return = 0.005
        position_size = 3000  # Typical position size
        
        opportunity_cost = position_size * hourly_expected_return * (dead_zone_minutes / 60)
        return opportunity_cost


# Convenience function for batch analysis
def detect_patterns_batch(
    df: pd.DataFrame,
    ticker: str,
    analysis_date: datetime
) -> List[Dict]:
    """
    Detect all patterns for a stock (convenience wrapper).
    
    Args:
        df: OHLCV DataFrame
        ticker: Stock symbol
        analysis_date: Analysis date
    
    Returns:
        List of pattern dictionaries
    """
    detector = PatternDetector()
    return detector.detect_all_patterns(df, ticker, analysis_date)


# =============================================================================
# MAIN INTERFACE FUNCTION FOR MORNING REPORT
# =============================================================================

def analyze_vwap_patterns(
    df: pd.DataFrame,
    decline_threshold: float = 1.0,
    entry_threshold: float = 1.5,
    target_1: float = 0.75,
    target_2: float = 2.0,
    stop_loss: float = 0.5,
    analysis_period_days: int = 20
) -> Dict:
    """
    Analyze VWAP recovery patterns and return comprehensive statistics.
    
    This is the main interface function used by morning_report.py.
    
    Args:
        df: DataFrame with OHLCV data (1-minute bars)
        decline_threshold: Minimum decline % to detect (Step 1)
        entry_threshold: % climb to confirm entry
        target_1: First profit target %
        target_2: Second profit target %
        stop_loss: Stop loss threshold %
        analysis_period_days: Number of days in analysis window (default 20)
    
    Returns:
        Dictionary with:
        - all_patterns: List of all detected patterns
        - confirmed_entries: List of patterns with entry confirmation
        - wins: List of winning trades
        - losses: List of losing trades
        - expected_value: Expected value per trade
        - avg_win_pct: Average win percentage
        - avg_loss_pct: Average loss percentage
        - total_patterns_found: Total patterns detected (Priority 2 ✅)
        - confirmed_entries_count: Number of confirmed entries (Priority 2 ✅)
        - patterns_per_day: Average patterns per day (Priority 2 ✅)
        - expected_daily_entries: Expected entries per day (Priority 2 ✅)
        - signal_frequency_20d: Signal frequency over 20 days (Priority 2 ✅)
        - signal_success_rate_20d: Success rate over 20 days (Priority 2 ✅)
    """
    from datetime import datetime
    
    # Initialize detector with specified parameters
    detector = PatternDetector(
        decline_threshold_pct=decline_threshold,
        entry_confirmation_pct=entry_threshold,
        target_1_pct=target_1,
        target_2_pct=target_2,
        stop_loss_pct=stop_loss
    )
    
    # Detect all patterns
    analysis_date = datetime.now()
    ticker = 'UNKNOWN'  # Will be set by caller if needed
    
    all_patterns = detector.detect_all_patterns(df, ticker, analysis_date)
    
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
    avg_win_pct = np.mean([p.get('profit_pct', 0) for p in wins]) if wins else 0
    avg_loss_pct = abs(np.mean([p.get('profit_pct', 0) for p in losses])) if losses else stop_loss
    
    # Expected value calculation
    win_rate = total_wins / total_confirmed if total_confirmed > 0 else 0
    loss_rate = 1 - win_rate
    expected_value = (win_rate * avg_win_pct) - (loss_rate * avg_loss_pct)
    
    # Priority 2 Metrics: Pattern frequency and entry rate
    patterns_per_day = total_patterns / analysis_period_days if analysis_period_days > 0 else 0
    confirmation_rate = total_confirmed / total_patterns if total_patterns > 0 else 0
    expected_daily_entries = patterns_per_day * confirmation_rate
    
    # Signal frequency and success rate (20-day normalized)
    signal_frequency_20d = patterns_per_day  # Same as patterns_per_day
    signal_success_rate_20d = win_rate  # Same as win_rate
    
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
        
        # Priority 2 Metrics (NEW)
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
        'total_losses': total_losses
    }
