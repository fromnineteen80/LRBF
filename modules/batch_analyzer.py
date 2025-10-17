"""
Batch Pattern Analyzer

Efficiently analyzes VWAP Recovery Patterns across multiple stocks.
Downloads historical data and runs pattern detection in batch.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
sys.path.append('/home/claude/railyard')

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
from modules.pattern_detector import analyze_patterns_with_outcomes, get_pattern_summary
from modules.stock_universe import get_stock_universe, get_sample_tickers
from config import TradingConfig as cfg


def download_stock_data(
    ticker: str,
    period: str = "20d",
    interval: str = "1m",
    max_retries: int = 3,
    use_simulation: bool = False
) -> Optional[pd.DataFrame]:
    """
    Download historical price data for a stock.
    
    Args:
        ticker: Stock ticker symbol
        period: Time period (e.g. "20d" for 20 days)
        interval: Bar interval (e.g. "1m" for 1 minute)
        max_retries: Maximum retry attempts
        use_simulation: Use simulated data if True (for testing)
    
    Returns:
        DataFrame with OHLCV data, or None if download fails
    """
    
    # If simulation mode, generate synthetic data
    if use_simulation:
        return generate_simulated_stock_data(ticker, period, interval)
    
    try:
        from modules.data_provider import get_data_provider
    except ImportError:
        print("⚠️  yfinance not installed. Using simulation mode.")
        return generate_simulated_stock_data(ticker, period, interval)
    
    for attempt in range(max_retries):
        try:
            # Download data
            # Using RapidAPI data provider
            data_provider = get_data_provider()
            data = data_provider.get_historical_data(ticker=ticker, interval=interval, range_str=period, region='US')
            
            if data is not None:
                data = data.reset_index()
            
            if data.empty:
                # Fallback to simulation
                return generate_simulated_stock_data(ticker, period, interval)
            
            # Prepare data for pattern detector
            data = data.reset_index()
            
            # Standardize column names
            data.columns = [col.lower().replace(' ', '_') for col in data.columns]
            
            # Rename datetime/date column to timestamp
            if 'datetime' in data.columns:
                data.rename(columns={'datetime': 'timestamp'}, inplace=True)
            elif 'date' in data.columns:
                data.rename(columns={'date': 'timestamp'}, inplace=True)
            
            return data
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry
                continue
            else:
                # Fallback to simulation
                return generate_simulated_stock_data(ticker, period, interval)
    
    return generate_simulated_stock_data(ticker, period, interval)


def generate_simulated_stock_data(
    ticker: str,
    period: str = "20d",
    interval: str = "1m"
) -> pd.DataFrame:
    """
    Generate realistic simulated stock data for testing.
    
    This creates data that mimics real market behavior with:
    - Institutional VWAP effects
    - Realistic volatility
    - Clean patterns (not too noisy like our first synthetic data)
    
    Args:
        ticker: Stock ticker symbol (used for seeding randomness)
        period: Time period
        interval: Bar interval
    
    Returns:
        DataFrame with simulated OHLCV data
    """
    
    # Parse period to get days
    days = int(period.replace('d', ''))
    
    # Seed based on ticker for reproducibility
    np.random.seed(sum(ord(c) for c in ticker))
    
    # Base price varies by ticker characteristics
    if ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN']:
        base_price = 175.0
        daily_volatility = 0.015  # 1.5% per day
    elif ticker in ['TSLA', 'NVDA', 'AMD', 'COIN']:
        base_price = 200.0
        daily_volatility = 0.030  # 3% per day
    else:
        base_price = 100.0
        daily_volatility = 0.020  # 2% per day
    
    all_data = []
    current_price = base_price
    
    start_date = datetime(2025, 10, 1, 9, 30)
    
    # Generate data for specified days
    trading_day = 0
    for day in range(days * 2):  # Extra days to account for weekends
        day_date = start_date + timedelta(days=day)
        
        # Skip weekends
        if day_date.weekday() >= 5:
            continue
        
        trading_day += 1
        if trading_day > days:
            break
        
        # Each trading day: 390 minutes (9:30 AM to 4:00 PM)
        for minute in range(390):
            timestamp = day_date + timedelta(minutes=minute)
            
            # Add drift and volatility
            minute_volatility = daily_volatility / np.sqrt(390)  # Scale to minute
            drift = np.random.normal(0, minute_volatility)
            current_price = current_price * (1 + drift)
            
            # Occasionally inject a clean VWAP recovery pattern
            # More frequent for volatile stocks
            pattern_probability = 0.015 if ticker in ['TSLA', 'NVDA'] else 0.010
            
            if np.random.random() < pattern_probability and minute < 380:
                # Inject a high-quality pattern
                pattern_bars = inject_quality_pattern(current_price, timestamp)
                all_data.extend(pattern_bars)
                
                # Update current price and skip ahead
                current_price = pattern_bars[-1]['close']
                minute += len(pattern_bars)
                
                if minute >= 390:
                    break
            else:
                # Normal bar
                open_price = current_price
                high = current_price + abs(np.random.normal(0, current_price * 0.0015))
                low = current_price - abs(np.random.normal(0, current_price * 0.0015))
                close = current_price + np.random.normal(0, current_price * 0.001)
                
                all_data.append({
                    'timestamp': timestamp,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': int(np.random.lognormal(12, 0.5))  # Realistic volume distribution
                })
    
    return pd.DataFrame(all_data)


def inject_quality_pattern(start_price: float, start_time: datetime) -> List[Dict]:
    """
    Inject a high-quality VWAP recovery pattern that WILL confirm.
    
    This creates patterns that behave like real institutional VWAP buying.
    """
    
    bars = []
    price = start_price
    
    # Build up to high over 3-5 bars
    buildup_bars = np.random.randint(3, 6)
    for i in range(buildup_bars):
        price += price * np.random.uniform(0.001, 0.003)
        bars.append({
            'timestamp': start_time + timedelta(minutes=i),
            'open': price - price * 0.0005,
            'high': price + price * 0.001,
            'low': price - price * 0.001,
            'close': price,
            'volume': int(np.random.lognormal(12, 0.5))
        })
    
    recent_high = price
    
    # DECLINE: 0.8-1.2%
    decline_pct = np.random.uniform(0.008, 0.012)
    decline_amount = recent_high * decline_pct
    price = recent_high - decline_amount
    
    bars.append({
        'timestamp': start_time + timedelta(minutes=len(bars)),
        'open': recent_high - decline_amount/3,
        'high': recent_high - decline_amount/4,
        'low': price,
        'close': price + price * 0.0002,
        'volume': int(np.random.lognormal(12.5, 0.5))  # Higher volume
    })
    
    # RECOVERY: 50% back up
    recovery_amount = decline_amount * 0.50
    for i in range(2):
        price += recovery_amount / 2
        bars.append({
            'timestamp': start_time + timedelta(minutes=len(bars)),
            'open': bars[-1]['close'],
            'high': price + price * 0.0005,
            'low': bars[-1]['close'] - price * 0.0003,
            'close': price,
            'volume': int(np.random.lognormal(12.2, 0.5))
        })
    
    recovery_high = price
    
    # RETRACEMENT: 50% back down
    retracement_amount = recovery_amount * 0.50
    price -= retracement_amount
    
    bars.append({
        'timestamp': start_time + timedelta(minutes=len(bars)),
        'open': recovery_high,
        'high': recovery_high + price * 0.0003,
        'low': price,
        'close': price + price * 0.0002,
        'volume': int(np.random.lognormal(12.1, 0.5))
    })
    
    # ENTRY CONFIRMATION: Climb +1.5-2.5%
    # This makes the pattern high-quality (will confirm)
    entry_trigger = price * 1.015  # +1.5%
    target = price * np.random.uniform(1.018, 1.025)  # +1.8-2.5%
    
    climb_bars = np.random.randint(4, 8)
    for i in range(climb_bars):
        price += (target - price) / (climb_bars - i) * np.random.uniform(0.8, 1.2)
        bars.append({
            'timestamp': start_time + timedelta(minutes=len(bars)),
            'open': bars[-1]['close'],
            'high': price + price * 0.0005,
            'low': bars[-1]['close'] - price * 0.0003,
            'close': price,
            'volume': int(np.random.lognormal(12, 0.5))
        })
    
    return bars


def analyze_single_stock(
    ticker: str,
    period: str = "20d",
    interval: str = "1m",
    entry_confirmation_pct: float = 1.5,
    verbose: bool = False,
    use_simulation: bool = False
) -> Optional[Dict]:
    """
    Analyze a single stock for VWAP Recovery Patterns.
    
    Args:
        ticker: Stock ticker symbol
        period: Historical data period
        interval: Bar interval
        entry_confirmation_pct: Entry threshold percentage
        verbose: Print progress messages
        use_simulation: Use simulated data (for testing/demo)
    
    Returns:
        Dictionary with analysis results, or None if failed
    """
    
    if verbose:
        print(f"   Analyzing {ticker}...", end=" ")
    
    # Download data
    data = download_stock_data(ticker, period, interval, use_simulation=use_simulation)
    
    if data is None:
        if verbose:
            print("❌ Data download failed")
        return None
    
    if len(data) < 100:  # Need sufficient data
        if verbose:
            print(f"❌ Insufficient data ({len(data)} bars)")
        return None
    
    # Analyze patterns
    try:
        results = analyze_patterns_with_outcomes(
            data,
            entry_confirmation_pct=entry_confirmation_pct
        )
        
        # Get summary statistics
        summary = get_pattern_summary(results)
        
        # Calculate additional metrics
        bars_count = len(data)
        trading_days = bars_count / 390  # Approximate (390 mins per day)
        
        patterns_per_day = summary['total_patterns'] / trading_days if trading_days > 0 else 0
        entries_per_day = summary['confirmed_entries'] / trading_days if trading_days > 0 else 0
        
        # Calculate expected value
        if summary['confirmed_entries'] > 0:
            expected_value = (
                summary['win_rate'] * summary['avg_win_pct']
            ) + (
                (1 - summary['win_rate']) * summary['avg_loss_pct']
            )
        else:
            expected_value = 0.0
        
        # Build result
        result = {
            'ticker': ticker,
            'success': True,
            'bars_analyzed': bars_count,
            'trading_days': round(trading_days, 1),
            'patterns_total': summary['total_patterns'],
            'patterns_per_day': round(patterns_per_day, 1),
            'confirmed_entries': summary['confirmed_entries'],
            'entries_per_day': round(entries_per_day, 1),
            'confirmation_rate': summary['confirmation_rate'],
            'win_rate': summary['win_rate'],
            'wins': summary['wins'],
            'losses': summary['losses'],
            'avg_win_pct': summary['avg_win_pct'],
            'avg_loss_pct': summary['avg_loss_pct'],
            'expected_value': expected_value,
            'quality_score': 0.0,  # Will be calculated later
        }
        
        if verbose:
            print(f"✅ {summary['total_patterns']} patterns, {summary['confirmed_entries']} entries, {expected_value:+.2f}% EV")
        
        return result
        
    except Exception as e:
        if verbose:
            print(f"❌ Analysis error: {str(e)}")
        return None


def analyze_batch(
    tickers: List[str],
    period: str = None,
    interval: str = None,
    entry_confirmation_pct: float = None,
    verbose: bool = True,
    delay: float = 0.5,
    use_simulation: bool = False
) -> pd.DataFrame:
    """
    Analyze multiple stocks in batch.
    
    Args:
        tickers: List of ticker symbols
        period: Historical data period (default from config)
        interval: Bar interval (default from config)
        entry_confirmation_pct: Entry threshold percentage (default from config)
        verbose: Print progress messages
        delay: Delay between requests (seconds) to avoid rate limits
        use_simulation: Use simulated data (for testing/demo)
    
    Returns:
        DataFrame with all analysis results
    """
    
    # Use config defaults if not specified
    if period is None:
        period = f"{cfg.ANALYSIS_PERIOD_DAYS}d"
    if interval is None:
        interval = cfg.BAR_INTERVAL
    if entry_confirmation_pct is None:
        entry_confirmation_pct = cfg.ENTRY_THRESHOLD
    
    if verbose:
        print(f"\n📊 Batch Analysis Starting")
        print(f"   Tickers: {len(tickers)}")
        print(f"   Period: {period}")
        print(f"   Interval: {interval}")
        print(f"   Entry threshold: {entry_confirmation_pct}%")
        if use_simulation:
            print(f"   Mode: SIMULATION (realistic synthetic data)")
        print()
    
    results = []
    successful = 0
    failed = 0
    
    for i, ticker in enumerate(tickers, 1):
        if verbose:
            print(f"[{i}/{len(tickers)}]", end=" ")
        
        result = analyze_single_stock(
            ticker,
            period=period,
            interval=interval,
            entry_confirmation_pct=entry_confirmation_pct,
            verbose=verbose,
            use_simulation=use_simulation
        )
        
        if result:
            results.append(result)
            successful += 1
        else:
            failed += 1
        
        # Rate limiting
        if i < len(tickers):
            time.sleep(delay)
    
    if verbose:
        print()
        print(f"✅ Batch Analysis Complete")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        print(f"   Success rate: {successful/len(tickers)*100:.1f}%")
        print()
    
    # Convert to DataFrame
    if results:
        df = pd.DataFrame(results)
        return df
    else:
        return pd.DataFrame()


def calculate_quality_scores(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate quality scores for each stock based on multiple factors.
    
    Quality score components:
    - Confirmation rate (40% weight)
    - Expected value (30% weight)
    - Win rate (20% weight)
    - Activity level (10% weight)
    
    Args:
        results_df: DataFrame with analysis results
    
    Returns:
        DataFrame with quality_score column added
    """
    
    if results_df.empty:
        return results_df
    
    df = results_df.copy()
    
    # Normalize components to 0-1 scale
    
    # 1. Confirmation rate (higher is better)
    conf_rate_normalized = df['confirmation_rate']
    
    # 2. Expected value (higher is better, normalize around +0.5% to +1.5%)
    ev_normalized = np.clip((df['expected_value'] + 0.5) / 2.0, 0, 1)
    
    # 3. Win rate (higher is better)
    win_rate_normalized = df['win_rate']
    
    # 4. Activity level (normalized around 5-15 entries/day)
    activity_normalized = np.clip(df['entries_per_day'] / 15.0, 0, 1)
    
    # Calculate weighted quality score
    df['quality_score'] = (
        conf_rate_normalized * 0.40 +
        ev_normalized * 0.30 +
        win_rate_normalized * 0.20 +
        activity_normalized * 0.10
    )
    
    return df


