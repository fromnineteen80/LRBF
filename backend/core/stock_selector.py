"""
Stock Selector

Selects the best 8 stocks from batch analysis results for daily trading.

Selection criteria:
- Quality scoring (confirmation rate, EV, win rate, activity)
- Minimum standards filtering
- Balanced portfolio construction (2 conservative / 4 medium / 2 aggressive)

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
sys.path.append('/home/claude/railyard')

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from config import TradingConfig as cfg
from backend.data.stock_universe import get_conservative_stocks, get_aggressive_stocks


def categorize_stocks(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize stocks as Conservative, Medium, or Aggressive based on characteristics.
    
    Conservative:
    - Lower volatility (fewer entries per day)
    - Higher confirmation rates (>70%)
    - Mega-cap stocks from conservative list
    
    Aggressive:
    - Higher volatility (more entries per day)
    - Lower confirmation rates (but still >40%)
    - High-growth or volatile stocks
    
    Medium:
    - Everything in between
    
    Args:
        results_df: DataFrame with analysis results and quality scores
    
    Returns:
        DataFrame with 'category' column added
    """
    
    if results_df.empty:
        return results_df
    
    df = results_df.copy()
    
    # Get reference lists
    conservative_list = get_conservative_stocks()
    aggressive_list = get_aggressive_stocks()
    
    # Initialize category column
    df['category'] = 'Medium'
    
    # Categorize based on characteristics
    for idx, row in df.iterrows():
        ticker = row['ticker']
        conf_rate = row['confirmation_rate']
        entries_per_day = row['entries_per_day']
        
        # Conservative: High confirmation OR in conservative list
        if ticker in conservative_list or (conf_rate >= 0.35 and entries_per_day < 35):
            df.at[idx, 'category'] = 'Conservative'
        
        # Aggressive: Very high activity OR in aggressive list
        elif ticker in aggressive_list or (entries_per_day >= 50):
            df.at[idx, 'category'] = 'Aggressive'
        
        # Medium: Everything else (most stocks should fall here)
        # - Moderate confirmation (25-35%)
        # - Moderate activity (35-50 entries/day)
    
    return df


def get_portfolio_configurations() -> Dict[str, Dict[str, int]]:
    """
    Get predefined portfolio configurations for different market conditions.
    
    Returns:
        Dictionary of configuration names and their stock allocations
        
    Example:
        >>> configs = get_portfolio_configurations()
        >>> aggressive_config = configs['aggressive']
        >>> # Use with: select_balanced_portfolio(..., **aggressive_config)
    """
    
    return {
        'aggressive': {
            'n_conservative': 2,
            'n_medium': 3,
            'n_aggressive': 3,
            # Use when: Market favors momentum, want max trade volume
        },
        'balanced': {
            'n_conservative': 2,
            'n_medium': 4,
            'n_aggressive': 2,
            # Use when: Uncertain conditions, want stability
        },
        'conservative': {
            'n_conservative': 3,
            'n_medium': 3,
            'n_aggressive': 2,
            # Use when: Risk-off environment, prioritize safety
        },
        'maximum_volume': {
            'n_conservative': 1,
            'n_medium': 2,
            'n_aggressive': 5,
            # Use when: Need maximum trade frequency
        }
    }


