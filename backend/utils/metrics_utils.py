"""
Technical Metrics Utilities

Calculates technical indicators used for adaptive strategy parameters:
- ATR (Average True Range) for volatility-based threshold adjustment
- VWAP stability metrics
- Volume analysis

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import pandas as pd
import numpy as np
from typing import Dict


def calculate_atr(price_data: pd.DataFrame, period: int = 14) -> float:
    """
    Calculate Average True Range (ATR) - a volatility indicator.
    
    ATR measures stock volatility by analyzing the range of price movement.
    Used to calculate adaptive confirmation thresholds:
    - Low ATR (< 2%) = low volatility = lower threshold (0.5%)
    - High ATR (> 4%) = high volatility = higher threshold (1.0%)
    
    Args:
        price_data: DataFrame with columns [high, low, close]
        period: Lookback period for ATR calculation (default: 14)
    
    Returns:
        ATR value as percentage of price
        
    Example:
        >>> atr = calculate_atr(price_data, period=14)
        >>> if atr < 0.02:
        >>>     print("Low volatility stock")
        >>> elif atr > 0.04:
        >>>     print("High volatility stock")
    """
    if price_data.empty or len(price_data) < period:
        return 0.02  # Default to 2% if insufficient data
    
    # Ensure we have required columns
    required_cols = ['high', 'low', 'close']
    if not all(col in price_data.columns for col in required_cols):
        return 0.02
    
    # Calculate True Range for each bar
    # TR = max(high - low, |high - prev_close|, |low - prev_close|)
    
    high = price_data['high']
    low = price_data['low']
    close = price_data['close']
    prev_close = close.shift(1)
    
    # Three components of True Range
    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)
    
    # True Range is the maximum of the three
    true_range = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
    
    # ATR is the moving average of True Range
    atr_values = true_range.rolling(window=period).mean()
    
    # Get the most recent ATR value
    current_atr = atr_values.iloc[-1]
    
    # Express as percentage of current price
    current_price = close.iloc[-1]
    atr_pct = (current_atr / current_price) if current_price > 0 else 0.02
    
    return atr_pct


def calculate_adaptive_confirmation_threshold(atr_pct: float, min_threshold: float = 0.5, max_threshold: float = 1.0) -> float:
    """
    Calculate adaptive confirmation threshold based on ATR.
    
    Formula: confirmation_threshold = max(min, min(max, ATR * 0.5))
    
    This ensures:
    - Low volatility stocks (ATR < 1%) get 0.5% threshold
    - Medium volatility (ATR 1-2%) get 0.5-1.0% threshold  
    - High volatility (ATR > 2%) get 1.0% threshold (capped)
    
    Args:
        atr_pct: ATR as percentage (e.g., 0.025 = 2.5%)
        min_threshold: Minimum threshold % (default: 0.5%)
        max_threshold: Maximum threshold % (default: 1.0%)
    
    Returns:
        Adaptive confirmation threshold as percentage
        
    Example:
        >>> atr = 0.015  # 1.5% ATR
        >>> threshold = calculate_adaptive_confirmation_threshold(atr)
        >>> print(f"Threshold: {threshold}%")  # Output: 0.75%
    """
    # Scale ATR by 0.5 to get threshold
    threshold = atr_pct * 100 * 0.5  # Convert to percentage and scale
    
    # Clamp between min and max
    threshold = max(min_threshold, min(max_threshold, threshold))
    
    return threshold


def analyze_stock_metrics(price_data: pd.DataFrame) -> Dict:
    """
    Analyze comprehensive stock metrics for pattern detection.
    
    Args:
        price_data: DataFrame with OHLCV data
    
    Returns:
        Dictionary with:
        - atr_pct: ATR as percentage
        - atr_14: Raw ATR value (14-period)
        - adaptive_threshold: Recommended confirmation threshold
        - volatility_category: 'low', 'medium', or 'high'
        - avg_volume: Average daily volume
        - avg_spread_pct: Average bid-ask spread estimate
    """
    if price_data.empty:
        return {
            'atr_pct': 0.02,
            'atr_14': 0.0,
            'adaptive_threshold': 0.75,
            'volatility_category': 'medium',
            'avg_volume': 0,
            'avg_spread_pct': 0.0
        }
    
    # Calculate ATR
    atr_pct = calculate_atr(price_data, period=14)
    atr_14 = atr_pct * price_data['close'].iloc[-1]  # Raw ATR value
    
    # Calculate adaptive threshold
    adaptive_threshold = calculate_adaptive_confirmation_threshold(atr_pct)
    
    # Categorize volatility
    if atr_pct < 0.02:
        volatility_category = 'low'
    elif atr_pct < 0.03:
        volatility_category = 'medium'
    else:
        volatility_category = 'high'
    
    # Calculate average volume
    avg_volume = price_data['volume'].mean() if 'volume' in price_data.columns else 0
    
    # Estimate spread (high-low as proxy for bid-ask spread)
    if 'high' in price_data.columns and 'low' in price_data.columns:
        spreads = (price_data['high'] - price_data['low']) / price_data['close']
        avg_spread_pct = spreads.mean() * 100
    else:
        avg_spread_pct = 0.0
    
    return {
        'atr_pct': atr_pct,
        'atr_14': atr_14,
        'adaptive_threshold': adaptive_threshold,
        'volatility_category': volatility_category,
        'avg_volume': avg_volume,
        'avg_spread_pct': avg_spread_pct
    }


def get_liquidity_score(price_data: pd.DataFrame) -> float:
    """
    Calculate liquidity score (0-100) based on volume and spread.
    
    Higher score = better liquidity = easier to enter/exit positions.
    
    Args:
        price_data: DataFrame with OHLCV data
    
    Returns:
        Liquidity score (0-100)
    """
    if price_data.empty:
        return 0.0
    
    # Volume component (0-50 points)
    avg_volume = price_data['volume'].mean() if 'volume' in price_data.columns else 0
    volume_score = min(50, (avg_volume / 1_000_000) * 5)  # 10M volume = 50 points
    
    # Spread component (0-50 points)
    if 'high' in price_data.columns and 'low' in price_data.columns:
        spreads = (price_data['high'] - price_data['low']) / price_data['close']
        avg_spread_pct = spreads.mean() * 100
        spread_score = max(0, 50 - (avg_spread_pct * 10))  # Tighter spread = higher score
    else:
        spread_score = 25  # Neutral score if no data
    
    return volume_score + spread_score
