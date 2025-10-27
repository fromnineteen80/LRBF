"""
VWAP Breakout Strategy - Pattern Detection

Strategy 2: Detects price crossing back above VWAP after dropping below.

Pattern Steps:
1. Price drops BELOW VWAP
2. Price stabilizes near/under VWAP for confirmation (2-5 minutes)
3. Price crosses BACK ABOVE VWAP (the breakout)
4. Entry signal: Price climbs +0.5% above VWAP with volume confirmation

Different from 3-Step Geometric which ignores VWAP position.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


def detect_vwap_breakout_patterns(
    df: pd.DataFrame,
    config: Dict
) -> Dict:
    """
    Detect VWAP breakout patterns in historical data.
    
    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume, vwap]
        config: Trading configuration
    
    Returns:
        Dictionary with pattern analysis:
        {
            'total_patterns': int,
            'confirmed_entries': int,
            'win_rate': float,
            'avg_win_pct': float,
            'avg_loss_pct': float,
            'expected_daily_patterns': float,
            'expected_daily_pl': float,
            'patterns': List[Dict]  # Individual pattern details
        }
    """
    if df is None or df.empty or 'vwap' not in df.columns:
        return _empty_result()
    
    patterns = []
    i = 0
    
    while i < len(df) - 10:  # Need at least 10 bars ahead
        # STEP 1: Find price drop below VWAP
        if df.iloc[i]['close'] < df.iloc[i]['vwap']:
            below_start = i
            
            # STEP 2: Confirm stabilization (price stays below/near VWAP for 2-5 bars)
            stabilization_bars = 0
            j = i + 1
            
            while j < len(df) - 5 and stabilization_bars < 5:
                if df.iloc[j]['close'] <= df.iloc[j]['vwap'] * 1.003:  # Within 0.3% of VWAP
                    stabilization_bars += 1
                    j += 1
                else:
                    break
            
            # Need at least 2 bars of stabilization
            if stabilization_bars >= 2:
                # STEP 3: Find breakout (price crosses back above VWAP)
                breakout_idx = None
                
                for k in range(j, min(j + 10, len(df))):
                    if df.iloc[k]['close'] > df.iloc[k]['vwap']:
                        breakout_idx = k
                        break
                
                if breakout_idx:
                    # STEP 4: Check for entry signal (+0.5% above VWAP with volume)
                    vwap_price = df.iloc[breakout_idx]['vwap']
                    entry_threshold = vwap_price * 1.005  # 0.5% above VWAP
                    
                    entry_idx = None
                    entry_price = None
                    
                    for m in range(breakout_idx, min(breakout_idx + 5, len(df))):
                        if df.iloc[m]['close'] >= entry_threshold:
                            # Check volume confirmation (2x recent average)
                            recent_vol = df.iloc[max(0, m-20):m]['volume'].mean()
                            if df.iloc[m]['volume'] >= recent_vol * 1.5:
                                entry_idx = m
                                entry_price = df.iloc[m]['close']
                                break
                    
                    if entry_idx and entry_price:
                        # Pattern found! Record it
                        pattern = {
                            'below_start_idx': below_start,
                            'stabilization_bars': stabilization_bars,
                            'breakout_idx': breakout_idx,
                            'entry_idx': entry_idx,
                            'entry_price': entry_price,
                            'vwap_at_entry': df.iloc[entry_idx]['vwap'],
                            'entry_confirmed': True
                        }
                        
                        # Simulate trade outcome
                        outcome = _simulate_vwap_trade(df, entry_idx, entry_price, config)
                        pattern.update(outcome)
                        
                        patterns.append(pattern)
                        i = entry_idx + 1  # Move past this pattern
                        continue
        
        i += 1
    
    # Calculate aggregate statistics
    return _calculate_vwap_statistics(patterns, len(df))


def _simulate_vwap_trade(
    df: pd.DataFrame,
    entry_idx: int,
    entry_price: float,
    config: Dict
) -> Dict:
    """
    Simulate trade outcome using universal exit rules.
    
    Exit Rules (same as 3-Step):
    - Target 1 (T1): +0.75% from entry
    - Target 2 (T2): +1.75% from entry
    - Stop Loss: -0.5% from entry
    - Deadzone: 8-minute timeout in ±0.6% range
    """
    target1 = entry_price * (1 + 0.0075)  # +0.75%
    target2 = entry_price * (1 + 0.0175)  # +1.75%
    stop_loss = entry_price * (1 - 0.005)  # -0.5%
    
    deadzone_minutes = 0
    deadzone_threshold = entry_price * 0.006  # ±0.6%
    
    for i in range(entry_idx + 1, min(entry_idx + 60, len(df))):  # Max 60 bars
        current_price = df.iloc[i]['close']
        
        # Check stop loss
        if current_price <= stop_loss:
            return {
                'exit_reason': 'StopLoss',
                'exit_price': stop_loss,
                'pnl_pct': -0.5,
                'bars_held': i - entry_idx,
                'winner': False
            }
        
        # Check Target 2 first
        if current_price >= target2:
            # Wait for +1.00% exit or return to T1
            for j in range(i, min(i + 10, len(df))):
                if df.iloc[j]['close'] >= entry_price * 1.01:
                    return {
                        'exit_reason': 'Target2',
                        'exit_price': entry_price * 1.01,
                        'pnl_pct': 1.0,
                        'bars_held': j - entry_idx,
                        'winner': True
                    }
                elif df.iloc[j]['close'] <= target1:
                    return {
                        'exit_reason': 'Target1',
                        'exit_price': target1,
                        'pnl_pct': 0.75,
                        'bars_held': j - entry_idx,
                        'winner': True
                    }
        
        # Check Target 1
        if current_price >= target1:
            deadzone_minutes = 0  # Reset deadzone if making progress
        
        # Check deadzone
        if abs(current_price - entry_price) <= deadzone_threshold:
            deadzone_minutes += 1
            if deadzone_minutes >= 8:
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                return {
                    'exit_reason': 'DeadZone',
                    'exit_price': current_price,
                    'pnl_pct': pnl_pct,
                    'bars_held': i - entry_idx,
                    'winner': pnl_pct > 0
                }
        else:
            deadzone_minutes = 0
    
    # Timeout (60 bars = ~1 hour)
    final_price = df.iloc[min(entry_idx + 60, len(df) - 1)]['close']
    pnl_pct = ((final_price - entry_price) / entry_price) * 100
    
    return {
        'exit_reason': 'TimeOut',
        'exit_price': final_price,
        'pnl_pct': pnl_pct,
        'bars_held': 60,
        'winner': pnl_pct > 0
    }


def _calculate_vwap_statistics(patterns: List[Dict], total_bars: int) -> Dict:
    """Calculate aggregate statistics from patterns."""
    if not patterns:
        return _empty_result()
    
    winners = [p for p in patterns if p.get('winner', False)]
    losers = [p for p in patterns if not p.get('winner', False)]
    
    total_patterns = len(patterns)
    win_rate = len(winners) / total_patterns if total_patterns > 0 else 0
    
    avg_win_pct = np.mean([p['pnl_pct'] for p in winners]) if winners else 0
    avg_loss_pct = np.mean([p['pnl_pct'] for p in losers]) if losers else 0
    
    # Calculate expected daily values
    bars_per_day = 390  # Market hours: 6.5 hours * 60 minutes
    days_in_sample = total_bars / bars_per_day
    
    expected_daily_patterns = total_patterns / days_in_sample if days_in_sample > 0 else 0
    confirmed_entries = total_patterns  # All patterns that reached entry signal
    
    # Expected daily P&L (per position)
    expected_value = (win_rate * avg_win_pct) - ((1 - win_rate) * abs(avg_loss_pct))
    expected_daily_pl = expected_daily_patterns * expected_value
    
    return {
        'total_patterns': total_patterns,
        'confirmed_entries': confirmed_entries,
        'win_rate': win_rate,
        'avg_win_pct': avg_win_pct,
        'avg_loss_pct': avg_loss_pct,
        'expected_daily_patterns': expected_daily_patterns,
        'expected_daily_pl': expected_daily_pl,
        'patterns': patterns
    }


def _empty_result() -> Dict:
    """Return empty result when no patterns found."""
    return {
        'total_patterns': 0,
        'confirmed_entries': 0,
        'win_rate': 0.0,
        'avg_win_pct': 0.0,
        'avg_loss_pct': 0.0,
        'expected_daily_patterns': 0.0,
        'expected_daily_pl': 0.0,
        'patterns': []
    }


# Convenience function matching pattern_detector interface
def analyze_vwap_breakout_patterns(ticker: str, df: pd.DataFrame, config: Dict) -> Dict:
    """
    Wrapper function matching the pattern_detector interface.
    
    Args:
        ticker: Stock symbol
        df: DataFrame with OHLCV + VWAP
        config: Trading configuration
    
    Returns:
        Dictionary with pattern analysis
    """
    result = detect_vwap_breakout_patterns(df, config)
    result['ticker'] = ticker
    return result