def select_balanced_portfolio(
    results_df: pd.DataFrame,
    n_conservative: int = None,
    n_medium: int = None,
    n_aggressive: int = None,
    min_confirmation_rate: float = None,
    min_expected_value: float = None,
    min_entries_per_day: float = None
) -> Dict[str, pd.DataFrame]:
    """
    Select a balanced portfolio of stocks.
    
    Args:
        results_df: DataFrame with analysis results and quality scores
        n_conservative: Number of conservative stocks (default from config)
        n_medium: Number of medium stocks (default from config)
        n_aggressive: Number of aggressive stocks (default from config)
        min_confirmation_rate: Minimum confirmation rate (default from config)
        min_expected_value: Minimum expected value (default from config)
        min_entries_per_day: Minimum entries per day (default from config)
    
    Returns:
        Dictionary with 'selected' DataFrame and selection metadata
        
    Note:
        Common configurations:
        - 2/3/3: Balanced with slight aggressive tilt (more trade volume)
        - 2/4/2: Balanced with medium emphasis (more stability)
        - 3/3/2: Conservative tilt (lower risk)
    """
    
    # Use config defaults if not specified
    portfolio_counts = cfg.get_portfolio_counts()
    if n_conservative is None:
        n_conservative = portfolio_counts['conservative']
    if n_medium is None:
        n_medium = portfolio_counts['medium']
    if n_aggressive is None:
        n_aggressive = portfolio_counts['aggressive']
    if min_confirmation_rate is None:
        min_confirmation_rate = cfg.MIN_CONFIRMATION_RATE
    if min_expected_value is None:
        min_expected_value = cfg.MIN_EXPECTED_VALUE
    if min_entries_per_day is None:
        min_entries_per_day = cfg.MIN_ENTRIES_PER_DAY
    
    if results_df.empty:
        return {
            'selected': pd.DataFrame(),
            'conservative': pd.DataFrame(),
            'medium': pd.DataFrame(),
            'aggressive': pd.DataFrame(),
            'rejected_count': 0,
            'total_analyzed': 0
        }
    
    # Categorize stocks
    df = categorize_stocks(results_df)
    
    total_analyzed = len(df)
    
    # Filter for minimum quality
    quality_mask = (
        (df['confirmation_rate'] >= min_confirmation_rate) &
        (df['expected_value'] >= min_expected_value) &
        (df['entries_per_day'] >= min_entries_per_day)
    )
    
    df_quality = df[quality_mask].copy()
    rejected_count = total_analyzed - len(df_quality)
    
    if df_quality.empty:
        print("⚠️  No stocks met minimum quality criteria!")
        return {
            'selected': pd.DataFrame(),
            'conservative': pd.DataFrame(),
            'medium': pd.DataFrame(),
            'aggressive': pd.DataFrame(),
            'rejected_count': rejected_count,
            'total_analyzed': total_analyzed
        }
    
    # Split by category
    conservative = df_quality[df_quality['category'] == 'Conservative'].copy()
    medium = df_quality[df_quality['category'] == 'Medium'].copy()
    aggressive = df_quality[df_quality['category'] == 'Aggressive'].copy()
    
    # Sort each by quality score with tie-breaking
    conservative = conservative.sort_values(
        ['quality_score', 'confirmation_rate', 'expected_value', 'ticker'],
        ascending=[False, False, False, True]
    ).head(n_conservative * 2)  # Get extras in case needed
    medium = medium.sort_values(
        ['quality_score', 'confirmation_rate', 'expected_value', 'ticker'],
        ascending=[False, False, False, True]
    ).head(n_medium * 2)
    aggressive = aggressive.sort_values(
        ['quality_score', 'confirmation_rate', 'expected_value', 'ticker'],
        ascending=[False, False, False, True]
    ).head(n_aggressive * 2)
    
    # Select top N from each category
    selected_conservative = conservative.head(n_conservative)
    selected_medium = medium.head(n_medium)
    selected_aggressive = aggressive.head(n_aggressive)
    
    # Handle shortfalls (if not enough in a category)
    total_selected = len(selected_conservative) + len(selected_medium) + len(selected_aggressive)
    target_total = n_conservative + n_medium + n_aggressive
    
    if total_selected < target_total:
        # Not enough in specific categories, fill from overall pool
        already_selected = pd.concat([selected_conservative, selected_medium, selected_aggressive])
        remaining = df_quality[~df_quality['ticker'].isin(already_selected['ticker'])]
        
        shortfall = target_total - total_selected
        additional = remaining.sort_values(
            ['quality_score', 'confirmation_rate', 'expected_value', 'ticker'],
            ascending=[False, False, False, True]
        ).head(shortfall)
        
        # Combine
        final_selection = pd.concat([selected_conservative, selected_medium, selected_aggressive, additional])
    else:
        final_selection = pd.concat([selected_conservative, selected_medium, selected_aggressive])
    
    # Sort by quality score
    final_selection = final_selection.sort_values(
        ['quality_score', 'confirmation_rate', 'expected_value', 'ticker'],
        ascending=[False, False, False, True]
    ).reset_index(drop=True)
    
    # Select 4 backup stocks (next best after primary selection)
    backup_stocks = pd.DataFrame()
    remaining_stocks = df_quality[~df_quality['ticker'].isin(final_selection['ticker'])]
    if len(remaining_stocks) >= 4:
        backup_stocks = remaining_stocks.sort_values(
            ['quality_score', 'confirmation_rate', 'expected_value', 'ticker'],
            ascending=[False, False, False, True]
        ).head(4).reset_index(drop=True)
    elif len(remaining_stocks) > 0:
        backup_stocks = remaining_stocks.sort_values(
            ['quality_score', 'confirmation_rate', 'expected_value', 'ticker'],
            ascending=[False, False, False, True]
        ).reset_index(drop=True)
    
    return {
        'selected': final_selection,
        'backup': backup_stocks,
        'conservative': selected_conservative,
        'medium': selected_medium,
        'aggressive': selected_aggressive,
        'rejected_count': rejected_count,
        'total_analyzed': total_analyzed,
        'selection_summary': {
            'conservative_count': len(selected_conservative),
            'medium_count': len(selected_medium),
            'aggressive_count': len(selected_aggressive),
            'total_selected': len(final_selection),
            'backup_count': len(backup_stocks)
        }
    }


