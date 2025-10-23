"""
VWAP Recovery Pattern Detector

This module detects VWAP Recovery Patterns in price data - a 3-step geometry that
predicts short-term mean reversions:

Step 1: DECLINE - Price drops from recent high
Step 2: 50% RECOVERY - Price rebounds by 50% of decline
Step 3: 50% RETRACEMENT - Price pulls back by 50% of recovery

After pattern completes, we check for entry confirmation from config.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
sys.path.append('/home/claude/railyard')

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config import TradingConfig as cfg


def detect_vwap_recovery_patterns(
    price_data: pd.DataFrame,
    decline_threshold_pct: float = None,
    entry_confirmation_pct: float = None,
    lookback_bars: int = 20,
    lookahead_bars: int = 30
) -> List[Dict]:
    """
    Scan 1-minute price data for VWAP Recovery Patterns.
    
    Args:
        price_data: DataFrame with columns [timestamp, open, high, low, close, volume]
                   Index should be DatetimeIndex or include timestamp column
        decline_threshold_pct: Minimum decline % to consider (default from config)
        entry_confirmation_pct: % climb required to confirm entry (default from config)
        lookback_bars: Bars to look back for recent high (default 20)
        lookahead_bars: Max bars to wait for entry confirmation (default 30)
    
    Returns:
        List of pattern dictionaries with detection details
    
    Example:
        >>> patterns = detect_vwap_recovery_patterns(price_data)
        >>> print(f"Found {len(patterns)} patterns")
        >>> for p in patterns:
        >>>     if p['entry_confirmed']:
        >>>         print(f"Pattern at {p['pattern_complete_time']}, entry at {p['entry_price']}")
    """
    
    # Use config defaults if not specified
    if decline_threshold_pct is None:
        decline_threshold_pct = cfg.DECLINE_THRESHOLD
    if entry_confirmation_pct is None:
        entry_confirmation_pct = cfg.ENTRY_THRESHOLD
    
    # Validate input data
    if price_data.empty:
        return []
    
    required_cols = ['close', 'high', 'low']
    if not all(col in price_data.columns for col in required_cols):
        raise ValueError(f"price_data must contain columns: {required_cols}")
    
    # Ensure we have a timestamp column or index
    if 'timestamp' not in price_data.columns:
        if isinstance(price_data.index, pd.DatetimeIndex):
            price_data = price_data.reset_index()
            price_data.columns = ['timestamp'] + list(price_data.columns[1:])
        else:
            raise ValueError("price_data must have timestamp column or DatetimeIndex")
    
    patterns = []
    data_len = len(price_data)
    
    # Need at least lookback_bars to find patterns
    if data_len < lookback_bars:
        return []
    
    # Scan through price data looking for the 3-step pattern
    for i in range(lookback_bars, data_len):
        
        # Step 1: Find DECLINE from recent high
        # Look at the high values in the lookback window AND current bar
        recent_high_lookback = price_data['high'][i-lookback_bars:i].max()
        current_high = price_data['high'].iloc[i]
        recent_high = max(recent_high_lookback, current_high)
        
        # Current low as potential decline point
        current_low = price_data['low'].iloc[i]
        
        decline_amount = recent_high - current_low
        decline_pct = (decline_amount / recent_high) * 100
        
        # Must meet minimum decline threshold
        if decline_pct < decline_threshold_pct:
            continue
        
        # Record the decline low
        decline_low = current_low
        decline_index = i
        decline_time = price_data['timestamp'].iloc[i]
        
        # Step 2: Look ahead for 50% RECOVERY
        recovery_target = decline_low + (decline_amount * 0.5)
        
        for j in range(i+1, min(i+lookback_bars+1, data_len)):
            price_high_j = price_data['high'].iloc[j]
            
            # Check if we've hit the 50% recovery target
            if price_high_j >= recovery_target:
                recovery_high = price_high_j
                recovery_amount = recovery_high - decline_low
                recovery_index = j
                recovery_time = price_data['timestamp'].iloc[j]
                
                # Step 3: Look ahead for 50% RETRACEMENT
                retracement_target = recovery_high - (recovery_amount * 0.5)
                
                for k in range(j+1, min(j+lookback_bars+1, data_len)):
                    price_low_k = price_data['low'].iloc[k]
                    
                    # Check if we've hit the 50% retracement
                    if price_low_k <= retracement_target:
                        last_low = price_low_k
                        pattern_complete_index = k
                        pattern_complete_time = price_data['timestamp'].iloc[k]
                        
                        # Pattern is complete! Now check for entry confirmation
                        entry_result = check_entry_confirmation(
                            price_data[k:],
                            last_low=last_low,
                            confirmation_pct=entry_confirmation_pct,
                            max_bars=lookahead_bars
                        )
                        
                        # Store the pattern
                        pattern = {
                            'pattern_complete_time': pattern_complete_time,
                            'pattern_complete_index': k,
                            'decline_start_index': decline_index - lookback_bars,
                            'decline_low_index': decline_index,
                            'recovery_high_index': recovery_index,
                            'recent_high': recent_high,
                            'decline_low': decline_low,
                            'decline_amount': decline_amount,
                            'decline_pct': decline_pct,
                            'recovery_high': recovery_high,
                            'recovery_amount': recovery_amount,
                            'last_low': last_low,
                            'entry_confirmed': entry_result['confirmed'],
                            'entry_price': entry_result.get('entry_price'),
                            'entry_time': entry_result.get('entry_time'),
                            'entry_index': entry_result.get('entry_index'),
                            'bars_to_entry': entry_result.get('bars_to_entry'),
                            'failure_reason': entry_result.get('reason')
                        }
                        
                        patterns.append(pattern)
                        
                        # Move past this pattern to avoid overlaps
                        break
                
                # If we found a retracement, move to next potential pattern
                break
    
    return patterns


def check_entry_confirmation(
    future_prices: pd.DataFrame,
    last_low: float,
    confirmation_pct: float = 1.5,  # OPTIMIZED: Changed from 2.0% to 1.5%
    max_bars: int = 30
) -> Dict:
    """
    After pattern completes at last_low, check if price climbs to confirm entry.
    
    Args:
        future_prices: Price data after pattern completion
        last_low: The last low price (pattern completion price)
        confirmation_pct: % climb required to confirm (default 2.0%)
        max_bars: Maximum bars to wait for confirmation (default 30)
    
    Returns:
        Dict with confirmation status and details
        
    Example:
        >>> result = check_entry_confirmation(future_data, last_low=99.25, confirmation_pct=2.0)
        >>> if result['confirmed']:
        >>>     print(f"Entry at {result['entry_price']}")
    """
    
    if future_prices.empty:
        return {
            'confirmed': False,
            'reason': 'no_future_data'
        }
    
    # Calculate entry trigger price (+2% from last low)
    entry_trigger = last_low * (1 + confirmation_pct / 100)
    
    # Calculate stop threshold (-0.5% from last low = pattern failure)
    stop_threshold = last_low * 0.995
    
    # Look ahead for confirmation or failure
    max_look = min(max_bars, len(future_prices))
    
    for i in range(max_look):
        price = future_prices['close'].iloc[i]
        
        # Pattern failed - price dropped too much
        if price < stop_threshold:
            return {
                'confirmed': False,
                'reason': 'pattern_failed',
                'failed_at': future_prices['timestamp'].iloc[i] if 'timestamp' in future_prices.columns else None,
                'lowest_price': price
            }
        
        # Entry confirmed - price climbed required %
        if price >= entry_trigger:
            return {
                'confirmed': True,
                'entry_price': price,
                'entry_time': future_prices['timestamp'].iloc[i] if 'timestamp' in future_prices.columns else None,
                'entry_index': i,
                'bars_to_entry': i
            }
    
    # Pattern didn't confirm or fail within time limit
    max_price = future_prices['close'][:max_look].max()
    return {
        'confirmed': False,
        'reason': 'timeout',
        'max_price_reached': max_price,
        'trigger_needed': entry_trigger
    }


def simulate_trade_outcome(
    entry_price: float,
    future_prices: pd.DataFrame,
    target_1_pct: float = None,
    target_2_pct: float = None,
    stop_loss_pct: float = None
) -> Dict:
    """
    Simulate trade outcome using X then X+ exit rules.
    
    Exit Rules (X then X+):
    1. If price hits Target 1, WAIT
    2. If price then hits Target 2, exit at Target 2
    3. If price returns to Target 1 after hitting it, exit at Target 1
    4. If price hits Stop Loss at any time, exit immediately
    
    Args:
        entry_price: Price at which position was entered
        future_prices: Price data after entry
        target_1_pct: First target % (default from config)
        target_2_pct: Second target % (default from config)
        stop_loss_pct: Stop loss % (default from config)
    
    Returns:
        Dict with trade outcome details
        
    Example:
        >>> outcome = simulate_trade_outcome(entry_price=101.24, future_data)
        >>> if outcome['outcome'] == 'win':
        >>>     print(f"Profit: {outcome['profit_pct']}%")
    """
    
    # Use config defaults if not specified
    if target_1_pct is None:
        target_1_pct = cfg.TARGET_1
    if target_2_pct is None:
        target_2_pct = cfg.TARGET_2
    if stop_loss_pct is None:
        stop_loss_pct = cfg.STOP_LOSS
    
    if future_prices.empty:
        return {
            'outcome': 'no_data',
            'exit_reason': 'no_future_data'
        }
    
    # Calculate price targets
    target_075 = entry_price * (1 + target_1_pct / 100)
    target_2 = entry_price * (1 + target_2_pct / 100)
    stop_loss = entry_price * (1 + stop_loss_pct / 100)
    
    hit_075 = False  # Track if we've hit first target
    
    # Simulate each bar after entry
    for i in range(len(future_prices)):
        high = future_prices['high'].iloc[i]
        low = future_prices['low'].iloc[i]
        close = future_prices['close'].iloc[i]
        
        # Check stop loss FIRST (highest priority)
        if low <= stop_loss:
            return {
                'outcome': 'loss',
                'exit_price': stop_loss,
                'profit_pct': stop_loss_pct,
                'profit_dollars': None,  # Will be calculated with position size
                'exit_reason': 'stop_loss',
                'bars_held': i,
                'exit_time': future_prices['timestamp'].iloc[i] if 'timestamp' in future_prices.columns else None
            }
        
        # Check if we hit first target
        if high >= target_075 and not hit_075:
            hit_075 = True
        
        # Check if we hit second target
        if high >= target_2:
            return {
                'outcome': 'win',
                'exit_price': target_2,
                'profit_pct': target_2_pct,
                'profit_dollars': None,
                'exit_reason': 'target_2',
                'bars_held': i,
                'exit_time': future_prices['timestamp'].iloc[i] if 'timestamp' in future_prices.columns else None
            }
        
        # If we hit first target and price returns to it, exit
        if hit_075 and close <= target_075:
            return {
                'outcome': 'win',
                'exit_price': target_075,
                'profit_pct': target_1_pct,
                'profit_dollars': None,
                'exit_reason': 'target_1_return',
                'bars_held': i,
                'exit_time': future_prices['timestamp'].iloc[i] if 'timestamp' in future_prices.columns else None
            }
    
    # End of data - calculate final P&L based on last close
    last_price = future_prices['close'].iloc[-1]
    profit_pct = ((last_price - entry_price) / entry_price) * 100
    
    if profit_pct >= target_1_pct:
        outcome = 'win'
        exit_reason = 'eod_win'
    else:
        outcome = 'loss'
        exit_reason = 'eod_loss'
    
    return {
        'outcome': outcome,
        'exit_price': last_price,
        'profit_pct': profit_pct,
        'profit_dollars': None,
        'exit_reason': exit_reason,
        'bars_held': len(future_prices),
        'exit_time': future_prices['timestamp'].iloc[-1] if 'timestamp' in future_prices.columns else None
    }


def analyze_patterns_with_outcomes(
    price_data: pd.DataFrame,
    **kwargs
) -> pd.DataFrame:
    """
    Detect patterns and simulate all trades, returning comprehensive DataFrame.
    
    This is a convenience function that:
    1. Detects all VWAP Recovery Patterns
    2. For confirmed entries, simulates the trade outcome
    3. Returns everything in a pandas DataFrame for analysis
    
    Args:
        price_data: Price DataFrame
        **kwargs: Additional arguments passed to detect_vwap_recovery_patterns
    
    Returns:
        DataFrame with columns for pattern details and trade outcomes
        
    Example:
        >>> results = analyze_patterns_with_outcomes(aapl_data)
        >>> print(f"Win rate: {results['outcome'].value_counts(normalize=True)}")
        >>> print(f"Avg profit: {results[results['outcome']=='win']['profit_pct'].mean()}")
    """
    
    # Detect all patterns
    patterns = detect_vwap_recovery_patterns(price_data, **kwargs)
    
    if not patterns:
        return pd.DataFrame()
    
    # For each confirmed entry, simulate the trade
    results = []
    
    for pattern in patterns:
        result = pattern.copy()
        
        if pattern['entry_confirmed']:
            # Get price data after entry
            entry_index = pattern['pattern_complete_index'] + pattern['bars_to_entry']
            future_data = price_data.iloc[entry_index+1:]
            
            if not future_data.empty:
                # Simulate the trade
                trade_outcome = simulate_trade_outcome(
                    entry_price=pattern['entry_price'],
                    future_prices=future_data
                )
                
                # Merge trade outcome into result
                result.update(trade_outcome)
        
        results.append(result)
    
    return pd.DataFrame(results)


# Utility functions for analysis

def calculate_win_rate(outcomes_df: pd.DataFrame) -> float:
    """Calculate win rate from outcomes DataFrame."""
    if outcomes_df.empty or 'outcome' not in outcomes_df.columns:
        return 0.0
    
    confirmed_entries = outcomes_df[outcomes_df['entry_confirmed'] == True]
    if confirmed_entries.empty:
        return 0.0
    
    wins = (confirmed_entries['outcome'] == 'win').sum()
    total = len(confirmed_entries)
    
    return wins / total if total > 0 else 0.0


def calculate_avg_profit_loss(outcomes_df: pd.DataFrame) -> Dict[str, float]:
    """Calculate average profit and loss from outcomes DataFrame."""
    if outcomes_df.empty or 'profit_pct' not in outcomes_df.columns:
        return {'avg_win': 0.0, 'avg_loss': 0.0}
    
    confirmed = outcomes_df[outcomes_df['entry_confirmed'] == True]
    
    if confirmed.empty:
        return {'avg_win': 0.0, 'avg_loss': 0.0}
    
    wins = confirmed[confirmed['outcome'] == 'win']['profit_pct']
    losses = confirmed[confirmed['outcome'] == 'loss']['profit_pct']
    
    return {
        'avg_win': wins.mean() if not wins.empty else 0.0,
        'avg_loss': losses.mean() if not losses.empty else 0.0
    }


def get_pattern_summary(outcomes_df: pd.DataFrame) -> Dict:
    """
    Generate summary statistics from pattern analysis.
    
    Returns:
        Dict with key metrics for stock evaluation
    """
    if outcomes_df.empty:
        return {
            'total_patterns': 0,
            'confirmed_entries': 0,
            'confirmation_rate': 0.0,
            'win_rate': 0.0,
            'wins': 0,
            'losses': 0,
            'avg_win_pct': 0.0,
            'avg_loss_pct': 0.0
        }
    
    total_patterns = len(outcomes_df)
    confirmed_entries = outcomes_df['entry_confirmed'].sum()
    confirmation_rate = confirmed_entries / total_patterns if total_patterns > 0 else 0.0
    
    confirmed = outcomes_df[outcomes_df['entry_confirmed'] == True]
    
    # Check if we have outcome column (only present if trades were simulated)
    if 'outcome' not in confirmed.columns or confirmed.empty:
        return {
            'total_patterns': total_patterns,
            'confirmed_entries': int(confirmed_entries),
            'confirmation_rate': confirmation_rate,
            'win_rate': 0.0,
            'wins': 0,
            'losses': 0,
            'avg_win_pct': 0.0,
            'avg_loss_pct': 0.0
        }
    
    wins = (confirmed['outcome'] == 'win').sum()
    losses = (confirmed['outcome'] == 'loss').sum()
    
    win_rate = wins / confirmed_entries if confirmed_entries > 0 else 0.0
    
    profit_loss = calculate_avg_profit_loss(outcomes_df)
    
    return {
        'total_patterns': total_patterns,
        'confirmed_entries': int(confirmed_entries),
        'confirmation_rate': confirmation_rate,
        'win_rate': win_rate,
        'wins': int(wins),
        'losses': int(losses),
        'avg_win_pct': profit_loss['avg_win'],
        'avg_loss_pct': profit_loss['avg_loss']
    }


if __name__ == "__main__":
    print("VWAP Recovery Pattern Detector Module")
    print("=" * 50)
    print("This module provides pattern detection and trade simulation.")
    print("\nKey functions:")
    print("  - detect_vwap_recovery_patterns(): Find patterns in price data")
    print("  - simulate_trade_outcome(): Simulate X then X+ exit rules")
    print("  - analyze_patterns_with_outcomes(): Complete analysis pipeline")
    print("\nSee function docstrings for usage examples.")
