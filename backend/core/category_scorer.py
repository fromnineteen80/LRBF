"""
Category Scorer - 16-Category Comprehensive Stock Ranking System

Calculates composite scores for stock selection based on 16 weighted categories
across 5 tiers: Profitability, Execution, Risk, Portfolio, and System Confidence.

Each category scored 0-100 (higher = better) and weighted according to tier importance.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class CategoryScorer:
    """
    Calculates 16-category composite scores for stock ranking.
    
    TIER 1: Profitability & Pattern Quality (45%)
    TIER 2: Execution Quality (30%)
    TIER 3: Risk Management (15%)
    TIER 4: Portfolio Construction (7%)
    TIER 5: System Confidence (3%)
    """
    
    # Category weights (must sum to 1.0)
    WEIGHTS = {
        # TIER 1: Profitability & Pattern Quality (45%)
        'expected_value': 0.15,
        'pattern_frequency': 0.25,  # Occurrences are king
        'dead_zone': 0.05,
        
        # TIER 2: Execution Quality (30%)
        'liquidity': 0.10,
        'volatility': 0.10,
        'vwap_stability': 0.05,
        'time_efficiency': 0.05,
        
        # TIER 3: Risk Management (15%)
        'slippage': 0.05,
        'false_positive_rate': 0.04,
        'drawdown': 0.03,
        'news_risk': 0.03,
        
        # TIER 4: Portfolio Construction (7%)
        'correlation': 0.03,
        'halt_risk': 0.02,
        'execution_cycle': 0.02,
        
        # TIER 5: System Confidence (3%)
        'historical_reliability': 0.02,
        'data_quality': 0.01
    }
    
    def __init__(self):
        """Initialize category scorer."""
        assert abs(sum(self.WEIGHTS.values()) - 1.0) < 0.001, "Weights must sum to 1.0"
    
    # ========================================================================
    # TIER 1: PROFITABILITY & PATTERN QUALITY (45%)
    # ========================================================================
    
    def score_expected_value(self, stock_data: Dict) -> float:
        """
        Expected Value Score (15% weight)
        
        EV = win_rate × avg_win - loss_rate × avg_loss
        
        Inputs from stock_data:
        - wins_20d: Number of winning trades
        - losses_20d: Number of losing trades
        - avg_win_pct: Average win size (%)
        - avg_loss_pct: Average loss size (%)
        - confirmation_rate: % of patterns that became entries
        
        Target: EV > 0.5% per trade
        Scale: 0-100 (higher = better)
        """
        wins = stock_data.get('wins_20d', 0)
        losses = stock_data.get('losses_20d', 0)
        total_trades = wins + losses
        
        if total_trades == 0:
            return 0.0
        
        win_rate = wins / total_trades
        loss_rate = losses / total_trades
        
        avg_win = stock_data.get('avg_win_pct', 0.0)
        avg_loss = abs(stock_data.get('avg_loss_pct', 0.0))
        
        # Calculate expected value
        ev = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        # Scale to 0-100
        # Target: 0.5% = 80 points, 1.0% = 100 points
        if ev >= 1.0:
            score = 100.0
        elif ev >= 0.5:
            score = 80.0 + ((ev - 0.5) / 0.5) * 20.0
        elif ev > 0:
            score = (ev / 0.5) * 80.0
        else:
            score = 0.0
        
        return min(100.0, max(0.0, score))
    
    def score_pattern_frequency(self, stock_data: Dict) -> float:
        """
        Pattern Frequency Score (25% weight) - OCCURRENCES ARE KING
        
        Multi-tier professional analysis of tradeable opportunity density.
        Focus: Maximum daily opportunities + quality confirmation + even distribution.
        
        Inputs:
        - vwap_occurred_20d: Total patterns detected
        - entries_20d: Confirmed entries (patterns that met thresholds)
        - confirmation_rate: % of patterns that became trades
        - pattern_distribution_score: Evenness of patterns throughout day (0-1)
        
        3-tier scoring:
        - Daily Occurrence Rate (60%): MORE = BETTER (more compounding opportunities)
        - Entry Confirmation Rate (20%): Pattern quality filter
        - Distribution Consistency (20%): Patterns spread evenly vs clustered
        
        Target: 4-8+ entries/day (high occurrence), 50%+ confirmation, even distribution
        Scale: 0-100 (higher = better)
        """
        entries_20d = stock_data.get('entries_20d', 0)
        occurred_20d = stock_data.get('vwap_occurred_20d', 0)
        confirmation_rate = stock_data.get('confirmation_rate', 0.0)  # 0-100
        
        # Calculate daily rates
        daily_entries = entries_20d / 20.0 if entries_20d > 0 else 0.0
        
        # === 1. Daily Occurrence Rate (60% weight) ===
        # MORE OCCURRENCES = MORE COMPOUNDING = KING
        # No penalty for "too many" - confirmation rate filters quality
        if daily_entries >= 8.0:
            occurrence_score = 100.0  # Elite: 8+ entries/day
        elif daily_entries >= 6.0:
            occurrence_score = 92.0 + ((daily_entries - 6.0) / 2.0) * 8.0  # Excellent: 6-8/day
        elif daily_entries >= 4.0:
            occurrence_score = 80.0 + ((daily_entries - 4.0) / 2.0) * 12.0  # Very good: 4-6/day
        elif daily_entries >= 3.0:
            occurrence_score = 65.0 + ((daily_entries - 3.0) / 1.0) * 15.0  # Good: 3-4/day
        elif daily_entries >= 2.0:
            occurrence_score = 45.0 + ((daily_entries - 2.0) / 1.0) * 20.0  # Acceptable: 2-3/day
        elif daily_entries >= 1.0:
            occurrence_score = 20.0 + ((daily_entries - 1.0) / 1.0) * 25.0  # Marginal: 1-2/day
        else:
            occurrence_score = (daily_entries / 1.0) * 20.0  # Poor: <1/day
        
        # === 2. Entry Confirmation Rate (20% weight) ===
        # Filters quality - high rate = real patterns, not noise
        # This is why we don't penalize high occurrence - confirmation filters it
        if confirmation_rate >= 65.0:
            confirmation_score = 100.0  # Elite quality
        elif confirmation_rate >= 55.0:
            confirmation_score = 88.0 + ((confirmation_rate - 55.0) / 10.0) * 12.0  # Excellent
        elif confirmation_rate >= 45.0:
            confirmation_score = 72.0 + ((confirmation_rate - 45.0) / 10.0) * 16.0  # Good
        elif confirmation_rate >= 35.0:
            confirmation_score = 52.0 + ((confirmation_rate - 35.0) / 10.0) * 20.0  # Acceptable
        elif confirmation_rate >= 25.0:
            confirmation_score = 30.0 + ((confirmation_rate - 25.0) / 10.0) * 22.0  # Marginal
        else:
            confirmation_score = (confirmation_rate / 25.0) * 30.0  # Poor (too many false signals)
        
        # === 3. Distribution Consistency (20% weight) ===
        # Even distribution = continuous compounding, less idle capital
        distribution_score_raw = stock_data.get('pattern_distribution_score', 0.7)  # 0-1
        
        if distribution_score_raw >= 0.85:
            distribution_score = 100.0  # Very even
        elif distribution_score_raw >= 0.75:
            distribution_score = 88.0 + ((distribution_score_raw - 0.75) / 0.1) * 12.0
        elif distribution_score_raw >= 0.65:
            distribution_score = 72.0 + ((distribution_score_raw - 0.65) / 0.1) * 16.0
        elif distribution_score_raw >= 0.50:
            distribution_score = 50.0 + ((distribution_score_raw - 0.50) / 0.15) * 22.0
        else:
            distribution_score = (distribution_score_raw / 0.50) * 50.0
        
        # === Composite Pattern Frequency Score ===
        # 60% occurrence (MORE = BETTER), 20% confirmation (quality filter), 20% distribution
        score = (occurrence_score * 0.60) + (confirmation_score * 0.20) + (distribution_score * 0.20)
        
        return min(100.0, max(0.0, score))
    
    def score_dead_zone(self, stock_data: Dict) -> float:
        """
        Dead Zone Score (15% weight)
        
        Capital efficiency & opportunity cost from idle periods.
        
        Inputs:
        - dead_zone_frequency: % of trades with dead zones (lower = better)
        - dead_zone_duration: Avg minutes idle (lower = better)
        - opportunity_cost: Avg $ lost from idle capital (lower = better)
        
        3-tier scoring:
        - Frequency (40%): How often do dead zones occur?
        - Duration (30%): How long do they last?
        - Opp Cost (30%): How much $ is lost?
        
        Target: Severity < 35/100
        Scale: 0-100 (higher = better, inverted from severity)
        """
        frequency = stock_data.get('dead_zone_frequency', 0.0)  # 0-100 (lower = better)
        duration = stock_data.get('dead_zone_duration', 0.0)     # minutes
        opp_cost = stock_data.get('opportunity_cost', 0.0)       # dollars
        
        # Frequency subscore (40% weight)
        # Target: < 20% = excellent, 20-35% = good, > 50% = poor
        if frequency <= 20:
            freq_score = 100.0
        elif frequency <= 35:
            freq_score = 100.0 - ((frequency - 20) / 15) * 20.0
        else:
            freq_score = max(0.0, 80.0 - ((frequency - 35) * 2.0))
        
        # Duration subscore (30% weight)
        # Target: < 5 min = excellent, 5-10 min = good, > 15 min = poor
        if duration <= 5:
            dur_score = 100.0
        elif duration <= 10:
            dur_score = 100.0 - ((duration - 5) / 5) * 20.0
        else:
            dur_score = max(0.0, 80.0 - ((duration - 10) * 4.0))
        
        # Opportunity cost subscore (30% weight)
        # Target: < $20 = excellent, $20-$50 = good, > $80 = poor
        if opp_cost <= 20:
            cost_score = 100.0
        elif opp_cost <= 50:
            cost_score = 100.0 - ((opp_cost - 20) / 30) * 20.0
        else:
            cost_score = max(0.0, 80.0 - ((opp_cost - 50) * 1.6))
        
        # Composite dead zone score
        score = (freq_score * 0.4) + (dur_score * 0.3) + (cost_score * 0.3)
        
        return min(100.0, max(0.0, score))
    
    # ========================================================================
    # TIER 2: EXECUTION QUALITY (30%)
    # ========================================================================
    
    def score_liquidity(self, stock_data: Dict) -> float:
        """
        Liquidity Score (10% weight)
        
        Volume depth & spread tightness for easy entry/exit.
        
        Inputs:
        - avg_volume_20d: Average daily volume
        - spread_bps: Bid-ask spread in basis points
        - spread_drift_std: Spread volatility
        
        Target: Volume > 5M/day, spread < 5 bps
        Scale: 0-100 (higher = better)
        """
        volume = stock_data.get('avg_volume_20d', 0) / 1_000_000  # Convert to millions
        spread_bps = stock_data.get('spread_bps', 100.0)
        
        # Volume subscore (60%)
        if volume >= 10:
            vol_score = 100.0
        elif volume >= 5:
            vol_score = 80.0 + ((volume - 5) / 5) * 20.0
        elif volume >= 2:
            vol_score = 50.0 + ((volume - 2) / 3) * 30.0
        else:
            vol_score = (volume / 2) * 50.0
        
        # Spread subscore (40%)
        if spread_bps <= 3:
            spread_score = 100.0
        elif spread_bps <= 5:
            spread_score = 100.0 - ((spread_bps - 3) / 2) * 20.0
        elif spread_bps <= 10:
            spread_score = 80.0 - ((spread_bps - 5) / 5) * 40.0
        else:
            spread_score = max(0.0, 40.0 - ((spread_bps - 10) * 2.0))
        
        score = (vol_score * 0.6) + (spread_score * 0.4)
        return min(100.0, max(0.0, score))
    
    def score_volatility(self, stock_data: Dict) -> float:
        """
        Volatility Score (10% weight)
        
        ATR-based adaptive threshold matching.
        Match stock volatility to strategy (not too quiet, not too choppy).
        
        Inputs:
        - atr_pct: Average True Range as % of price
        - volatility_20d: Rolling volatility
        - intraday_range_pct: Avg high-low range
        
        Target: ATR 1.5%-3.5% (sweet spot)
        Scale: 0-100 (higher = better)
        """
        atr_pct = stock_data.get('atr_pct', 0.0)
        
        # Sweet spot scoring
        if 1.5 <= atr_pct <= 3.5:
            score = 100.0
        elif 1.0 <= atr_pct < 1.5:
            score = 70.0 + ((atr_pct - 1.0) / 0.5) * 30.0
        elif 3.5 < atr_pct <= 5.0:
            score = 100.0 - ((atr_pct - 3.5) / 1.5) * 20.0
        elif atr_pct > 5.0:
            # Too volatile
            score = max(0.0, 80.0 - ((atr_pct - 5.0) * 10.0))
        else:
            # Too quiet
            score = (atr_pct / 1.0) * 70.0
        
        return min(100.0, max(0.0, score))
    
    def score_vwap_stability(self, stock_data: Dict) -> float:
        """
        VWAP Stability Score (5% weight)
        
        Pattern cleanliness - clean VWAP = reliable patterns, less noise.
        
        Inputs:
        - vwap_stability_score: Consistency metric
        - vwap_distance_pct: How far price strays from VWAP
        
        Target: Stability score < 1.5%
        Scale: 0-100 (higher = better, lower stability value = better)
        """
        stability = stock_data.get('vwap_stability_score', 5.0)
        
        if stability <= 1.0:
            score = 100.0
        elif stability <= 1.5:
            score = 100.0 - ((stability - 1.0) / 0.5) * 20.0
        elif stability <= 2.5:
            score = 80.0 - ((stability - 1.5) / 1.0) * 40.0
        else:
            score = max(0.0, 40.0 - ((stability - 2.5) * 10.0))
        
        return min(100.0, max(0.0, score))
    
    def score_time_efficiency(self, stock_data: Dict) -> float:
        """
        Time Efficiency Score (5% weight)
        
        Multi-tier professional analysis of capital turnover speed.
        Focus: Fast compounding + quick wins + capital efficiency.
        
        Inputs:
        - avg_hold_time_minutes: Average position duration
        - avg_bars_to_entry: Bars needed for pattern confirmation
        - time_to_target_minutes: Average time to hit profit target
        - capital_idle_rate: % of trading day capital is unused (lower = better)
        - win_speed_vs_loss_speed: Ratio of time to win vs time to loss
        
        3-tier scoring:
        - Position Duration (35%): Fast trade resolution
        - Entry Confirmation Speed (30%): Quick pattern validation
        - Target Achievement Time (35%): Rapid profit realization
        
        Target: Hold <12 min, confirm <3 bars, target <10 min
        Scale: 0-100 (higher = better)
        """
        hold_time = stock_data.get('avg_hold_time_minutes', 30.0)
        bars_to_entry = stock_data.get('avg_bars_to_entry', 5.0)  # 1-min bars
        time_to_target = stock_data.get('time_to_target_minutes', 20.0)
        
        # === 1. Position Duration (35% weight) ===
        # Fast resolution = more opportunities to compound per day
        if hold_time <= 8:
            duration_score = 100.0  # Elite speed (8 min avg)
        elif hold_time <= 12:
            duration_score = 90.0 + ((12 - hold_time) / 4) * 10.0  # Excellent
        elif hold_time <= 18:
            duration_score = 75.0 + ((18 - hold_time) / 6) * 15.0  # Good
        elif hold_time <= 25:
            duration_score = 55.0 + ((25 - hold_time) / 7) * 20.0  # Acceptable
        elif hold_time <= 35:
            duration_score = 30.0 + ((35 - hold_time) / 10) * 25.0  # Marginal
        else:
            duration_score = max(0.0, 30.0 - ((hold_time - 35) * 1.5))  # Poor
        
        # === 2. Entry Confirmation Speed (30% weight) ===
        # Fast confirmation = less capital idle, more entries per day
        # With 1-min bars, 2-3 bars = 2-3 minutes confirmation
        if bars_to_entry <= 2:
            entry_speed_score = 100.0  # Very fast (2 min)
        elif bars_to_entry <= 3:
            entry_speed_score = 88.0 + ((3 - bars_to_entry) / 1) * 12.0  # Fast
        elif bars_to_entry <= 5:
            entry_speed_score = 70.0 + ((5 - bars_to_entry) / 2) * 18.0  # Good
        elif bars_to_entry <= 8:
            entry_speed_score = 50.0 + ((8 - bars_to_entry) / 3) * 20.0  # Acceptable
        elif bars_to_entry <= 12:
            entry_speed_score = 25.0 + ((12 - bars_to_entry) / 4) * 25.0  # Slow
        else:
            entry_speed_score = max(0.0, 25.0 - ((bars_to_entry - 12) * 2.0))  # Very slow
        
        # === 3. Target Achievement Time (35% weight) ===
        # Fast profit realization = reduced risk exposure, faster compounding
        if time_to_target <= 7:
            target_speed_score = 100.0  # Elite (7 min to profit)
        elif time_to_target <= 10:
            target_speed_score = 90.0 + ((10 - time_to_target) / 3) * 10.0  # Excellent
        elif time_to_target <= 15:
            target_speed_score = 75.0 + ((15 - time_to_target) / 5) * 15.0  # Good
        elif time_to_target <= 22:
            target_speed_score = 55.0 + ((22 - time_to_target) / 7) * 20.0  # Acceptable
        elif time_to_target <= 30:
            target_speed_score = 30.0 + ((30 - time_to_target) / 8) * 25.0  # Marginal
        else:
            target_speed_score = max(0.0, 30.0 - ((time_to_target - 30) * 1.5))  # Poor
        
        # Boost for favorable win speed vs loss speed ratio
        # Winners that hit fast and losers that exit fast = ideal
        speed_ratio = stock_data.get('win_speed_vs_loss_speed', 1.0)  # >1 = wins faster than losses
        if speed_ratio >= 1.5:
            speed_boost = 10.0  # Wins much faster than losses
        elif speed_ratio >= 1.2:
            speed_boost = 5.0  # Wins faster than losses
        else:
            speed_boost = 0.0
        
        target_speed_score = min(100.0, target_speed_score + speed_boost)
        
        # === Composite Time Efficiency Score ===
        score = (duration_score * 0.35) + (entry_speed_score * 0.30) + (target_speed_score * 0.35)
        
        return min(100.0, max(0.0, score))
    
    # ========================================================================
    # TIER 3: RISK MANAGEMENT (15%)
    # ========================================================================
    
    def score_slippage(self, stock_data: Dict) -> float:
        """
        Slippage Score (5% weight)
        
        Multi-tier professional analysis of execution cost leakage.
        Focus: Minimize cost drag + predictable execution + curve preservation.
        
        Inputs:
        - slippage_avg_bps: Average slippage in basis points
        - slippage_std_dev: Slippage consistency (std dev in bps)
        - positive_slippage_rate: % of trades with favorable slippage
        - market_impact_bps: Price movement caused by our order
        - fill_quality_score: Overall execution quality (0-1)
        
        3-tier scoring:
        - Slippage Magnitude (35%): Average cost drag per trade
        - Slippage Consistency (30%): Predictability of execution costs
        - Market Impact (35%): Order size vs liquidity balance
        
        Target: <2 bps avg, <1.5 bps std dev, minimal market impact
        Scale: 0-100 (higher = better)
        """
        slippage_bps = stock_data.get('slippage_avg_bps', 10.0)
        slippage_std = stock_data.get('slippage_std_dev', 3.0)  # Std dev in bps
        market_impact = stock_data.get('market_impact_bps', 5.0)
        
        # === 1. Slippage Magnitude (35% weight) ===
        # Average slippage = hidden tax on every trade
        # Lower = better (preserve the curve)
        if slippage_bps <= 1.5:
            magnitude_score = 100.0  # Elite execution
        elif slippage_bps <= 2.5:
            magnitude_score = 90.0 + ((2.5 - slippage_bps) / 1.0) * 10.0  # Excellent
        elif slippage_bps <= 3.5:
            magnitude_score = 78.0 + ((3.5 - slippage_bps) / 1.0) * 12.0  # Very good
        elif slippage_bps <= 5.0:
            magnitude_score = 60.0 + ((5.0 - slippage_bps) / 1.5) * 18.0  # Good
        elif slippage_bps <= 7.0:
            magnitude_score = 40.0 + ((7.0 - slippage_bps) / 2.0) * 20.0  # Acceptable
        elif slippage_bps <= 10.0:
            magnitude_score = 20.0 + ((10.0 - slippage_bps) / 3.0) * 20.0  # Marginal
        else:
            magnitude_score = max(0.0, 20.0 - ((slippage_bps - 10.0) * 2.0))  # Poor
        
        # Boost for positive slippage (price improvement)
        positive_rate = stock_data.get('positive_slippage_rate', 0.15)  # 0-1
        if positive_rate >= 0.25:
            positive_boost = 10.0  # Frequent price improvement
        elif positive_rate >= 0.15:
            positive_boost = 5.0
        else:
            positive_boost = 0.0
        
        magnitude_score = min(100.0, magnitude_score + positive_boost)
        
        # === 2. Slippage Consistency (30% weight) ===
        # Predictable slippage = budgetable costs, no surprises
        # Low std dev = consistent execution quality
        if slippage_std <= 1.0:
            consistency_score = 100.0  # Very consistent
        elif slippage_std <= 1.5:
            consistency_score = 88.0 + ((1.5 - slippage_std) / 0.5) * 12.0  # Consistent
        elif slippage_std <= 2.5:
            consistency_score = 70.0 + ((2.5 - slippage_std) / 1.0) * 18.0  # Good
        elif slippage_std <= 4.0:
            consistency_score = 50.0 + ((4.0 - slippage_std) / 1.5) * 20.0  # Acceptable
        elif slippage_std <= 6.0:
            consistency_score = 25.0 + ((6.0 - slippage_std) / 2.0) * 25.0  # Inconsistent
        else:
            consistency_score = max(0.0, 25.0 - ((slippage_std - 6.0) * 3.0))  # Very inconsistent
        
        # === 3. Market Impact (35% weight) ===
        # Does our order size move the market?
        # Low impact = liquidity matches our size, no adverse selection
        if market_impact <= 1.5:
            impact_score = 100.0  # Negligible impact
        elif market_impact <= 2.5:
            impact_score = 90.0 + ((2.5 - market_impact) / 1.0) * 10.0  # Very low
        elif market_impact <= 4.0:
            impact_score = 75.0 + ((4.0 - market_impact) / 1.5) * 15.0  # Low
        elif market_impact <= 6.0:
            impact_score = 55.0 + ((6.0 - market_impact) / 2.0) * 20.0  # Moderate
        elif market_impact <= 9.0:
            impact_score = 30.0 + ((9.0 - market_impact) / 3.0) * 25.0  # Noticeable
        else:
            impact_score = max(0.0, 30.0 - ((market_impact - 9.0) * 3.0))  # Significant
        
        # Adjustment from fill quality score
        fill_quality = stock_data.get('fill_quality_score', 0.75)  # 0-1
        if fill_quality >= 0.85:
            quality_boost = 5.0
        elif fill_quality >= 0.75:
            quality_boost = 2.0
        else:
            quality_boost = 0.0
        
        impact_score = min(100.0, impact_score + quality_boost)
        
        # === Composite Slippage Score ===
        score = (magnitude_score * 0.35) + (consistency_score * 0.30) + (impact_score * 0.35)
        
        return min(100.0, max(0.0, score))
    
    def score_false_positive_rate(self, stock_data: Dict) -> float:
        """
        False Positive Rate Score (4% weight) - Risk Tier
        
        Multi-tier professional analysis of pattern reliability and signal quality.
        Focus: Reduce losing trades from bad signals + protect curve + minimize whipsaw costs.
        
        Inputs:
        - pattern_failure_rate: % of patterns that don't complete (false signals)
        - whipsaw_cost_total: $ lost to false positive trades over 20 days
        - recovery_after_false: Days to first win after false positive
        - false_positive_frequency: How often false signals occur per day
        
        3-tier scoring:
        - Pattern Failure Rate (40%): % of detected patterns that fail to complete
        - Whipsaw Cost (35%): Dollar damage from false signals
        - Recovery After False (25%): Speed to resume winning after false positive
        
        Target: <25% failure rate, <$100 whipsaw cost, recover within 1 day
        Scale: 0-100 (higher = better)
        """
        failure_rate = stock_data.get('pattern_failure_rate', 40.0)  # % (lower = better)
        whipsaw_cost = stock_data.get('whipsaw_cost_total', 150.0)   # $ (lower = better)
        recovery_days = stock_data.get('recovery_after_false', 2.5)  # days (lower = better)
        
        # === 1. Pattern Failure Rate (40% weight) ===
        # Lower failure rate = more reliable signals = fewer losing trades
        if failure_rate <= 15:
            failure_score = 100.0  # Elite reliability
        elif failure_rate <= 25:
            failure_score = 90.0 + ((25 - failure_rate) / 10) * 10.0  # Excellent
        elif failure_rate <= 35:
            failure_score = 75.0 + ((35 - failure_rate) / 10) * 15.0  # Good
        elif failure_rate <= 45:
            failure_score = 55.0 + ((45 - failure_rate) / 10) * 20.0  # Acceptable
        elif failure_rate <= 60:
            failure_score = 30.0 + ((60 - failure_rate) / 15) * 25.0  # Marginal
        else:
            failure_score = max(0.0, 30.0 - ((failure_rate - 60) * 1.5))  # Poor
        
        # === 2. Whipsaw Cost (35% weight) ===
        # Dollar cost of false signals = hidden drag on curve
        # Lower cost = less capital erosion from bad signals
        if whipsaw_cost <= 50:
            cost_score = 100.0  # Minimal damage
        elif whipsaw_cost <= 100:
            cost_score = 90.0 + ((100 - whipsaw_cost) / 50) * 10.0  # Low damage
        elif whipsaw_cost <= 150:
            cost_score = 75.0 + ((150 - whipsaw_cost) / 50) * 15.0  # Moderate
        elif whipsaw_cost <= 225:
            cost_score = 55.0 + ((225 - whipsaw_cost) / 75) * 20.0  # Acceptable
        elif whipsaw_cost <= 325:
            cost_score = 30.0 + ((325 - whipsaw_cost) / 100) * 25.0  # High damage
        else:
            cost_score = max(0.0, 30.0 - ((whipsaw_cost - 325) * 0.15))  # Severe damage
        
        # === 3. Recovery After False (25% weight) ===
        # How quickly wins resume after false positive
        # Fast recovery = resilient performance, curve preserved
        if recovery_days <= 0.5:
            recovery_score = 100.0  # Immediate recovery
        elif recovery_days <= 1.0:
            recovery_score = 90.0 + ((1.0 - recovery_days) / 0.5) * 10.0  # Very fast
        elif recovery_days <= 1.5:
            recovery_score = 78.0 + ((1.5 - recovery_days) / 0.5) * 12.0  # Fast
        elif recovery_days <= 2.5:
            recovery_score = 60.0 + ((2.5 - recovery_days) / 1.0) * 18.0  # Moderate
        elif recovery_days <= 4.0:
            recovery_score = 38.0 + ((4.0 - recovery_days) / 1.5) * 22.0  # Slow
        else:
            recovery_score = max(0.0, 38.0 - ((recovery_days - 4.0) * 8.0))  # Very slow
        
        # Penalty for high false positive frequency
        fp_frequency = stock_data.get('false_positive_frequency', 1.0)  # per day
        if fp_frequency > 2.5:
            frequency_penalty = 10.0  # Too many false signals
        elif fp_frequency > 1.5:
            frequency_penalty = 5.0
        else:
            frequency_penalty = 0.0
        
        # === Composite False Positive Score ===
        score = (failure_score * 0.40) + (cost_score * 0.35) + (recovery_score * 0.25)
        score = max(0.0, score - frequency_penalty)
        
        return min(100.0, max(0.0, score))
    
    def score_drawdown(self, stock_data: Dict) -> float:
        """
        Drawdown Score (3% weight) - Risk Tier
        
        Multi-tier professional analysis of downside risk and recovery capability.
        Focus: Stocks that recover quickly preserve compounding curve.
        
        Inputs:
        - max_drawdown_magnitude: Deepest loss from peak (%)
        - drawdown_frequency: Number of drawdown events per 20 days
        - recovery_speed_days: Average days to recover from drawdown to new high
        - drawdown_duration_avg: Average time spent in drawdown (days)
        
        3-tier scoring:
        - Max Drawdown Magnitude (35%): Worst peak-to-trough decline
        - Drawdown Frequency (30%): How often drawdowns occur
        - Recovery Speed (35%): Days to recover from drawdown
        
        Target: <1.5% max DD, <3 drawdowns/20 days, recover within 2 days
        Scale: 0-100 (higher = better)
        """
        max_dd = abs(stock_data.get('max_drawdown_magnitude', 3.5))  # % (lower = better)
        dd_frequency = stock_data.get('drawdown_frequency', 5.0)     # count (lower = better)
        recovery_days = stock_data.get('recovery_speed_days', 3.5)   # days (lower = better)
        
        # === 1. Max Drawdown Magnitude (35% weight) ===
        # Smaller drawdowns = less capital at risk = curve preserved
        if max_dd <= 1.0:
            magnitude_score = 100.0  # Minimal drawdown
        elif max_dd <= 1.5:
            magnitude_score = 92.0 + ((1.5 - max_dd) / 0.5) * 8.0  # Very small
        elif max_dd <= 2.0:
            magnitude_score = 82.0 + ((2.0 - max_dd) / 0.5) * 10.0  # Small
        elif max_dd <= 2.75:
            magnitude_score = 68.0 + ((2.75 - max_dd) / 0.75) * 14.0  # Moderate
        elif max_dd <= 3.5:
            magnitude_score = 50.0 + ((3.5 - max_dd) / 0.75) * 18.0  # Acceptable
        elif max_dd <= 5.0:
            magnitude_score = 28.0 + ((5.0 - max_dd) / 1.5) * 22.0  # High
        else:
            magnitude_score = max(0.0, 28.0 - ((max_dd - 5.0) * 4.0))  # Severe
        
        # === 2. Drawdown Frequency (30% weight) ===
        # Fewer drawdowns = more stable performance = predictable curve
        if dd_frequency <= 2:
            frequency_score = 100.0  # Very rare
        elif dd_frequency <= 3:
            frequency_score = 90.0 + ((3 - dd_frequency) / 1) * 10.0  # Rare
        elif dd_frequency <= 5:
            frequency_score = 75.0 + ((5 - dd_frequency) / 2) * 15.0  # Infrequent
        elif dd_frequency <= 7:
            frequency_score = 58.0 + ((7 - dd_frequency) / 2) * 17.0  # Moderate
        elif dd_frequency <= 10:
            frequency_score = 35.0 + ((10 - dd_frequency) / 3) * 23.0  # Frequent
        else:
            frequency_score = max(0.0, 35.0 - ((dd_frequency - 10) * 3.5))  # Very frequent
        
        # === 3. Recovery Speed (35% weight) ===
        # Fast recovery = resilient performance = compounding resumes quickly
        if recovery_days <= 1.5:
            recovery_score = 100.0  # Very fast recovery
        elif recovery_days <= 2.5:
            recovery_score = 90.0 + ((2.5 - recovery_days) / 1.0) * 10.0  # Fast
        elif recovery_days <= 3.5:
            recovery_score = 77.0 + ((3.5 - recovery_days) / 1.0) * 13.0  # Moderate
        elif recovery_days <= 5.0:
            recovery_score = 60.0 + ((5.0 - recovery_days) / 1.5) * 17.0  # Acceptable
        elif recovery_days <= 7.5:
            recovery_score = 38.0 + ((7.5 - recovery_days) / 2.5) * 22.0  # Slow
        else:
            recovery_score = max(0.0, 38.0 - ((recovery_days - 7.5) * 5.0))  # Very slow
        
        # Boost for consistent shallow drawdowns
        drawdown_consistency = stock_data.get('drawdown_consistency', 0.6)  # 0-1, higher = better
        if drawdown_consistency >= 0.80:
            consistency_boost = 8.0  # Very consistent (predictable risk)
        elif drawdown_consistency >= 0.70:
            consistency_boost = 4.0  # Consistent
        else:
            consistency_boost = 0.0
        
        # === Composite Drawdown Score ===
        score = (magnitude_score * 0.35) + (frequency_score * 0.30) + (recovery_score * 0.35)
        score = min(100.0, score + consistency_boost)
        
        return min(100.0, max(0.0, score))
    
    def score_news_risk(self, stock_data: Dict) -> float:
        """
        News Risk Score (3% weight)
        
        Earnings/events exposure - avoid mid-pattern news bombs.
        
        Inputs:
        - days_to_earnings: Days until next earnings
        - news_event_density: Recent news volume
        
        Target: No earnings within 3 days
        Scale: 0-100 (higher = better)
        """
        days_to_earnings = stock_data.get('days_to_earnings', 100)
        
        if days_to_earnings >= 7:
            score = 100.0
        elif days_to_earnings >= 3:
            score = 80.0 + ((days_to_earnings - 3) / 4) * 20.0
        elif days_to_earnings >= 1:
            score = 40.0 + ((days_to_earnings - 1) / 2) * 40.0
        else:
            score = 0.0  # Avoid trading on earnings day
        
        return min(100.0, max(0.0, score))
    
    # ========================================================================
    # TIER 4: PORTFOLIO CONSTRUCTION (7%)
    # ========================================================================
    
    def score_correlation(self, stock_data: Dict, selected_stocks: List[str] = None) -> float:
        """
        Correlation Score (3% weight)
        
        Diversification benefit - don't pick 8 tech stocks (all move together).
        
        Inputs:
        - correlation_matrix: Correlation with other candidates
        - sector_exposure: Industry classification
        
        Target: Max 0.7 correlation with other selections
        Scale: 0-100 (higher = better)
        """
        # If no other stocks selected yet, give perfect score
        if not selected_stocks:
            return 100.0
        
        avg_correlation = stock_data.get('avg_correlation', 0.5)
        
        if avg_correlation <= 0.5:
            score = 100.0
        elif avg_correlation <= 0.7:
            score = 100.0 - ((avg_correlation - 0.5) / 0.2) * 30.0
        elif avg_correlation <= 0.85:
            score = 70.0 - ((avg_correlation - 0.7) / 0.15) * 40.0
        else:
            score = max(0.0, 30.0 - ((avg_correlation - 0.85) * 100.0))
        
        return min(100.0, max(0.0, score))
    
    def score_halt_risk(self, stock_data: Dict) -> float:
        """
        Halt Risk Score (2% weight)
        
        Trading suspension risk - halts kill positions instantly.
        
        Inputs:
        - halt_history: Number of halts in recent period
        - regulatory_flags: Any compliance issues
        - avg_gap_size: Overnight gap volatility
        
        Target: Zero halts in 20-day history
        Scale: 0-100 (higher = better)
        """
        halt_count = stock_data.get('halt_history', 0)
        
        if halt_count == 0:
            score = 100.0
        elif halt_count == 1:
            score = 50.0
        else:
            score = max(0.0, 50.0 - ((halt_count - 1) * 20.0))
        
        return min(100.0, max(0.0, score))
    
def score_execution_cycle(self, stock_data: Dict) -> float:
        """
        Execution Cycle Feasibility Score (2% weight) - REPLACES Sector Balance
        
        Evaluates if there's enough time for full intraminute trade cycle.
        
        Full Cycle: VWAP detection → pattern confirmation → entry execution 
                   → hold to target/stop → exit execution → cash settlement
        
        Inputs:
        - avg_bars_to_entry: Minutes until pattern confirms
        - avg_hold_time_minutes: Time from entry to exit
        - avg_execution_latency_ms: Order fill speed (entry + exit)
        - settlement_lag_minutes: Cash availability delay
        
        Total Cycle = detection + entry_latency + hold + exit_latency + settlement
        
        Target: < 12 minutes (can do 15+ trades/day)
        Scale: 0-100 (higher = better, faster cycles = more opportunities)
        """
        # Component times
        bars_to_entry = stock_data.get('avg_bars_to_entry', 3.0)  # minutes
        hold_time = stock_data.get('avg_hold_time_minutes', 15.0)  # minutes
        entry_latency = stock_data.get('avg_execution_latency_ms', 50.0) / 1000 / 60  # ms to minutes
        exit_latency = entry_latency  # Assume similar
        settlement_lag = stock_data.get('settlement_lag_minutes', 0.5)  # minutes
        
        # Total cycle time
        total_cycle_minutes = (
            bars_to_entry +
            entry_latency +
            hold_time +
            exit_latency +
            settlement_lag
        )
        
        # Calculate daily capacity (6.5 hour session = 390 minutes)
        # Reserve 30 min for market open/close volatility = 360 min usable
        max_daily_trades = 360 / total_cycle_minutes if total_cycle_minutes > 0 else 0
        
        # Score based on cycle speed (capital turnover efficiency)
        if total_cycle_minutes <= 10:
            # Excellent: 36+ trades possible
            score = 100.0
        elif total_cycle_minutes <= 12:
            # Very good: 30+ trades possible
            score = 100.0 - ((total_cycle_minutes - 10) / 2) * 10.0
        elif total_cycle_minutes <= 15:
            # Good: 24+ trades possible
            score = 90.0 - ((total_cycle_minutes - 12) / 3) * 15.0
        elif total_cycle_minutes <= 20:
            # Acceptable: 18+ trades possible
            score = 75.0 - ((total_cycle_minutes - 15) / 5) * 25.0
        elif total_cycle_minutes <= 30:
            # Marginal: 12+ trades possible
            score = 50.0 - ((total_cycle_minutes - 20) / 10) * 30.0
        else:
            # Poor: < 12 trades possible (capital turnover too slow)
            score = max(0.0, 20.0 - ((total_cycle_minutes - 30) * 1.0))
        
        return min(100.0, max(0.0, score))
    
    # ========================================================================
    # TIER 5: SYSTEM CONFIDENCE (3%)
    # ========================================================================
    
    def score_historical_reliability(self, stock_data: Dict) -> float:
        """
        Historical Reliability (2% weight)
        
        Track record stability - has this stock been reliable over time?
        
        Inputs:
        - performance_consistency: Variance in daily results
        - forecast_accuracy_20d: How close actual matched forecast
        
        Target: Consistency score > 85%
        Scale: 0-100 (higher = better)
        """
        consistency = stock_data.get('performance_consistency', 50.0)
        
        if consistency >= 90:
            score = 100.0
        elif consistency >= 85:
            score = 80.0 + ((consistency - 85) / 5) * 20.0
        elif consistency >= 70:
            score = 50.0 + ((consistency - 70) / 15) * 30.0
        else:
            score = (consistency / 70) * 50.0
        
        return min(100.0, max(0.0, score))
    
    def score_data_quality(self, stock_data: Dict) -> float:
        """
        Data Quality Score (1% weight)
        
        Clean data, no gaps - bad data = bad decisions.
        
        Inputs:
        - missing_bars: % of missing 1-minute bars
        - anomaly_count: Number of data anomalies detected
        - api_latency: Data feed reliability
        
        Target: < 1% missing bars
        Scale: 0-100 (higher = better)
        """
        missing_pct = stock_data.get('missing_bars', 0.0)
        
        if missing_pct <= 0.5:
            score = 100.0
        elif missing_pct <= 1.0:
            score = 100.0 - ((missing_pct - 0.5) / 0.5) * 20.0
        elif missing_pct <= 2.0:
            score = 80.0 - ((missing_pct - 1.0) / 1.0) * 40.0
        else:
            score = max(0.0, 40.0 - ((missing_pct - 2.0) * 10.0))
        
        return min(100.0, max(0.0, score))
    
    # ========================================================================
    # COMPOSITE SCORING
    # ========================================================================
    
    def calculate_composite_score(
        self,
        stock_data: Dict,
        selected_stocks: List[Dict] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate composite score using all 16 categories.
        
        Args:
            stock_data: Dictionary with all stock metrics
            selected_stocks: List of already-selected stocks (for correlation/sector)
        
        Returns:
            Tuple of (composite_score, category_scores_dict)
        """
        # Calculate all category scores
        scores = {
            'expected_value': self.score_expected_value(stock_data),
            'pattern_frequency': self.score_pattern_frequency(stock_data),
            'dead_zone': self.score_dead_zone(stock_data),
            'liquidity': self.score_liquidity(stock_data),
            'volatility': self.score_volatility(stock_data),
            'vwap_stability': self.score_vwap_stability(stock_data),
            'time_efficiency': self.score_time_efficiency(stock_data),
            'slippage': self.score_slippage(stock_data),
            'false_positive_rate': self.score_false_positive_rate(stock_data),
            'drawdown': self.score_drawdown(stock_data),
            'news_risk': self.score_news_risk(stock_data),
            'correlation': self.score_correlation(stock_data, [s.get('ticker') for s in selected_stocks] if selected_stocks else None),
            'halt_risk': self.score_halt_risk(stock_data),
            'execution_cycle': self.score_execution_cycle(stock_data, selected_stocks),
            'historical_reliability': self.score_historical_reliability(stock_data),
            'data_quality': self.score_data_quality(stock_data)
        }
        
        # Calculate weighted composite
        composite = sum(scores[cat] * weight for cat, weight in self.WEIGHTS.items())
        
        return composite, scores
    
    def rank_stocks(
        self,
        stock_data_list: List[Dict],
        top_n: int = 24
    ) -> List[Dict]:
        """
        Rank stocks by composite score and return top N.
        
        Args:
            stock_data_list: List of stock data dictionaries
            top_n: Number of top stocks to return (default 24)
        
        Returns:
            List of stocks with composite scores, sorted by rank
        """
        ranked = []
        
        for stock_data in stock_data_list:
            composite, category_scores = self.calculate_composite_score(
                stock_data,
                selected_stocks=ranked  # Pass already-selected for correlation/sector
            )
            
            ranked.append({
                **stock_data,
                'composite_score': composite,
                'category_scores': category_scores,
                'rank': 0  # Will be set after sorting
            })
        
        # Sort by composite score (descending)
        ranked.sort(key=lambda x: x['composite_score'], reverse=True)
        
        # Assign ranks
        for i, stock in enumerate(ranked[:top_n], start=1):
            stock['rank'] = i
        
        return ranked[:top_n]


