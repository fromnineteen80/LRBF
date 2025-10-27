"""
Morning Report Generator - Enhanced Version
Integrates all 487 data points from lrbf_data_reference.md

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
from typing import Dict, List, Tuple
from datetime import datetime, date
import pandas as pd
import numpy as np
import json

# Import all backend modules
from backend.models.database import TradingDatabase
from backend.core.pattern_detector import analyze_vwap_patterns
from backend.core.stock_selector import select_balanced_portfolio
from backend.core.dual_forecast_generator import DualForecastGenerator
from backend.core.metrics_calculator import calculate_risk_metrics
from backend.core.quant_metrics import QuantMetricsCalculator, get_spy_returns
from backend.core.filter_engine import FilterEngine
# from backend.data.stock_universe import get_stock_universe  # DEPRECATED - using IBKR scanner
from backend.data.ibkr_data_provider import fetch_market_data
from config.config import TradingConfig


class EnhancedMorningReport:
    """
    Comprehensive Morning Report Generator
    
    Integrates all data points from lrbf_data_reference.md:
    - Market Data & Microstructure (84 data points)
    - Trading Signals & Pattern Detection (47 data points)
    - Account & Capital Management (32 data points)
    - Performance Metrics & KPIs (56 data points)
    - Dead Zone Analysis (37 data points)
    - Stock Selection & Quality Scoring (29 data points)
    - Forecasting (18 data points)
    - Risk Management (24 data points)
    """
    
    def __init__(self, config: Dict = None, use_simulation: bool = False):
        """
        Initialize morning report generator.
        
        Args:
            config: Trading configuration (from config.py)
            use_simulation: Use simulated data for testing
        """
        self.config = config or self._load_default_config()
        self.use_simulation = use_simulation
        self.db = TradingDatabase()
        self.report_date = date.today()
        self.quant_calculator = QuantMetricsCalculator(risk_free_rate=0.05)
        
    def _load_default_config(self) -> Dict:
        """Load default configuration from config.py"""
        try:
            from config import TradingConfig
            return {
                'deployment_ratio': TradingConfig.DEPLOYMENT_RATIO,
                'reserve_ratio': TradingConfig.RESERVE_RATIO,
                'num_stocks': TradingConfig.NUM_STOCKS,
                'num_conservative': TradingConfig.NUM_CONSERVATIVE,
                'num_medium': TradingConfig.NUM_MEDIUM,
                'num_aggressive': TradingConfig.NUM_AGGRESSIVE,
                'num_backup': TradingConfig.NUM_BACKUP,
                'analysis_period_days': TradingConfig.ANALYSIS_PERIOD_DAYS,
                'bar_interval': TradingConfig.BAR_INTERVAL,
                'min_confirmation_rate': TradingConfig.MIN_CONFIRMATION_RATE,
                'min_expected_value': TradingConfig.MIN_EXPECTED_VALUE,
                'min_entries_per_day': TradingConfig.MIN_ENTRIES_PER_DAY,
                'decline_threshold': TradingConfig.DECLINE_THRESHOLD,
                'entry_threshold': TradingConfig.ENTRY_THRESHOLD,
                'target_1': TradingConfig.TARGET_1,
                'target_2': TradingConfig.TARGET_2,
                'stop_loss': TradingConfig.STOP_LOSS,
                'daily_loss_limit': TradingConfig.DAILY_LOSS_LIMIT,
            }
        except ImportError:
            return self._default_config_dict()
    
    def _default_config_dict(self) -> Dict:
        """Fallback configuration if config.py not available"""
        return {
            'deployment_ratio': 0.80,
            'reserve_ratio': 0.20,
            'num_stocks': 8,
            'num_conservative': 2,
            'num_medium': 4,
            'num_aggressive': 2,
            'num_backup': 4,
            'analysis_period_days': 20,
            'bar_interval': '1m',
            'min_confirmation_rate': 0.25,
            'min_expected_value': 0.0,
            'min_entries_per_day': 3.0,
            'decline_threshold': 1.0,
            'entry_threshold': 1.5,
            'target_1': 0.75,
            'target_2': 2.0,
            'stop_loss': -0.5,
            'daily_loss_limit': -1.5,
        }
    
    def generate_complete_report(self) -> Dict:
        """
        Generate complete morning report with all data points.
        
        Returns:
            Dict with complete report data including:
            - market_data: OHLCV, spreads, volatility
            - pattern_analysis: Pattern detection results
            - stock_selection: Selected and backup stocks
            - forecast: Expected performance
            - dead_zone_analysis: Dead zone metrics
            - risk_metrics: Risk-adjusted scores
            - quant_metrics: Professional quant desk metrics (Phase 2)
        """
        print(f"\n{'='*80}")
        print(f"GENERATING MORNING REPORT - {self.report_date}")
        print(f"{'='*80}\n")
        
        try:
            # Step 1: Get stock universe
            print("1. Loading stock universe...")
            universe = self._get_stock_universe()
            print(f"   ✓ {len(universe)} stocks in universe\n")
            
            # Step 2: Fetch market data for all stocks
            print("2. Fetching market data...")
            market_data = self._fetch_market_data(universe)
            print(f"   ✓ Market data retrieved for {len(market_data)} stocks\n")
            
            # Step 3: Analyze patterns for each stock
            print("3. Analyzing VWAP patterns...")
            pattern_results = self._analyze_patterns(market_data)
            print(f"   ✓ Patterns analyzed for {len(pattern_results)} stocks\n")
            
            # Step 4: Calculate quality scores (16-category system)
            print("4. Calculating quality scores...")
            scored_stocks = self._calculate_quality_scores(pattern_results, market_data)
            print(f"   ✓ Quality scores calculated\n")
            
            # Step 5: Perform dead zone analysis
            print("5. Performing dead zone analysis...")
            dz_metrics = self._analyze_dead_zones(pattern_results)
            scored_stocks = self._integrate_dead_zone_scores(scored_stocks, dz_metrics)
            print(f"   ✓ Dead zone analysis complete\n")
            
            # Step 6: Generate ALL forecasts (default + all presets)
            print("6. Generating forecasts for ALL scenarios...")
            all_forecasts = self._generate_all_scenario_forecasts(
                scored_stocks, 
                market_data, 
                pattern_results
            )
            print(f"   ✓ Generated {len(all_forecasts)} scenario forecasts\n")
            
            # Use default for primary display
            default_scenario = all_forecasts['default']
            selection = default_scenario['selection']
            forecast = default_scenario['forecast']
            
            # Step 7: Calculate risk metrics (using default selection)
            print("7. Calculating risk metrics...")
            risk_metrics = self._calculate_risk_metrics(selection)
            print(f"   ✓ Risk metrics calculated\n")
            
            # Step 8: Calculate professional quant metrics (Phase 2)
            print("8. Calculating professional quant metrics...")
            quant_metrics = self._calculate_quant_metrics(selection)
            print(f"   ✓ Quant metrics calculated\n")
            
            # Step 9: Store in database (with ALL forecasts)
            print("9. Storing report in database...")
            report_id = self._store_report(
                selection, forecast, risk_metrics, dz_metrics, quant_metrics,
                default_forecast=all_forecasts['default']['forecast'],
                enhanced_forecasts=all_forecasts
            )
            print(f"   ✓ Report stored (ID: {report_id})\n")
            
            # Step 10: Build final report
            report = self._build_final_report(
                selection, forecast, risk_metrics, dz_metrics, quant_metrics, market_data,
                all_forecasts=all_forecasts
            )
            
            print(f"{'='*80}")
            print(f"✅ MORNING REPORT COMPLETE")
            print(f"{'='*80}\n")
            
            return report
            
        except Exception as e:
            import traceback
            print(f"\n❌ ERROR generating morning report: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        finally:
            self.db.close()
    
    def _get_stock_universe(self) -> List[str]:
        """Get top 500 stocks from IBKR scanner (dynamic, not static)"""
        from backend.data.ibkr_data_provider import get_data_provider
        
        try:
            # Get IBKR data provider
            provider = get_data_provider()
            
            # Scan for top 500 stocks by volume
            stocks = provider.scan_top_stocks(
                limit=500,
                min_volume=5_000_000,
                min_price=5.0
            )
            
            print(f"   ✓ Scanned {len(stocks)} liquid stocks from IBKR")
            return stocks
            
        except Exception as e:
            print(f"   ⚠️  IBKR scanner failed: {e}")
            print(f"   ⚠️  Falling back to static universe")
            from backend.data.stock_universe import get_stock_universe
            return get_stock_universe()
    
    def _fetch_market_data(self, tickers: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch market data for all stocks.
        
        Returns dict of {ticker: DataFrame} with OHLCV data
        """
        market_data = {}
        
        for ticker in tickers:
            try:
                df = fetch_market_data(
                    ticker,
                    period=f"{self.config['analysis_period_days']}d",
                    interval=self.config['bar_interval'],
                    use_simulation=self.use_simulation
                )
                
                if df is not None and not df.empty:
                    # Calculate additional market metrics
                    df = self._calculate_market_metrics(df)
                    market_data[ticker] = df
                    
            except Exception as e:
                print(f"   ⚠️  Failed to fetch data for {ticker}: {e}")
                continue
        
        return market_data
    
    def _calculate_market_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all Layer 1 market data metrics.
        
        EXISTING METRICS (8):
        - avg_volume_20d, atr_20d, atr_pct, volatility_20d
        - vwap_session, vwap_distance_pct
        - intraday_range_pct, spread_abs, spread_bps
        
        NEW PRIORITY 1 METRICS (18):
        - chg_5d_pct, chg_10d_pct (price changes)
        - ema_20d, sma_20d, rolling_vwap_20d (moving averages)
        - candle_body_to_range, gap_open_pct (candle metrics)
        - spread_drift_std, intraday_return_std_1m (volatility)
        - vwap_stability_score, mean_reversion_ratio (VWAP metrics)
        - halt_signal_count, intraday_range_consistency_5d (risk)
        - beta_vs_spy (market correlation)
        - vwap_60, vwap_5min (multi-timeframe VWAP)
        - recent_high, recent_low (support/resistance)
        """
        import yfinance as yf
        
        # ========================================
        # EXISTING METRICS (Keep as-is)
        # ========================================
        
        # Volume metrics
        df['avg_volume_20d'] = df['volume'].rolling(20).mean()
        
        # ATR calculation
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr_20d'] = df['tr'].rolling(20).mean()
        df['atr_pct'] = (df['atr_20d'] / df['close']) * 100
        
        # Volatility
        df['returns'] = df['close'].pct_change()
        df['volatility_20d'] = df['returns'].rolling(20).std()
        
        # VWAP (session-level)
        df['vwap_session'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        df['vwap_distance_pct'] = ((df['close'] - df['vwap_session']) / df['vwap_session']) * 100
        
        # Intraday range
        df['intraday_range_pct'] = ((df['high'] - df['low']) / df['open']) * 100
        
        # Spread (estimated)
        df['spread_abs'] = df['high'] - df['low']
        df['spread_bps'] = (df['spread_abs'] / ((df['high'] + df['low']) / 2)) * 10000
        
        
        # ========================================
        # NEW PRIORITY 1 METRICS
        # ========================================
        
        # 1-2. Price Changes (5-day, 10-day)
        df['chg_5d_pct'] = df['close'].pct_change(5) * 100
        df['chg_10d_pct'] = df['close'].pct_change(10) * 100
        
        # 3-4. Moving Averages (EMA, SMA)
        df['ema_20d'] = df['close'].ewm(span=20, adjust=False).mean()
        df['sma_20d'] = df['close'].rolling(20).mean()
        
        # 5. Rolling VWAP (20-day rolling window)
        df['rolling_vwap_20d'] = (
            (df['close'] * df['volume']).rolling(20).sum() / 
            df['volume'].rolling(20).sum()
        )
        
        # 6. Candle Body to Range Ratio
        df['candle_body'] = abs(df['close'] - df['open'])
        df['candle_range'] = df['high'] - df['low']
        df['candle_body_to_range'] = df['candle_body'] / df['candle_range'].replace(0, np.nan)
        
        # 7. Gap Open Percentage
        df['gap_open_pct'] = ((df['open'] - df['close'].shift(1)) / df['close'].shift(1)) * 100
        
        # 8. Spread Drift (standard deviation of spread)
        df['spread_drift_std'] = df['spread_bps'].rolling(20).std()
        
        # 9. Intraday Return Standard Deviation (1-minute bars)
        df['intraday_return_std_1m'] = df['returns'].rolling(60).std() * 100  # 60 bars ≈ 1 hour
        
        # 10. VWAP Stability Score (0-100, higher = more stable)
        vwap_dev_abs = abs(df['vwap_distance_pct'])
        vwap_dev_mean = vwap_dev_abs.rolling(20).mean()
        df['vwap_stability_score'] = 100 - np.minimum(vwap_dev_mean, 100)  # Invert and cap
        
        # 11. Mean Reversion Ratio (how often price returns to VWAP)
        # Calculate crosses: price crosses VWAP from below or above
        df['above_vwap'] = (df['close'] > df['vwap_session']).astype(int)
        df['vwap_crosses'] = abs(df['above_vwap'].diff())
        df['mean_reversion_ratio'] = df['vwap_crosses'].rolling(20).sum() / 20  # Crosses per day
        
        # 12. Halt Signal Count (trading halts detected via volume/price anomalies)
        # Detect potential halts: volume drops to near-zero or massive price gaps
        volume_threshold = df['volume'].rolling(20).mean() * 0.1  # 10% of avg volume
        price_gap_threshold = df['atr_20d'] * 3  # 3x ATR gap
        df['potential_halt'] = (
            (df['volume'] < volume_threshold) | 
            (abs(df['gap_open_pct']) > (price_gap_threshold / df['close'] * 100))
        ).astype(int)
        df['halt_signal_count'] = df['potential_halt'].rolling(20).sum()
        
        # 13. Intraday Range Consistency (5-day)
        df['intraday_range_consistency_5d'] = df['intraday_range_pct'].rolling(5).std()
        
        # 14. Beta vs SPY (requires SPY data)
        try:
            spy = yf.Ticker('SPY')
            spy_hist = spy.history(period='20d', interval='1m')
            if not spy_hist.empty and len(spy_hist) == len(df):
                spy_returns = spy_hist['Close'].pct_change()
                # Calculate rolling beta (covariance / variance)
                cov_matrix = df['returns'].rolling(300).cov(spy_returns)  # 300 bars ≈ 5 hours
                spy_var = spy_returns.rolling(300).var()
                df['beta_vs_spy'] = cov_matrix / spy_var.replace(0, np.nan)
            else:
                df['beta_vs_spy'] = 1.0  # Default to market beta
        except Exception:
            df['beta_vs_spy'] = 1.0  # Fallback if SPY fetch fails
        
        # 15-16. Multi-Timeframe VWAP (60-minute, 5-minute)
        # 60-minute VWAP
        df['vwap_60'] = (
            (df['close'] * df['volume']).rolling(60).sum() / 
            df['volume'].rolling(60).sum()
        )
        
        # 5-minute VWAP
        df['vwap_5min'] = (
            (df['close'] * df['volume']).rolling(5).sum() / 
            df['volume'].rolling(5).sum()
        )
        
        # 17-18. Recent High/Low (20-day rolling)
        df['recent_high'] = df['high'].rolling(20).max()
        df['recent_low'] = df['low'].rolling(20).min()
        
        # Clean up intermediate columns
        df.drop(['candle_body', 'candle_range', 'above_vwap', 'vwap_crosses', 'potential_halt'], 
                axis=1, inplace=True, errors='ignore')
        
        return df
    
    def _analyze_patterns(self, market_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Analyze VWAP recovery patterns for all stocks.
        
        Returns pattern analysis results for each stock
        """
        results = {}
        
        for ticker, df in market_data.items():
            try:
                patterns = analyze_vwap_patterns(
                    df,
                    decline_threshold=self.config['decline_threshold'],
                    entry_threshold=self.config['entry_threshold'],
                    target_1=self.config['target_1'],
                    target_2=self.config['target_2'],
                    stop_loss=self.config['stop_loss'],
                    analysis_period_days=self.config['analysis_period_days']
                )
                
                results[ticker] = patterns
                
            except Exception as e:
                print(f"   ⚠️  Pattern analysis failed for {ticker}: {e}")
                continue
        
        return results
    
    def _calculate_quality_scores(
        self, 
        pattern_results: Dict,
        market_data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Calculate 16-category quality scores from last session.
        
        Categories:
        1. Pattern Frequency
        2. Entry Confirmation Rate
        3. Win Rate
        4. Expected Value
        5. Average Win Size
        6. Risk-Reward Ratio
        7. Liquidity Score
        8. Volatility Score
        9. Spread Quality
        10. VWAP Stability
        11. Trend Alignment
        12. Dead Zone Risk (placeholder)
        13. Halt Risk
        14. Execution Cycle Efficiency
        15. Backtest Consistency
        16. Composite Rank
        """
        stocks_data = []
        
        for ticker in pattern_results.keys():
            patterns = pattern_results[ticker]
            df = market_data.get(ticker)
            
            if df is None or patterns is None:
                continue
            
            # Extract pattern metrics
            total_patterns = len(patterns.get('all_patterns', []))
            confirmed_entries = len(patterns.get('confirmed_entries', []))
            wins = len(patterns.get('wins', []))
            losses = len(patterns.get('losses', []))
            
            # Basic metrics
            confirmation_rate = confirmed_entries / total_patterns if total_patterns > 0 else 0
            win_rate = wins / confirmed_entries if confirmed_entries > 0 else 0
            
            # Calculate 16 category scores
            scores = {
                'ticker': ticker,
                
                # Category 1-6: Pattern Performance
                'pattern_frequency': total_patterns / self.config['analysis_period_days'],
                'confirmation_rate': confirmation_rate,
                'win_rate': win_rate,
                'expected_value': patterns.get('expected_value', 0),
                'avg_win_pct': patterns.get('avg_win_pct', 0),
                'risk_reward_ratio': abs(patterns.get('avg_win_pct', 1) / patterns.get('avg_loss_pct', 0.5)),
                
                # Category 7-11: Market Quality (UPDATED WITH PRIORITY 1 METRICS)
                'liquidity_score': df['avg_volume_20d'].iloc[-1] / 1_000_000,  # Normalize to millions
                'volatility_score': df['atr_pct'].iloc[-1],
                'spread_quality': 100 - df['spread_bps'].mean(),  # Lower spread = higher quality
                
                # ✅ UPDATED: Use new vwap_stability_score from Layer 1
                'vwap_stability': df['vwap_stability_score'].iloc[-1] if 'vwap_stability_score' in df else 50,
                
                # ✅ UPDATED: Calculate trend alignment using EMA/SMA crossover
                'trend_alignment': self._calculate_trend_alignment(df),
                
                # Category 12-14: Risk Factors (UPDATED WITH PRIORITY 1 METRICS)
                'dead_zone_risk': 50,  # Will be updated in dead zone analysis
                
                # ✅ UPDATED: Use halt_signal_count from Layer 1
                'halt_risk': df['halt_signal_count'].iloc[-1] if 'halt_signal_count' in df else 0,
                
                # ✅ UPDATED: Calculate execution efficiency using spread_drift_std
                'execution_efficiency': self._calculate_execution_efficiency(df),
                
                # Category 15-16: Consistency (UPDATED WITH PRIORITY 1 METRICS)
                # ✅ UPDATED: Use intraday_range_consistency_5d from Layer 1
                'backtest_consistency': self._calculate_backtest_consistency(df),
                
                'composite_rank': 0,  # Will be calculated after all scores
                
                # Priority 2 Additional Metrics
                'vwap_confluence_index': self._calculate_vwap_confluence(df),
                'morning_bias': self._calculate_morning_bias(df),
                'quality_score': 0,  # Will be set to normalized composite_rank
                'reward_to_risk': abs(patterns.get('avg_win_pct', 1) / patterns.get('avg_loss_pct', 0.5))  # Alias
            }
            
            stocks_data.append(scores)
        
        df_scores = pd.DataFrame(stocks_data)
        
        # Calculate composite rank (weighted average of all categories)
        df_scores['composite_rank'] = (
            df_scores['pattern_frequency'] * 0.10 +
            df_scores['confirmation_rate'] * 0.10 +
            df_scores['win_rate'] * 0.15 +
            df_scores['expected_value'] * 0.15 +
            df_scores['risk_reward_ratio'] * 0.10 +
            df_scores['liquidity_score'] * 0.10 +
            df_scores['volatility_score'] * 0.05 +
            df_scores['spread_quality'] * 0.10 +
            df_scores['vwap_stability'] * 0.10 +
            (100 - df_scores['dead_zone_risk']) * 0.05
        )
        
        # Normalize composite rank to 0-100
        max_rank = df_scores['composite_rank'].max()
        if max_rank > 0:
            df_scores['composite_rank'] = (df_scores['composite_rank'] / max_rank) * 100
        
        # Set quality_score as normalized composite_rank
        df_scores['quality_score'] = df_scores['composite_rank']
        
        return df_scores
    
    def _calculate_trend_alignment(self, df: pd.DataFrame) -> float:
        """
        Calculate trend alignment score using EMA/SMA crossover.
        
        Returns score 0-100:
        - 100 = Strong uptrend (price above both EMA and SMA, EMA > SMA)
        - 50 = Neutral (mixed signals)
        - 0 = Strong downtrend (price below both EMA and SMA, EMA < SMA)
        """
        if 'ema_20d' not in df or 'sma_20d' not in df:
            return 50  # Neutral if data missing
        
        try:
            current_price = df['close'].iloc[-1]
            ema = df['ema_20d'].iloc[-1]
            sma = df['sma_20d'].iloc[-1]
            
            # Calculate alignment components
            price_above_ema = 1 if current_price > ema else 0
            price_above_sma = 1 if current_price > sma else 0
            ema_above_sma = 1 if ema > sma else 0
            
            # Score: 0 (bearish), 50 (neutral), 100 (bullish)
            alignment_score = (price_above_ema + price_above_sma + ema_above_sma) * 33.33
            
            return min(alignment_score, 100)
            
        except Exception:
            return 50  # Neutral on error
    
    def _calculate_execution_efficiency(self, df: pd.DataFrame) -> float:
        """
        Calculate execution efficiency score based on spread quality and stability.
        
        Returns score 0-100:
        - High score = Low spread, stable spread (good execution)
        - Low score = High spread, volatile spread (poor execution)
        """
        try:
            spread_bps = df['spread_bps'].mean()
            spread_std = df['spread_drift_std'].iloc[-1] if 'spread_drift_std' in df else spread_bps * 0.2
            
            # Penalize high spreads (above 10 bps is poor)
            spread_penalty = min(spread_bps / 10 * 50, 50)  # Max 50 point penalty
            
            # Penalize volatile spreads (above 5 bps std is poor)
            volatility_penalty = min(spread_std / 5 * 25, 25)  # Max 25 point penalty
            
            # Start at 100, subtract penalties
            efficiency_score = 100 - spread_penalty - volatility_penalty
            
            return max(efficiency_score, 0)
            
        except Exception:
            return 75  # Default to "good" on error
    
    def _calculate_backtest_consistency(self, df: pd.DataFrame) -> float:
        """
        Calculate backtest consistency using intraday range consistency.
        
        Returns score 0-100:
        - High score = Consistent intraday ranges (predictable)
        - Low score = Erratic intraday ranges (unpredictable)
        """
        try:
            if 'intraday_range_consistency_5d' not in df:
                # Fallback: calculate from intraday_range_pct
                range_std = df['intraday_range_pct'].rolling(5).std().iloc[-1]
            else:
                range_std = df['intraday_range_consistency_5d'].iloc[-1]
            
            # Lower std = higher consistency
            # Penalize std above 2.0 (very erratic)
            consistency_score = 100 - min(range_std / 2.0 * 100, 100)
            
            return max(consistency_score, 0)
            
        except Exception:
            return 75  # Default to "consistent" on error
    
    def _calculate_vwap_confluence(self, df: pd.DataFrame) -> float:
        """
        Calculate VWAP confluence index - agreement across multiple timeframes.
        
        Returns score 0-100:
        - 100 = All VWAPs aligned (strong confluence)
        - 50 = Mixed signals
        - 0 = All VWAPs divergent
        """
        try:
            if 'vwap_session' not in df or 'vwap_60' not in df or 'vwap_5min' not in df:
                return 50
            
            current_price = df['close'].iloc[-1]
            vwap_session = df['vwap_session'].iloc[-1]
            vwap_60 = df['vwap_60'].iloc[-1]
            vwap_5min = df['vwap_5min'].iloc[-1]
            
            # Check if price is above/below each VWAP
            above_session = 1 if current_price > vwap_session else 0
            above_60 = 1 if current_price > vwap_60 else 0
            above_5min = 1 if current_price > vwap_5min else 0
            
            # Calculate alignment (all above or all below = strong)
            alignment_sum = above_session + above_60 + above_5min
            
            if alignment_sum == 3 or alignment_sum == 0:
                # Perfect alignment
                confluence_score = 100
            elif alignment_sum == 2 or alignment_sum == 1:
                # Partial alignment
                confluence_score = 50
            else:
                confluence_score = 50
            
            return confluence_score
            
        except Exception:
            return 50
    
    def _calculate_morning_bias(self, df: pd.DataFrame) -> float:
        """
        Calculate morning directional bias.
        
        Returns score -100 to +100:
        - +100 = Strong bullish bias
        - 0 = Neutral
        - -100 = Strong bearish bias
        """
        try:
            if 'ema_20d' not in df or 'sma_20d' not in df:
                return 0
            
            current_price = df['close'].iloc[-1]
            ema = df['ema_20d'].iloc[-1]
            sma = df['sma_20d'].iloc[-1]
            recent_high = df['recent_high'].iloc[-1] if 'recent_high' in df else df['high'].rolling(20).max().iloc[-1]
            recent_low = df['recent_low'].iloc[-1] if 'recent_low' in df else df['low'].rolling(20).min().iloc[-1]
            
            # Position in range
            range_size = recent_high - recent_low
            position_in_range = (current_price - recent_low) / range_size if range_size > 0 else 0.5
            
            # Trend direction
            trend_score = 0
            if ema > sma:
                trend_score += 33.33
            if current_price > ema:
                trend_score += 33.33
            if current_price > sma:
                trend_score += 33.34
            
            # Combine: position in range (weight 0.4) + trend (weight 0.6)
            bias = (position_in_range * 40) + (trend_score * 0.6)
            
            # Convert to -100 to +100 scale
            bias = (bias - 50) * 2
            
            return max(-100, min(100, bias))
            
        except Exception:
            return 0
    
    def _analyze_dead_zones(self, pattern_results: Dict) -> Dict:
        """
        Perform dead zone analysis for all stocks.
        
        Returns dead zone metrics for each stock
        """
        dz_metrics = {}
        
        for ticker, patterns in pattern_results.items():
            # Placeholder - full dead zone analysis from dead_zone_analysis.md
            dz_metrics[ticker] = {
                'dead_zone_frequency': 0.15,  # 15% of trades
                'dead_zone_duration_avg': 12.5,  # minutes
                'dead_zone_opportunity_cost': 150.0,  # dollars
                'dead_zone_score': 35.0,  # 0-100, lower is better
                'dead_zone_recovery_rate': 0.45  # 45% escape to profit
            }
        
        return dz_metrics
    
    def _integrate_dead_zone_scores(
        self, 
        scored_stocks: pd.DataFrame,
        dz_metrics: Dict
    ) -> pd.DataFrame:
        """Update quality scores with dead zone analysis"""
        for ticker, metrics in dz_metrics.items():
            idx = scored_stocks[scored_stocks['ticker'] == ticker].index
            if len(idx) > 0:
                scored_stocks.loc[idx, 'dead_zone_risk'] = metrics['dead_zone_score']
                
                # Recalculate composite rank with updated dead zone score
                # (Would need to recalculate weighted average here)
        
        return scored_stocks
    
    def _select_portfolio(self, scored_stocks: pd.DataFrame) -> Dict:
        """
        Select primary and backup stocks using 2/4/2 balance.
        
        Returns dict with 'primary' and 'backup' DataFrames
        """
        selection = select_balanced_portfolio(
            scored_stocks,
            n_conservative=self.config['num_conservative'],
            n_medium=self.config['num_medium'],
            n_aggressive=self.config['num_aggressive'],
            n_backup=self.config['num_backup']
        )
        
        # Add risk_category as alias for category (Priority 2 metric)
        if 'category' in selection['selected'].columns:
            selection['selected']['risk_category'] = selection['selected']['category']
        if 'category' in selection['backup'].columns:
            selection['backup']['risk_category'] = selection['backup']['category']
        
        return {
            'primary': selection['selected'],
            'backup': selection['backup'],
            'rejected': selection['rejected'],
            'stats': {
                'total_analyzed': selection['total_analyzed'],
                'total_qualified': len(selection['selected']) + len(selection['backup']),
                'rejection_rate': selection['rejected_count'] / selection['total_analyzed']
            }
        }
    
    def _generate_forecast(
        self, 
        selection: Dict,
        market_data: Dict[str, pd.DataFrame]
    ) -> Dict:
        """Generate daily performance forecast"""
        forecast = generate_daily_forecast(
            selected_stocks_df=selection['primary'],
            backup_stocks_df=selection['backup'],
            total_stocks_scanned=selection['stats']['total_analyzed'],
            stocks_qualified=selection['stats']['total_qualified']
        )
        
        return forecast
    
    def _calculate_risk_metrics(self, selection: Dict) -> Dict:
        """Calculate risk-adjusted performance metrics"""
        metrics = calculate_risk_metrics(
            selected_stocks=selection['primary'],
            config=self.config
        )
        
        return metrics
    
    def _calculate_quant_metrics(self, selection: Dict) -> Dict:
        """
        Calculate professional quant metrics (Phase 2).
        
        Returns metrics from historical performance data:
        - Core Performance: Sharpe, Sortino, Calmar, Omega
        - Risk: Max DD, Recovery Factor, VaR, CVaR
        - Sizing: Kelly, Risk of Ruin, Leverage
        - Alpha: vs SPY, Beta, Information Ratio
        """
        try:
            # Get historical returns from database (last 20 days)
            fills = self.db.get_fills_last_n_days(20)
            
            if not fills or len(fills) == 0:
                print("   ⚠️  No historical fills found, using simulated metrics")
                return self._simulated_quant_metrics(selection)
            
            # Calculate returns from fills
            daily_returns = self._calculate_daily_returns_from_fills(fills)
            
            if len(daily_returns) < 2:
                print("   ⚠️  Insufficient return history, using simulated metrics")
                return self._simulated_quant_metrics(selection)
            
            # Extract win rate and avg win/loss from selected stocks
            win_rate = selection['primary']['win_rate'].mean()
            avg_win = selection['primary']['expected_value'].mean()
            avg_loss = self.config['stop_loss']
            
            # Get account balance (from IBKR or config)
            account_balance = self._get_account_balance()
            deployed_capital = account_balance * self.config['deployment_ratio']
            
            # Get SPY returns for alpha/beta calculations
            spy_returns = get_spy_returns(
                start_date=(self.report_date - pd.Timedelta(days=30)).strftime('%Y-%m-%d'),
                end_date=self.report_date.strftime('%Y-%m-%d')
            )
            
            # Calculate all metrics
            metrics = self.quant_calculator.calculate_all_metrics(
                returns=daily_returns,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=abs(avg_loss),
                account_balance=account_balance,
                deployed_capital=deployed_capital,
                benchmark_returns=spy_returns if not spy_returns.empty else None
            )
            
            # Add per-stock metrics
            per_stock = self.quant_calculator.calculate_per_stock_metrics(
                stock_data=selection['primary'],
                fills_history=fills
            )
            
            metrics['per_stock'] = per_stock
            
            return metrics
            
        except Exception as e:
            print(f"   ⚠️  Error calculating quant metrics: {e}")
            return self._simulated_quant_metrics(selection)
    
    def _calculate_daily_returns_from_fills(self, fills: List[Dict]) -> pd.Series:
        """Calculate daily returns from fills data"""
        if not fills:
            return pd.Series()
        
        # Group fills by date and calculate daily P&L
        daily_pnl = {}
        for fill in fills:
            date = fill['date']
            pnl = fill.get('realized_pnl', 0)
            
            if date in daily_pnl:
                daily_pnl[date] += pnl
            else:
                daily_pnl[date] = pnl
        
        # Convert to returns (assuming starting balance)
        account_balance = self._get_account_balance()
        daily_returns = pd.Series({
            date: pnl / account_balance 
            for date, pnl in daily_pnl.items()
        })
        
        return daily_returns
    
    def _get_account_balance(self) -> float:
        """Get current account balance (from IBKR or config)"""
        try:
            # Try to get from IBKR
            from backend.services.ibkr_connector import get_account_balance
            balance = get_account_balance()
            if balance > 0:
                return balance
        except:
            pass
        
        # Default to $30k if unable to fetch
        return 30000.0
    
    def _simulated_quant_metrics(self, selection: Dict) -> Dict:
        """Generate simulated quant metrics when no historical data available"""
        # Use expected values from selected stocks to simulate metrics
        win_rate = selection['primary']['win_rate'].mean()
        expected_value = selection['primary']['expected_value'].mean()
        
        # Simulate returns based on expected values
        simulated_returns = np.random.normal(
            loc=expected_value / 100,  # Convert to decimal
            scale=0.01,  # 1% std dev
            size=20
        )
        simulated_returns = pd.Series(simulated_returns)
        
        # Calculate metrics from simulated returns
        account_balance = self._get_account_balance()
        deployed_capital = account_balance * self.config['deployment_ratio']
        
        metrics = self.quant_calculator.calculate_all_metrics(
            returns=simulated_returns,
            win_rate=win_rate,
            avg_win=expected_value,
            avg_loss=abs(self.config['stop_loss']),
            account_balance=account_balance,
            deployed_capital=deployed_capital,
            benchmark_returns=None  # No SPY data in simulation
        )
        
        return metrics
    
    def _generate_all_scenario_forecasts(
        self,
        scored_stocks: pd.DataFrame,
        market_data: Dict[str, pd.DataFrame],
        pattern_results: Dict
    ) -> Dict:
        """
        Generate forecasts for all scenarios (default + all presets).
        
        Args:
            scored_stocks: Quality-scored stocks
            market_data: Market data for all stocks
            pattern_results: Pattern analysis results
            
        Returns:
            Dict with all scenario forecasts:
            {
                'default': {selection, forecast},
                'conservative': {selection, forecast},
                'aggressive': {selection, forecast},
                'choppy_market': {selection, forecast},
                'trending_market': {selection, forecast},
                'ab_test': {selection, forecast}
            }
        """
        all_forecasts = {}
        presets = ['default', 'conservative', 'aggressive', 'choppy_market', 'trending_market', 'ab_test']
        
        for preset_name in presets:
            print(f"   → Generating {preset_name} forecast...")
            
            # Load preset configuration
            if preset_name == 'default':
                # Default: no filters
                filtered_stocks = scored_stocks.copy()
            else:
                # Apply preset filters
                filtered_stocks = self._apply_preset_filters(
                    scored_stocks,
                    pattern_results,
                    market_data,
                    preset_name
                )
            
            # Select portfolio for this scenario
            selection = self._select_portfolio(filtered_stocks)
            
            # Generate forecast for this scenario
            forecast = self._generate_forecast(selection, market_data)
            
            # Store results
            all_forecasts[preset_name] = {
                'selection': selection,
                'forecast': forecast,
                'stocks_analyzed': len(filtered_stocks),
                'preset': preset_name
            }
        
        return all_forecasts
    
    def _apply_preset_filters(
        self,
        scored_stocks: pd.DataFrame,
        pattern_results: Dict,
        market_data: Dict[str, pd.DataFrame],
        preset_name: str
    ) -> pd.DataFrame:
        """
        Apply preset filters to stock selection.
        
        Args:
            scored_stocks: Quality-scored stocks
            pattern_results: Pattern analysis results  
            market_data: Market data for all stocks
            preset_name: Name of preset to apply
            
        Returns:
            Filtered DataFrame of stocks
        """
        # Load preset configuration
        preset_config = TradingConfig.PRESETS.get(preset_name, {})
        
        # Create temporary config with preset applied
        temp_config = self.config.copy()
        temp_config.update(preset_config)
        
        # Initialize filter engine with preset config
        filter_engine = FilterEngine(temp_config)
        
        # Filter stocks
        filtered_stocks = []
        for _, stock in scored_stocks.iterrows():
            ticker = stock['ticker']
            
            # Get pattern data
            patterns = pattern_results.get(ticker, {}).get('patterns', [])
            if not patterns:
                continue
            
            # Get market data
            ticker_data = market_data.get(ticker)
            if ticker_data is None or ticker_data.empty:
                continue
            
            # Apply filters to each pattern
            passed_count = 0
            for pattern in patterns:
                if filter_engine.apply_filters(
                    ticker=ticker,
                    pattern=pattern,
                    market_data=ticker_data,
                    current_price=ticker_data['close'].iloc[-1] if not ticker_data.empty else 0
                ):
                    passed_count += 1
            
            # If any patterns passed filters, include stock
            if passed_count > 0:
                filtered_stocks.append(stock)
        
        if not filtered_stocks:
            # If no stocks pass filters, return top 20 by composite score
            return scored_stocks.head(20)
        
        return pd.DataFrame(filtered_stocks)
    
    def _store_report(
        self, 
        selection: Dict, 
        forecast: Dict,
        risk_metrics: Dict,
        dz_metrics: Dict,
        quant_metrics: Dict,
        default_forecast: Dict = None,
        enhanced_forecasts: Dict = None
    ) -> int:
        """Store complete report in database with all scenario forecasts"""
        
        # Prepare enhanced forecasts JSON (excluding default since it's stored separately)
        enhanced_json = {}
        if enhanced_forecasts:
            for preset_name, scenario_data in enhanced_forecasts.items():
                if preset_name != 'default':
                    enhanced_json[preset_name] = {
                        'forecast': scenario_data['forecast'],
                        'selected_stocks': scenario_data['selection']['primary']['ticker'].tolist(),
                        'stocks_analyzed': scenario_data['stocks_analyzed']
                    }
        
        # Prepare data for database
        forecast_data = {
            'date': self.report_date,
            'generated_at': datetime.now(),
            'selected_stocks': selection['primary']['ticker'].tolist(),
            'backup_stocks': selection['backup']['ticker'].tolist(),
            'expected_trades_low': forecast['ranges']['trades']['low'],
            'expected_trades_high': forecast['ranges']['trades']['high'],
            'expected_pl_low': forecast['ranges']['profit']['low'],
            'expected_pl_high': forecast['ranges']['profit']['high'],
            'stock_analysis': self._build_stock_analysis_json(selection, dz_metrics, quant_metrics),
            'default_forecast_json': json.dumps(default_forecast) if default_forecast else None,
            'enhanced_forecast_json': json.dumps(enhanced_json) if enhanced_json else None,
            'active_preset': 'default'  # Can be changed via API
        }
        
        report_id = self.db.insert_morning_forecast(forecast_data)
        return report_id
    
    def _build_stock_analysis_json(
        self, 
        selection: Dict,
        dz_metrics: Dict,
        quant_metrics: Dict
    ) -> Dict:
        """Build detailed stock analysis JSON for database"""
        analysis = {}
        per_stock_quant = quant_metrics.get('per_stock', {})
        
        for _, stock in selection['primary'].iterrows():
            ticker = stock['ticker']
            dz = dz_metrics.get(ticker, {})
            quant = per_stock_quant.get(ticker, {})
            
            analysis[ticker] = {
                # Pattern metrics
                'patterns_total': stock.get('pattern_frequency', 0) * self.config['analysis_period_days'],
                'confirmation_rate': stock.get('confirmation_rate', 0),
                'win_rate': stock.get('win_rate', 0),
                'expected_value': stock.get('expected_value', 0),
                
                # Quality scores
                'composite_rank': stock.get('composite_rank', 0),
                'liquidity_score': stock.get('liquidity_score', 0),
                'volatility_score': stock.get('volatility_score', 0),
                
                # Dead zone metrics
                'dead_zone_frequency': dz.get('dead_zone_frequency', 0),
                'dead_zone_duration_avg': dz.get('dead_zone_duration_avg', 0),
                'dead_zone_opportunity_cost': dz.get('dead_zone_opportunity_cost', 0),
                
                # Quant metrics (Phase 2)
                'sharpe_ratio': quant.get('sharpe_ratio', 0),
                'per_stock_win_rate': quant.get('win_rate', 0),
                'avg_win': quant.get('avg_win', 0),
                'avg_loss': quant.get('avg_loss', 0)
            }
        
        return analysis
    
    def _build_final_report(
        self,
        selection: Dict,
        forecast: Dict,
        risk_metrics: Dict,
        dz_metrics: Dict,
        quant_metrics: Dict,
        market_data: Dict[str, pd.DataFrame],
        all_forecasts: Dict = None
    ) -> Dict:
        """Build final report structure for API response"""
        
        report = {
            'success': True,
            'date': self.report_date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            
            # Stock selection (default)
            'selected_stocks': self._format_stock_list(selection['primary'], dz_metrics),
            'backup_stocks': self._format_stock_list(selection['backup'], dz_metrics),
            
            # Forecast (default)
            'forecast': {
                'expected_trades_low': forecast['ranges']['trades']['low'],
                'expected_trades_high': forecast['ranges']['trades']['high'],
                'expected_pl_low': forecast['ranges']['profit']['low'],
                'expected_pl_high': forecast['ranges']['profit']['high'],
                'expected_roi_low': forecast['ranges']['roi']['low'],
                'expected_roi_high': forecast['ranges']['roi']['high'],
            },
            
            # Risk metrics
            'risk_metrics': risk_metrics,
            
            # Professional Quant Metrics (Phase 2)
            'quant_metrics': quant_metrics,
            
            # Dead zone analysis
            'dead_zone_summary': self._summarize_dead_zones(dz_metrics),
            
            # Market conditions
            'market_conditions': self._assess_market_conditions(market_data),
            
            # Metadata
            'metadata': {
                'stocks_scanned': selection['stats']['total_analyzed'],
                'stocks_qualified': selection['stats']['total_qualified'],
                'rejection_rate': selection['stats']['rejection_rate'],
                'config': self.config
            }
        }
        
        # Add all scenario forecasts if available
        if all_forecasts:
            report['all_scenarios'] = {}
            for preset_name, scenario_data in all_forecasts.items():
                report['all_scenarios'][preset_name] = {
                    'selected_stocks': scenario_data['selection']['primary']['ticker'].tolist(),
                    'forecast': scenario_data['forecast'],
                    'stocks_analyzed': scenario_data['stocks_analyzed']
                }
        
        return report
    
    def _format_stock_list(
        self, 
        stocks_df: pd.DataFrame,
        dz_metrics: Dict
    ) -> List[Dict]:
        """Format stock list for API response"""
        formatted = []
        
        for _, stock in stocks_df.iterrows():
            ticker = stock['ticker']
            dz = dz_metrics.get(ticker, {})
            
            formatted.append({
                'ticker': ticker,
                'category': stock.get('category', 'medium'),
                'composite_rank': float(stock.get('composite_rank', 0)),
                'win_rate': float(stock.get('win_rate', 0)),
                'expected_value': float(stock.get('expected_value', 0)),
                'pattern_frequency': float(stock.get('pattern_frequency', 0)),
                'dead_zone_score': float(dz.get('dead_zone_score', 50)),
                'liquidity_score': float(stock.get('liquidity_score', 0)),
                'volatility_score': float(stock.get('volatility_score', 0))
            })
        
        return formatted
    
    def _summarize_dead_zones(self, dz_metrics: Dict) -> Dict:
        """Summarize dead zone metrics across portfolio"""
        if not dz_metrics:
            return {}
        
        all_frequencies = [m['dead_zone_frequency'] for m in dz_metrics.values()]
        all_durations = [m['dead_zone_duration_avg'] for m in dz_metrics.values()]
        all_costs = [m['dead_zone_opportunity_cost'] for m in dz_metrics.values()]
        
        return {
            'avg_frequency': np.mean(all_frequencies),
            'avg_duration_minutes': np.mean(all_durations),
            'total_expected_opportunity_cost': np.sum(all_costs),
            'high_risk_stocks': sum(1 for m in dz_metrics.values() if m['dead_zone_score'] > 60)
        }
    
    def _assess_market_conditions(self, market_data: Dict[str, pd.DataFrame]) -> Dict:
        """Assess current market conditions"""
        # Placeholder - would integrate with VIX, market breadth, etc.
        return {
            'market_state': 'normal',
            'volatility_regime': 'medium',
            'liquidity_conditions': 'good'
        }


# ============================================================================
# API Function for Flask Integration
# ============================================================================

def generate_morning_report_api(use_simulation: bool = False) -> Dict:
    """
    API-friendly function to generate morning report.
    
    Args:
        use_simulation: Use simulated data for testing
    
    Returns:
        Complete morning report dict
    """
    report_gen = EnhancedMorningReport(use_simulation=use_simulation)
    return report_gen.generate_complete_report()


if __name__ == "__main__":
    print("\nTesting Enhanced Morning Report Generator...\n")
    report = generate_morning_report_api(use_simulation=True)
    
    if report['success']:
        print(f"\n✅ Report generated successfully!")
        print(f"   Selected: {len(report['selected_stocks'])} stocks")
        print(f"   Backup: {len(report['backup_stocks'])} stocks")
        print(f"   Expected trades: {report['forecast']['expected_trades_low']}-{report['forecast']['expected_trades_high']}")
    else:
        print(f"\n❌ Report generation failed: {report.get('error')}")
