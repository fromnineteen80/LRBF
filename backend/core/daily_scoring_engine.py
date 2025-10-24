"""
Daily Scoring Engine - Calculate Per-Stock-Per-Day Composite Scores

Takes raw pattern data and generates daily composite scores for ranking.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

from datetime import date, datetime
from typing import Dict, List
import pandas as pd
import numpy as np

from backend.core.category_scorer import CategoryScorer
from backend.data.storage_manager import StorageManager


class DailyScoringEngine:
    """
    Calculates daily composite scores for all stocks.
    """
    
    def __init__(self):
        """Initialize scoring engine."""
        self.scorer = CategoryScorer()
        self.storage = StorageManager()
    
    def calculate_daily_scores(
        self,
        processed_stocks: List[Dict],
        target_date: date
    ) -> List[Dict]:
        """
        Calculate daily composite scores for all stocks.
        
        Args:
            processed_stocks: List of processed stock dictionaries from parallel processor
            target_date: Date for scoring
        
        Returns:
            List of daily score records
        """
        daily_scores = []
        
        for stock_result in processed_stocks:
            ticker = stock_result['ticker']
            composite_score = stock_result['composite_score']
            category_scores = stock_result['category_scores']
            
            # Build score record
            score_record = {
                'ticker': ticker,
                'date': target_date.isoformat(),
                'composite_score': composite_score,
                
                # Category scores
                'expected_value_score': category_scores['expected_value'],
                'pattern_frequency_score': category_scores['pattern_frequency'],
                'dead_zone_score': category_scores['dead_zone'],
                'liquidity_score': category_scores['liquidity'],
                'volatility_score': category_scores['volatility'],
                'vwap_stability_score': category_scores['vwap_stability'],
                'time_efficiency_score': category_scores['time_efficiency'],
                'slippage_score': category_scores['slippage'],
                'false_positive_score': category_scores['false_positive_rate'],
                'drawdown_score': category_scores['drawdown'],
                'news_risk_score': category_scores['news_risk'],
                'correlation_score': category_scores['correlation'],
                'halt_risk_score': category_scores['halt_risk'],
                'execution_cycle_score': category_scores['execution_cycle'],
                'historical_reliability_score': category_scores['historical_reliability'],
                'data_quality_score': category_scores['data_quality'],
                
                # Metadata
                'pattern_count': len(stock_result['today_patterns']),
                'daily_rank': 0  # Will be assigned after sorting
            }
            
            daily_scores.append(score_record)
        
        # Sort by composite score and assign ranks
        daily_scores.sort(key=lambda x: x['composite_score'], reverse=True)
        for i, record in enumerate(daily_scores, start=1):
            record['daily_rank'] = i
        
        return daily_scores
    
    def calculate_20_day_rankings(
        self,
        reference_date: date
    ) -> List[Dict]:
        """
        Calculate 20-day consistency rankings.
        
        Args:
            reference_date: Reference date for analysis
        
        Returns:
            List of ranking dictionaries (top 24 stocks)
        """
        # Load last 20 days of scores
        df = self.storage.get_last_20_days_scores(reference_date.isoformat())
        
        if df.empty:
            return []
        
        # Group by ticker and calculate consistency metrics
        rankings = []
        
        for ticker in df['ticker'].unique():
            ticker_df = df[df['ticker'] == ticker]
            
            # Must have at least 15 days of data
            if len(ticker_df) < 15:
                continue
            
            # Aggregated metrics
            avg_composite_score = ticker_df['composite_score'].mean()
            score_std_dev = ticker_df['composite_score'].std()
            avg_daily_rank = ticker_df['daily_rank'].mean()
            
            # Rank stability (lower std = more stable)
            rank_stability = 1.0 / (1.0 + ticker_df['daily_rank'].std())
            
            # Days in top 24
            days_in_top_24 = len(ticker_df[ticker_df['daily_rank'] <= 24])
            
            # Category for risk profile
            avg_volatility = ticker_df['volatility_score'].mean() if 'volatility_score' in ticker_df.columns else 75
            if avg_composite_score >= 88 and avg_volatility >= 85:
                category = 'Conservative'
            elif avg_composite_score >= 75:
                category = 'Medium'
            else:
                category = 'Aggressive'
            
            rankings.append({
                'ticker': ticker,
                'analysis_date': reference_date.isoformat(),
                'avg_composite_score': avg_composite_score,
                'score_std_dev': score_std_dev,
                'avg_daily_rank': avg_daily_rank,
                'rank_stability': rank_stability,
                'days_in_top_24': days_in_top_24,
                'category': category,
                'final_rank': 0  # Will be assigned after sorting
            })
        
        # Sort by consistency-weighted score
        # Prioritize: high avg score + low variance + consistent top-24 presence
        for rank_record in rankings:
            consistency_weight = (
                rank_record['avg_composite_score'] * 0.6 +
                rank_record['rank_stability'] * 100 * 0.2 +
                (rank_record['days_in_top_24'] / 20 * 100) * 0.2
            )
            rank_record['consistency_weight'] = consistency_weight
        
        rankings.sort(key=lambda x: x['consistency_weight'], reverse=True)
        
        # Assign final ranks (top 24)
        top_24 = rankings[:24]
        for i, record in enumerate(top_24, start=1):
            record['final_rank'] = i
        
        return top_24
    
    def run_daily_pipeline(
        self,
        processed_stocks: List[Dict],
        target_date: date
    ):
        """
        Run complete daily scoring pipeline.
        
        Args:
            processed_stocks: Processed stocks from parallel batch
            target_date: Date for analysis
        """
        print(f"\n📊 Running daily scoring pipeline for {target_date}...")
        
        # Step 1: Calculate daily scores
        print("   Calculating daily scores...")
        daily_scores = self.calculate_daily_scores(processed_stocks, target_date)
        
        # Step 2: Store daily scores
        print(f"   Storing {len(daily_scores)} daily scores...")
        self.storage.store_daily_scores(daily_scores)
        
        # Step 3: Store raw patterns
        print("   Storing raw patterns...")
        all_patterns = []
        for stock in processed_stocks:
            all_patterns.extend(stock['patterns'])
        self.storage.store_patterns(all_patterns, target_date.isoformat())
        
        # Step 4: Calculate 20-day rankings (if we have enough history)
        print("   Calculating 20-day rankings...")
        rankings = self.calculate_20_day_rankings(target_date)
        
        if rankings:
            print(f"   Top 24 stocks identified")
            self.storage.store_rankings(rankings, target_date.isoformat())
        else:
            print("   ⚠️  Not enough historical data for rankings yet")
        
        print(f"\n✅ Daily pipeline complete")
        
        return {
            'daily_scores': daily_scores,
            'rankings': rankings,
            'patterns_stored': len(all_patterns)
        }


# Convenience function
def run_daily_analysis(
    processed_stocks: List[Dict],
    target_date: date = None
) -> Dict:
    """
    Run daily analysis and store results.
    
    Args:
        processed_stocks: Processed stocks from batch analyzer
        target_date: Target date (default: today)
    
    Returns:
        Analysis results dictionary
    """
    if target_date is None:
        target_date = date.today()
    
    engine = DailyScoringEngine()
    return engine.run_daily_pipeline(processed_stocks, target_date)