def get_category_weights() -> Dict[str, float]:
    """
    Get the 16-category weight structure.
    
    Returns:
        Dictionary of category names -> weights
    """
    return CategoryScorer.WEIGHTS


def get_category_descriptions() -> Dict[str, str]:
    """
    Get descriptions for all 16 categories.
    
    Returns:
        Dictionary of category names -> descriptions
    """
    return {
        'expected_value': 'Win rate × avg win - loss rate × avg loss',
        'pattern_frequency': 'Tradeable opportunities per day (2-4 ideal)',
        'dead_zone': 'Capital efficiency & opportunity cost from idle periods',
        'liquidity': 'Volume depth & spread tightness (>5M vol, <5 bps)',
        'volatility': 'ATR-based threshold matching (1.5%-3.5% sweet spot)',
        'vwap_stability': 'Pattern cleanliness (<1.5% deviation)',
        'time_efficiency': 'Fast execution & resolution (<15 min hold)',
        'slippage': 'Actual vs expected execution (<3 bps)',
        'false_positive_rate': 'Pattern reliability (<30% FPR)',
        'drawdown': 'Downside protection (<2% max DD)',
        'news_risk': 'Earnings/events exposure (>3 days safe)',
        'correlation': 'Diversification benefit (<0.7 correlation)',
        'halt_risk': 'Trading suspension risk (zero halts)',
        'execution_cycle': 'Full trade cycle feasibility (<12 min ideal)',
        'historical_reliability': 'Track record stability (>85% consistency)',
        'data_quality': 'Clean data, no gaps (<1% missing)'
    }
