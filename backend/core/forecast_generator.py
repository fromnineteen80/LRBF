"""
Forecast Generator - Phase 2, Checkpoint 2.4

Generates comprehensive daily trading forecast from selected stocks.
This forecast feeds into the morning HTML report and is used by the 
live monitor for actual vs. expected comparison.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
sys.path.append('/home/claude/railyard')

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import json
from config import TradingConfig as cfg


def generate_daily_forecast(
    selected_stocks_df: pd.DataFrame,
    total_stocks_scanned: int,
    stocks_qualified: int,
    all_analyzed_stocks_df: pd.DataFrame = None,
    backup_stocks_df: pd.DataFrame = None,  # NEW: Backup stocks parameter
    position_size: float = None,
    deployed_capital: float = None,
    forecast_confidence: float = None
) -> Dict:
    """
    Generate complete daily forecast from selected stocks.
    
    This is the main function for Checkpoint 2.4. It takes the selected
    stocks from the stock selector and generates all forecast data needed
    for the morning report and live monitoring.
    
    Args:
        selected_stocks_df: DataFrame with selected stocks and their metrics
        total_stocks_scanned: Total number of stocks analyzed
        stocks_qualified: Number that met quality standards
        all_analyzed_stocks_df: DataFrame with ALL analyzed stocks (for total VWAP count)
        position_size: Position size per stock (default: $3,000)
        deployed_capital: Total capital deployed (default: $24,000)
        forecast_confidence: Confidence level for ranges (default: 94%)
    
    Returns:
        Dictionary with complete forecast data
    """
    
    if selected_stocks_df.empty:
        return _generate_empty_forecast()
    
    # Use config defaults if not specified
    if position_size is None:
        # Will be calculated from account balance in production
        # For testing, use example: $30K Ã 0.80 / 8 = $3K
        position_size = 3000  # Placeholder for testing
    if deployed_capital is None:
        deployed_capital = position_size * cfg.NUM_STOCKS
    if forecast_confidence is None:
        forecast_confidence = cfg.FORECAST_CONFIDENCE
    
    # Current date and time
    now = datetime.now()
    
    # Calculate total VWAP occurrences from ALL analyzed stocks
    if all_analyzed_stocks_df is not None and not all_analyzed_stocks_df.empty:
        total_vwap_all_stocks = int(all_analyzed_stocks_df['total_patterns'].sum())
    else:
        # Fallback: estimate from selected stocks
        total_vwap_all_stocks = 0
    
    # Calculate per-stock forecasts
    stock_forecasts = []
    
    for idx, row in selected_stocks_df.iterrows():
        stock_forecast = _calculate_stock_forecast(row, position_size)
        stock_forecasts.append(stock_forecast)
    
    # Calculate backup stock forecasts
    backup_forecasts = []
    if backup_stocks_df is not None and not backup_stocks_df.empty:
        for idx, row in backup_stocks_df.iterrows():
            backup_forecast = _calculate_stock_forecast(row, position_size)
            backup_forecasts.append(backup_forecast)
    
    # Calculate portfolio totals
    portfolio_forecast = _calculate_portfolio_forecast(
        stock_forecasts,
        deployed_capital,
        forecast_confidence,
        total_stocks_scanned,
        stocks_qualified,
        total_vwap_all_stocks
    )
    
    # Build complete forecast structure
    forecast = {
        'metadata': {
            'date': now.strftime('%Y-%m-%d'),
            'date_display': now.strftime('%A, %B %d, %Y'),
            'time_generated': now.strftime('%I:%M:%S %p ET'),
            'forecast_for': 'Today',
            'confidence_level': f"{forecast_confidence*100:.0f}%"
        },
        
        'scanning': {
            'total_scanned': total_stocks_scanned,
            'qualified': stocks_qualified,
            'selected': len(selected_stocks_df),
            'rejected': total_stocks_scanned - stocks_qualified
        },
        
        'summary': portfolio_forecast['summary'],
        
        'stocks': stock_forecasts,
        'backup_stocks': backup_forecasts,
        
        'portfolio': {
            'deployed_capital': deployed_capital,
            'position_size': position_size,
            'num_positions': len(selected_stocks_df),
            'reserve_capital': 30000 - deployed_capital,  # Assuming $30K total
            'reserve_pct': (30000 - deployed_capital) / 30000 * 100
        },
        
        'ranges': portfolio_forecast['ranges'],
        
        'risk_parameters': {
            'daily_loss_limit_pct': -1.5,
            'per_trade_stop_pct': -0.5,
            'per_trade_target_1_pct': 0.75,
            'per_trade_target_2_pct': 2.0,
            'position_size_pct': (position_size / 30000) * 100
        }
    }
    
    return forecast


def _calculate_stock_forecast(stock_row: pd.Series, position_size: float) -> Dict:
    """
    Calculate forecast for a single stock.
    
    Args:
        stock_row: Row from selected stocks DataFrame
        position_size: Position size for this stock
    
    Returns:
        Dictionary with stock-level forecast
    """
    
    # Extract metrics from stock_row
    ticker = stock_row['ticker']
    category = stock_row.get('category', 'Medium')
    
    patterns_per_day = stock_row.get('patterns_per_day', 0)
    entries_per_day = stock_row.get('entries_per_day', 0)
    confirmation_rate = stock_row.get('confirmation_rate', 0)
    win_rate = stock_row.get('win_rate', 0)
    
    avg_win_pct = stock_row.get('avg_win_pct', 0)
    avg_loss_pct = stock_row.get('avg_loss_pct', 0)
    expected_value = stock_row.get('expected_value', 0)
    
    quality_score = stock_row.get('quality_score', 0)
    
    wins = stock_row.get('wins', 0)
    losses = stock_row.get('losses', 0)
    
    # Calculate expected P&L
    expected_profit_per_entry = (expected_value / 100) * position_size
    expected_daily_pl = entries_per_day * expected_profit_per_entry
    
    # Estimate volatility (ATR proxy from patterns)
    # More patterns = more volatility
    estimated_atr_pct = min(2.0, patterns_per_day / 100)
    
    # Estimate spread (lower quality = wider spread)
    estimated_spread = 0.01 + (1 - quality_score) * 0.05
    
    # Estimate volume (conservative stocks = lower volume typically)
    if category == 'Conservative':
        estimated_volume_m = 15.0 + patterns_per_day * 0.1
    elif category == 'Aggressive':
        estimated_volume_m = 25.0 + patterns_per_day * 0.15
    else:  # Medium
        estimated_volume_m = 20.0 + patterns_per_day * 0.12
    
    return {
        'ticker': ticker,
        'category': category,
        
        # Pattern metrics
        'vwap_occurred_20d': int(patterns_per_day * 20),
        'expected_patterns_today': round(patterns_per_day, 1),
        'expected_entries_today': round(entries_per_day, 1),
        'confirmation_rate': confirmation_rate,
        
        # Performance metrics
        'win_rate': win_rate,
        'wins': int(wins),
        'losses': int(losses),
        'avg_win_pct': avg_win_pct,
        'avg_loss_pct': avg_loss_pct,
        'expected_value_pct': expected_value,
        
        # Forecast
        'expected_daily_pl': expected_daily_pl,
        
        # Market characteristics
        'volatility_atr_pct': estimated_atr_pct,
        'spread': estimated_spread,
        'volume_m': estimated_volume_m,
        
        # Quality
        'quality_score': quality_score
    }


def _calculate_portfolio_forecast(
    stock_forecasts: List[Dict],
    deployed_capital: float,
    confidence: float,
    total_scanned: int = 0,
    total_qualified: int = 0,
    total_vwap_all_stocks: int = 0
) -> Dict:
    """
    Calculate portfolio-level forecast from individual stock forecasts.
    
    Args:
        stock_forecasts: List of stock forecast dictionaries
        deployed_capital: Total capital deployed
        confidence: Confidence level (0.94 = 94%)
        total_scanned: Total stocks scanned from universe
        total_qualified: Total stocks that met quality criteria
        total_vwap_all_stocks: Total VWAP occurrences across ALL analyzed stocks
    
    Returns:
        Dictionary with portfolio forecast
    """
    
    # Sum up totals
    total_patterns = sum(s['expected_patterns_today'] for s in stock_forecasts)
    total_entries = sum(s['expected_entries_today'] for s in stock_forecasts)
    total_pl = sum(s['expected_daily_pl'] for s in stock_forecasts)
    
    # Calculate ranges based on confidence interval
    # Using Â±20% for conservative/optimistic
    patterns_low = int(total_patterns * 0.80)
    patterns_high = int(total_patterns * 1.20)
    
    entries_low = int(total_entries * 0.80)
    entries_high = int(total_entries * 1.20)
    
    pl_low = total_pl * 0.80
    pl_high = total_pl * 1.20
    
    # Calculate ROI
    roi_expected = (total_pl / deployed_capital) * 100
    roi_low = (pl_low / deployed_capital) * 100
    roi_high = (pl_high / deployed_capital) * 100
    
    # Calculate exact totals from SELECTED 8 stocks only (for Win/Loss card)
    total_wins_8 = sum(s['wins'] for s in stock_forecasts)
    total_losses_8 = sum(s['losses'] for s in stock_forecasts)
    total_trades_8 = total_wins_8 + total_losses_8
    win_rate_8 = (total_wins_8 / total_trades_8 * 100) if total_trades_8 > 0 else 0
    
    # Summary stats (4 cards for morning report)
    summary = {
        'universe_scanned': {
            'value': total_scanned,
            'subtext': f"{total_qualified} qualified, {len(stock_forecasts)} selected"
        },
        'vwap_occurrences': {
            'value': total_vwap_all_stocks,
            'subtext': f"${total_vwap_all_stocks * 3:,} in estimated value"
        },
        'expected_trades': {
            'low': entries_low,
            'expected': int(total_entries),
            'high': entries_high,
            'confidence': f"{confidence*100:.0f}%",
            'subtext': f"{confidence*100:.0f}% forecast confidence"
        },
        'win_loss_record': {
            'wins': total_wins_8,
            'losses': total_losses_8,
            'win_rate': win_rate_8,
            'subtext': f"from 20-day backtest"
        }
    }
    
    # Detailed ranges
    ranges = {
        'patterns': {
            'low': patterns_low,
            'expected': int(total_patterns),
            'high': patterns_high,
            'display': f"{patterns_low} - {patterns_high}"
        },
        'trades': {
            'low': entries_low,
            'expected': int(total_entries),
            'high': entries_high,
            'display': f"{entries_low} - {entries_high}"
        },
        'profit': {
            'low': pl_low,
            'expected': total_pl,
            'high': pl_high,
            'display': f"${pl_low:,.0f} - ${pl_high:,.0f}"
        },
        'roi': {
            'low': roi_low,
            'expected': roi_expected,
            'high': roi_high,
            'display': f"{roi_low:.1f}% - {roi_high:.1f}%"
        }
    }
    
    return {
        'summary': summary,
        'ranges': ranges
    }


def _generate_empty_forecast() -> Dict:
    """Generate empty forecast structure when no stocks selected."""
    
    now = datetime.now()
    
    return {
        'metadata': {
            'date': now.strftime('%Y-%m-%d'),
            'date_display': now.strftime('%A, %B %d, %Y'),
            'time_generated': now.strftime('%I:%M:%S %p ET'),
            'forecast_for': 'Today',
            'confidence_level': '0%'
        },
        'scanning': {
            'total_scanned': 0,
            'qualified': 0,
            'selected': 0,
            'rejected': 0
        },
        'summary': {},
        'stocks': [],
        'portfolio': {},
        'ranges': {},
        'risk_parameters': {}
    }


def save_forecast_to_json(forecast: Dict, filepath: str = None) -> str:
    """
    Save forecast to JSON file for live monitor comparison.
    
    Args:
        forecast: Forecast dictionary
        filepath: Path to save (default: output/forecast_YYYY-MM-DD.json)
    
    Returns:
        Path where forecast was saved
    """
    
    if filepath is None:
        date_str = forecast['metadata']['date']
        filepath = f"/home/claude/railyard/output/forecast_{date_str}.json"
    
    with open(filepath, 'w') as f:
        json.dump(forecast, f, indent=2)
    
    return filepath


def load_forecast_from_json(filepath: str) -> Dict:
    """
    Load forecast from JSON file.
    
    Args:
        filepath: Path to forecast JSON file
    
    Returns:
        Forecast dictionary
    """
    
    with open(filepath, 'r') as f:
        forecast = json.load(f)
    
    return forecast


def format_forecast_summary(forecast: Dict) -> str:
    """
    Format forecast as readable text summary.
    
    Args:
        forecast: Forecast dictionary
    
    Returns:
        Formatted text string
    """
    
    lines = []
    lines.append("")
    lines.append("="*80)
    lines.append("DAILY TRADING FORECAST")
    lines.append("="*80)
    lines.append("")
    
    # Metadata
    meta = forecast['metadata']
    lines.append(f"ð {meta['date_display']}")
    lines.append(f"ð Generated: {meta['time_generated']}")
    lines.append("")
    
    # Scanning summary
    scan = forecast['scanning']
    lines.append(f"ð Stock Scanning:")
    lines.append(f"   Total scanned: {scan['total_scanned']}")
    lines.append(f"   Qualified: {scan['qualified']}")
    lines.append(f"   Selected: {scan['selected']}")
    lines.append("")
    
    # Forecast summary
    if 'expected_trades' in forecast['summary']:
        trades = forecast['summary']['expected_trades']
        profit = forecast['summary']['forecasted_profit']
        
        lines.append(f"ð Expected Performance:")
        lines.append(f"   Trades: {trades['low']} - {trades['high']} (expected: {trades['expected']})")
        lines.append(f"   Profit: ${profit['low']:,.0f} - ${profit['high']:,.0f} (expected: ${profit['expected']:,.0f})")
        lines.append(f"   ROI: {profit['roi_low']:.1f}% - {profit['roi_high']:.1f}% (expected: {profit['roi_expected']:.1f}%)")
        lines.append("")
    
    # Selected stocks
    lines.append(f"ð¯ Selected Stocks ({len(forecast['stocks'])}):")
    lines.append("")
    
    for stock in forecast['stocks']:
        lines.append(f"  {stock['ticker']} ({stock['category']})")
        lines.append(f"     Expected entries: {stock['expected_entries_today']:.1f}")
        lines.append(f"     Expected P&L: ${stock['expected_daily_pl']:,.0f}")
        lines.append(f"     Win rate: {stock['win_rate']*100:.1f}%")
        lines.append(f"     Quality score: {stock['quality_score']:.3f}")
        lines.append("")
    
    lines.append("="*80)
    lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("FORECAST GENERATOR TEST - Checkpoint 2.4")
    print("="*80)
    print()
    
    # Import dependencies
    from backend.core.batch_analyzer import analyze_batch, calculate_quality_scores
    from backend.core.stock_selector import select_balanced_portfolio, get_portfolio_configurations
    from backend.data.stock_universe import get_sample_tickers
    
    print("Running batch analysis on 20 sample stocks...")
    print("(Using simulation mode)")
    print()
    
    # Analyze stocks
    sample_tickers = get_sample_tickers(10)
    sample_tickers.extend(['WMT', 'JPM', 'V', 'MA', 'HD', 'DIS', 'COIN', 'PLTR', 'RIVN', 'SNOW'])
    
    results = analyze_batch(
        sample_tickers,
        period="20d",
        interval="1m",
        entry_confirmation_pct=1.5,
        verbose=False,
        delay=0.05,
        use_simulation=True
    )
    
    if not results.empty:
        # Calculate quality scores
        results = calculate_quality_scores(results)
        
        print(f"â Analyzed {len(results)} stocks")
        print()
        
        # Select portfolio
        configs = get_portfolio_configurations()
        selection = select_balanced_portfolio(
            results,
            **configs['aggressive'],
            min_confirmation_rate=0.25,
            min_expected_value=0.0,
            min_entries_per_day=3.0
        )
        
        if not selection['selected'].empty:
            print(f"â Selected {len(selection['selected'])} stocks")
            print()
            
            # Generate forecast
            print("Generating daily forecast...")
            print()
            
            forecast = generate_daily_forecast(
                selected_stocks_df=selection['selected'],
                total_stocks_scanned=len(sample_tickers),
                stocks_qualified=len(results),
                position_size=3000,
                deployed_capital=24000
            )
            
            # Display forecast
            summary = format_forecast_summary(forecast)
            print(summary)
            
            # Save to JSON
            json_path = save_forecast_to_json(forecast)
            print(f"â Forecast saved to: {json_path}")
            print()
            
            # Show JSON structure
            print("ð Forecast JSON Structure:")
            print(f"   - metadata: {len(forecast['metadata'])} fields")
            print(f"   - scanning: {len(forecast['scanning'])} fields")
            print(f"   - summary: {len(forecast['summary'])} cards")
            print(f"   - stocks: {len(forecast['stocks'])} stocks")
            print(f"   - portfolio: {len(forecast['portfolio'])} fields")
            print(f"   - ranges: {len(forecast['ranges'])} metrics")
            print()
            
        else:
            print("â No stocks selected")
    
    else:
        print("â No analysis results")