def calculate_portfolio_forecast(selected_df: pd.DataFrame, position_size: float = 3000) -> Dict:
    """
    Calculate expected daily performance for the selected portfolio.
    
    Args:
        selected_df: DataFrame with selected stocks
        position_size: Position size per stock (default: $3,000 = 10% of $30K)
    
    Returns:
        Dictionary with portfolio forecast
    """
    
    if selected_df.empty:
        return {
            'total_entries_per_day': 0,
            'min_daily_pl': 0,
            'expected_daily_pl': 0,
            'max_daily_pl': 0,
            'min_daily_roi_pct': 0,
            'expected_daily_roi_pct': 0,
            'max_daily_roi_pct': 0,
        }
    
    # Calculate per-stock metrics
    selected_df = selected_df.copy()
    
    # Expected profit per entry
    selected_df['expected_profit_per_entry'] = selected_df['expected_value'] / 100 * position_size
    
    # Daily P&L per stock
    selected_df['expected_daily_pl'] = (
        selected_df['entries_per_day'] * selected_df['expected_profit_per_entry']
    )
    
    # Portfolio totals
    total_entries_per_day = selected_df['entries_per_day'].sum()
    expected_daily_pl = selected_df['expected_daily_pl'].sum()
    
    # Calculate range (conservative: -20%, aggressive: +20%)
    min_daily_pl = expected_daily_pl * 0.80
    max_daily_pl = expected_daily_pl * 1.20
    
    # ROI on deployed capital (8 stocks × $4,800 = $38,400 deployed)
    deployed_capital = position_size * len(selected_df)
    
    expected_daily_roi_pct = (expected_daily_pl / deployed_capital) * 100
    min_daily_roi_pct = (min_daily_pl / deployed_capital) * 100
    max_daily_roi_pct = (max_daily_pl / deployed_capital) * 100
    
    return {
        'total_entries_per_day': round(total_entries_per_day, 1),
        'min_daily_pl': round(min_daily_pl, 2),
        'expected_daily_pl': round(expected_daily_pl, 2),
        'max_daily_pl': round(max_daily_pl, 2),
        'min_daily_roi_pct': round(min_daily_roi_pct, 2),
        'expected_daily_roi_pct': round(expected_daily_roi_pct, 2),
        'max_daily_roi_pct': round(max_daily_roi_pct, 2),
        'deployed_capital': deployed_capital,
        'per_stock_breakdown': selected_df[['ticker', 'entries_per_day', 'expected_daily_pl']].to_dict('records')
    }


