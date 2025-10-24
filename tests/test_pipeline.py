"""
Pipeline Test Script - Validate End-to-End with Real Data

Tests the complete pipeline:
1. Fetch real market data (yfinance)
2. Detect patterns with timing
3. Calculate composite scores
4. Store to database
5. Generate rankings

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
from datetime import date, datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.market_data_service import MarketDataService
from backend.core.pattern_detector_v2 import PatternDetector
from backend.core.category_scorer import CategoryScorer
from backend.core.daily_scoring_engine import DailyScoringEngine
from backend.data.storage_manager import StorageManager


# Test with 10 liquid stocks
TEST_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
    'NVDA', 'TSLA', 'JPM', 'V', 'WMT'
]


def test_pipeline():
    """Run full pipeline test."""
    
    print("\n" + "="*70)
    print("LRBF PIPELINE TEST - Real Data Validation")
    print("="*70)
    
    target_date = date.today()
    
    # Initialize services
    market_data = MarketDataService(data_source='yfinance')
    pattern_detector = PatternDetector()
    scorer = CategoryScorer()
    scoring_engine = DailyScoringEngine()
    storage = StorageManager()
    
    print(f"\nTarget Date: {target_date}")
    print(f"Test Universe: {len(TEST_TICKERS)} stocks")
    
    # STEP 1: Fetch market data
    print("\n" + "-"*70)
    print("STEP 1: Fetching Market Data")
    print("-"*70)
    
    stock_data = market_data.get_batch_data(TEST_TICKERS, days=7, interval='1m')
    
    if not stock_data:
        print("❌ No data fetched - aborting test")
        return
    
    print(f"✅ Fetched data for {len(stock_data)} stocks")
    
    # STEP 2: Detect patterns
    print("\n" + "-"*70)
    print("STEP 2: Detecting Patterns")
    print("-"*70)
    
    all_patterns = []
    processed_stocks = []
    
    for ticker, df in stock_data.items():
        print(f"\n📊 Analyzing {ticker}...")
        
        # Detect patterns
        patterns = pattern_detector.detect_all_patterns(df, ticker, target_date)
        
        if not patterns:
            print(f"   No patterns found")
            continue
        
        print(f"   Found {len(patterns)} patterns")
        
        # Count outcomes
        entries = len([p for p in patterns if p['entry_confirmed']])
        wins = len([p for p in patterns if p['outcome'] == 'win'])
        losses = len([p for p in patterns if p['outcome'] == 'loss'])
        
        print(f"   Entries: {entries} ({wins}W / {losses}L)")
        
        # Calculate avg cycle time
        confirmed = [p for p in patterns if p['entry_confirmed']]
        if confirmed:
            avg_cycle = sum(p['total_cycle_minutes'] for p in confirmed) / len(confirmed)
            print(f"   Avg Cycle Time: {avg_cycle:.1f} minutes")
        
        all_patterns.extend(patterns)
        
        # Aggregate for scoring (simplified - in real system use aggregator)
        stock_metrics = _aggregate_patterns(ticker, patterns, df)
        processed_stocks.append(stock_metrics)
    
    print(f"\n✅ Total patterns detected: {len(all_patterns)}")
    
    # STEP 3: Calculate scores
    print("\n" + "-"*70)
    print("STEP 3: Calculating Composite Scores")
    print("-"*70)
    
    for stock_metrics in processed_stocks:
        composite, category_scores = scorer.calculate_composite_score(stock_metrics)
        
        stock_metrics['composite_score'] = composite
        stock_metrics['category_scores'] = category_scores
        stock_metrics['patterns'] = [p for p in all_patterns if p['ticker'] == stock_metrics['ticker']]
        stock_metrics['today_patterns'] = stock_metrics['patterns']
        
        print(f"\n{stock_metrics['ticker']}: {composite:.1f}/100")
        print(f"   Expected Value: {category_scores['expected_value']:.1f}")
        print(f"   Execution Cycle: {category_scores['execution_cycle']:.1f}")
        print(f"   Dead Zone: {category_scores['dead_zone']:.1f}")
    
    # STEP 4: Store to database
    print("\n" + "-"*70)
    print("STEP 4: Storing to Database")
    print("-"*70)
    
    result = scoring_engine.run_daily_pipeline(processed_stocks, target_date)
    
    print(f"✅ Stored {len(result['daily_scores'])} daily scores")
    print(f"✅ Stored {result['patterns_stored']} patterns")
    
    if result['rankings']:
        print(f"✅ Generated top {len(result['rankings'])} rankings")
    
    # STEP 5: Display results
    print("\n" + "-"*70)
    print("STEP 5: Results Summary")
    print("-"*70)
    
    # Sort by composite score
    sorted_stocks = sorted(processed_stocks, key=lambda x: x['composite_score'], reverse=True)
    
    print("\n🏆 RANKED STOCKS:")
    print(f"{'Rank':<6} {'Ticker':<8} {'Score':<8} {'Cycle':<10} {'Patterns':<10}")
    print("-" * 50)
    
    for i, stock in enumerate(sorted_stocks, 1):
        ticker = stock['ticker']
        score = stock['composite_score']
        cycle_score = stock['category_scores']['execution_cycle']
        pattern_count = len(stock['patterns'])
        
        print(f"{i:<6} {ticker:<8} {score:<8.1f} {cycle_score:<10.1f} {pattern_count:<10}")
    
    # Storage stats
    print("\n📊 STORAGE STATS:")
    stats = storage.get_storage_stats()
    print(f"   Pattern files: {stats['pattern_files']}")
    print(f"   Pattern storage: {stats['pattern_storage_mb']:.2f} MB")
    print(f"   Database size: {stats['database_size_mb']:.2f} MB")
    print(f"   Daily score records: {stats['daily_score_records']}")
    
    print("\n" + "="*70)
    print("✅ PIPELINE TEST COMPLETE")
    print("="*70)
    
    return {
        'stocks_analyzed': len(processed_stocks),
        'patterns_detected': len(all_patterns),
        'rankings': sorted_stocks
    }


def _aggregate_patterns(ticker: str, patterns: List, df: pd.DataFrame) -> Dict:
    """Aggregate pattern data for scoring (simplified)."""
    
    if not patterns:
        return None
    
    # Count outcomes
    total = len(patterns)
    entries = [p for p in patterns if p['entry_confirmed']]
    wins = [p for p in patterns if p['outcome'] == 'win']
    losses = [p for p in patterns if p['outcome'] == 'loss']
    
    # Metrics
    win_rate = len(wins) / len(entries) if entries else 0
    avg_win_pct = sum(p['pnl_pct'] for p in wins) / len(wins) if wins else 0
    avg_loss_pct = abs(sum(p['pnl_pct'] for p in losses) / len(losses)) if losses else 0
    
    expected_value_pct = (win_rate * avg_win_pct) - ((1 - win_rate) * avg_loss_pct)
    
    # Timing metrics
    confirmed = [p for p in entries if 'total_cycle_minutes' in p]
    avg_cycle_time = sum(p['total_cycle_minutes'] for p in confirmed) / len(confirmed) if confirmed else 20
    avg_hold_time = sum(p['hold_time_minutes'] for p in confirmed) / len(confirmed) if confirmed else 15
    avg_bars_to_entry = sum(p['bars_to_entry'] for p in confirmed) / len(confirmed) if confirmed else 3
    
    # Dead zone
    dz_patterns = [p for p in patterns if p.get('dead_zone_duration', 0) > 0]
    dead_zone_frequency = (len(dz_patterns) / total * 100) if total > 0 else 0
    dead_zone_duration = sum(p['dead_zone_duration'] for p in dz_patterns) / len(dz_patterns) if dz_patterns else 0
    opportunity_cost = sum(p['opportunity_cost'] for p in dz_patterns) / len(dz_patterns) if dz_patterns else 0
    
    # Market metrics
    avg_volume = df['volume'].mean()
    atr_pct = ((df['high'] - df['low']) / df['close'] * 100).mean()
    
    return {
        'ticker': ticker,
        'wins_20d': len(wins),
        'losses_20d': len(losses),
        'avg_win_pct': avg_win_pct,
        'avg_loss_pct': avg_loss_pct,
        'confirmation_rate': len(entries) / total if total > 0 else 0,
        'expected_value_pct': expected_value_pct,
        'vwap_occurred_20d': total,
        'entries_20d': len(entries),
        'expected_daily_patterns': total / 7.0,  # 7 days of data
        'entries_per_day': len(entries) / 7.0,
        'win_rate': win_rate,
        'dead_zone_frequency': dead_zone_frequency,
        'dead_zone_duration': dead_zone_duration,
        'opportunity_cost': opportunity_cost,
        'avg_volume_20d': avg_volume,
        'spread_bps': 3.0,
        'spread_drift_std': 0.5,
        'atr_pct': atr_pct,
        'volatility_20d': df['close'].pct_change().std() * np.sqrt(252) * 100,
        'intraday_range_pct': atr_pct,
        'vwap_stability_score': 1.2,
        'vwap_distance_pct': 0.8,
        'avg_hold_time_minutes': avg_hold_time,
        'avg_bars_to_entry': avg_bars_to_entry,
        'time_to_target': avg_hold_time * 0.7,
        'slippage_avg_bps': 2.5,
        'fill_quality_score': 90.0,
        'false_positive_rate': (len(losses) / total * 100) if total > 0 else 30,
        'pattern_quality_score': 85.0,
        'max_drawdown_intraday': min(p['pnl_pct'] for p in patterns) if patterns else -1.5,
        'largest_loss_20d': min(p['pnl_pct'] for p in patterns) if patterns else -1.5,
        'days_to_earnings': 100,
        'news_event_density': 0,
        'avg_correlation': 0.5,
        'sector_classification': 'Tech',
        'halt_history': 0,
        'regulatory_flags': 0,
        'avg_gap_size': 0.5,
        'performance_consistency': 80.0,
        'forecast_accuracy_20d': 85.0,
        'missing_bars': 0.5,
        'anomaly_count': 0,
        'api_latency': 50.0,
        'total_cycle_minutes': avg_cycle_time,
        'avg_execution_latency_ms': 50.0,
        'settlement_lag_minutes': 0.5
    }


if __name__ == '__main__':
    import numpy as np  # Import for aggregation function
    
    test_pipeline()