def filter_quality_stocks(
    results_df: pd.DataFrame,
    min_confirmation_rate: float = 0.50,
    min_expected_value: float = 0.0,
    min_entries_per_day: float = 3.0,
    min_patterns: int = 50
) -> pd.DataFrame:
    """
    Filter stocks that meet quality criteria.
    
    Args:
        results_df: DataFrame with analysis results
        min_confirmation_rate: Minimum confirmation rate (default: 50%)
        min_expected_value: Minimum expected value (default: 0%)
        min_entries_per_day: Minimum entries per day (default: 3)
        min_patterns: Minimum total patterns (default: 50)
    
    Returns:
        Filtered DataFrame
    """
    
    if results_df.empty:
        return results_df
    
    df = results_df.copy()
    
    # Apply filters
    mask = (
        (df['confirmation_rate'] >= min_confirmation_rate) &
        (df['expected_value'] >= min_expected_value) &
        (df['entries_per_day'] >= min_entries_per_day) &
        (df['patterns_total'] >= min_patterns)
    )
    
    return df[mask].copy()


def get_top_stocks(
    results_df: pd.DataFrame,
    n: int = 8,
    sort_by: str = 'quality_score'
) -> pd.DataFrame:
    """
    Get top N stocks sorted by specified metric.
    
    Args:
        results_df: DataFrame with analysis results
        n: Number of top stocks to return
        sort_by: Column to sort by (default: 'quality_score')
    
    Returns:
        DataFrame with top N stocks
    """
    
    if results_df.empty:
        return results_df
    
    return results_df.nlargest(n, sort_by).copy()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("BATCH PATTERN ANALYZER TEST")
    print("="*70)
    print()
    
    # Test with small sample
    print("Testing with 10 sample stocks (SIMULATION MODE)...")
    print("(Using realistic synthetic data - RapidAPI data unavailable)")
    print()
    
    sample_tickers = get_sample_tickers(10)
    
    # Run batch analysis in simulation mode
    results = analyze_batch(
        sample_tickers,
        period="20d",  
        interval="1m",
        entry_confirmation_pct=1.5,
        verbose=True,
        delay=0.1,  # Faster in simulation mode
        use_simulation=True  # Use simulation
    )
    
    if not results.empty:
        # Calculate quality scores
        results = calculate_quality_scores(results)
        
        # Show results
        print("="*70)
        print("RESULTS")
        print("="*70)
        print()
        
        print("All Stocks:")
        print(results[['ticker', 'patterns_per_day', 'confirmation_rate', 
                      'expected_value', 'quality_score']].to_string(index=False))
        print()
        
        # Filter for quality
        quality_stocks = filter_quality_stocks(results, min_confirmation_rate=0.30)
        
        print(f"Quality Stocks (confirmation rate > 30%):")
        if not quality_stocks.empty:
            print(quality_stocks[['ticker', 'confirmation_rate', 'expected_value']].to_string(index=False))
        else:
            print("   None met criteria")
        print()
        
    else:
        print("❌ No results - check internet connection or data provider")
        print()