def generate_selection_report(selection_result: Dict, forecast: Dict) -> str:
    """
    Generate a text report of the stock selection.
    
    Args:
        selection_result: Result from select_balanced_portfolio()
        forecast: Result from calculate_portfolio_forecast()
    
    Returns:
        Formatted text report
    """
    
    selected = selection_result['selected']
    
    if selected.empty:
        return "❌ No stocks selected - none met minimum quality criteria"
    
    report = []
    report.append("\n" + "="*80)
    report.append("STOCK SELECTION REPORT")
    report.append("="*80)
    report.append("")
    
    # Selection summary
    report.append("📊 SELECTION SUMMARY")
    report.append("-" * 80)
    report.append(f"   Total stocks analyzed: {selection_result['total_analyzed']}")
    report.append(f"   Stocks rejected (quality): {selection_result['rejected_count']}")
    report.append(f"   Stocks selected: {len(selected)}")
    report.append("")
    
    summary = selection_result['selection_summary']
    report.append(f"   Portfolio Balance:")
    report.append(f"     Conservative: {summary['conservative_count']} stocks")
    report.append(f"     Medium:       {summary['medium_count']} stocks")
    report.append(f"     Aggressive:   {summary['aggressive_count']} stocks")
    report.append("")
    
    # Selected stocks table
    report.append("📈 SELECTED STOCKS (Ranked by Quality Score)")
    report.append("-" * 80)
    report.append("")
    
    for idx, row in selected.iterrows():
        report.append(f"#{idx+1}. {row['ticker']} - {row['category']}")
        report.append(f"     Quality Score:    {row['quality_score']:.3f}")
        report.append(f"     Confirmation:     {row['confirmation_rate']*100:.1f}%")
        report.append(f"     Win Rate:         {row['win_rate']*100:.1f}%")
        report.append(f"     Expected Value:   {row['expected_value']:+.2f}%")
        report.append(f"     Entries/Day:      {row['entries_per_day']:.1f}")
        report.append(f"     Patterns/Day:     {row['patterns_per_day']:.1f}")
        report.append("")
    
    # Portfolio forecast
    report.append("="*80)
    report.append("💰 PORTFOLIO FORECAST (Today's Expected Performance)")
    report.append("="*80)
    report.append("")
    
    report.append(f"📊 Trading Activity:")
    report.append(f"   Total entries expected: {forecast['total_entries_per_day']:.0f} trades")
    report.append(f"   Deployed capital:       ${forecast['deployed_capital']:,.0f}")
    report.append("")
    
    report.append(f"💵 Expected Daily P&L:")
    report.append(f"   Conservative: ${forecast['min_daily_pl']:,.2f}")
    report.append(f"   Expected:     ${forecast['expected_daily_pl']:,.2f}")
    report.append(f"   Optimistic:   ${forecast['max_daily_pl']:,.2f}")
    report.append("")
    
    report.append(f"📈 Expected Daily ROI:")
    report.append(f"   Conservative: {forecast['min_daily_roi_pct']:.2f}%")
    report.append(f"   Expected:     {forecast['expected_daily_roi_pct']:.2f}%")
    report.append(f"   Optimistic:   {forecast['max_daily_roi_pct']:.2f}%")
    report.append("")
    
    report.append("="*80)
    
    return "\n".join(report)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("STOCK SELECTOR TEST")
    print("="*80)
    print()
    
    # Import batch analyzer
    from backend.core.batch_analyzer import analyze_batch, calculate_quality_scores
    from backend.data.stock_universe import get_sample_tickers
    
    print("Running batch analysis on 20 sample stocks...")
    print("(Using simulation mode)")
    print()
    
    # Analyze 20 stocks
    sample_tickers = get_sample_tickers(10)
    # Add some more for variety
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
        
        print(f"✅ Analyzed {len(results)} stocks")
        print()
        
        # Get available configurations
        configs = get_portfolio_configurations()
        
        # TEST 1: Aggressive configuration (2/3/3)
        print("="*80)
        print("CONFIGURATION 1: AGGRESSIVE (2/3/3)")
        print("="*80)
        print("Best for: Momentum markets, maximizing trade volume")
        print()
        
        selection_aggressive = select_balanced_portfolio(
            results,
            **configs['aggressive'],
            min_confirmation_rate=0.25,
            min_expected_value=0.0,
            min_entries_per_day=3.0
        )
        
        forecast_aggressive = calculate_portfolio_forecast(
            selection_aggressive['selected'], 
            position_size=3000
        )
        
        report_aggressive = generate_selection_report(selection_aggressive, forecast_aggressive)
        print(report_aggressive)
        
        # TEST 2: Balanced configuration (2/4/2)
        print("\n" + "="*80)
        print("CONFIGURATION 2: BALANCED (2/4/2)")
        print("="*80)
        print("Best for: Uncertain markets, emphasizing stability")
        print()
        
        selection_balanced = select_balanced_portfolio(
            results,
            **configs['balanced'],
            min_confirmation_rate=0.25,
            min_expected_value=0.0,
            min_entries_per_day=3.0
        )
        
        forecast_balanced = calculate_portfolio_forecast(
            selection_balanced['selected'], 
            position_size=3000
        )
        
        report_balanced = generate_selection_report(selection_balanced, forecast_balanced)
        print(report_balanced)
        
    else:
        print("❌ No analysis results")
