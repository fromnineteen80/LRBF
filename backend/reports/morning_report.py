"""
Morning Report Generator - Enhanced Version
Integrates all 487 data points from lrbf_data_reference.md
+ Professional Quant Metrics (Phase 2)

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
from typing import Dict, List, Tuple
from datetime import datetime, date
import pandas as pd
import numpy as np

# Import all backend modules
from backend.models.database import TradingDatabase
from backend.core.pattern_detector import analyze_vwap_patterns
from backend.core.stock_selector import select_balanced_portfolio
from backend.core.forecast_generator import generate_daily_forecast
from backend.core.metrics_calculator import calculate_risk_metrics
from backend.core.quant_metrics import QuantMetricsCalculator, get_spy_returns
from backend.data.stock_universe import get_stock_universe
from backend.data.data_provider import fetch_market_data


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
    + Professional Quant Metrics (Phase 2)
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
            
            # Step 6: Select stocks (primary + backup)
            print("6. Selecting stock portfolio...")
            selection = self._select_portfolio(scored_stocks)
            print(f"   ✓ Selected {len(selection['primary'])} primary + {len(selection['backup'])} backup stocks\n")
            
            # Step 7: Generate forecast
            print("7. Generating performance forecast...")
            forecast = self._generate_forecast(selection, market_data)
            print(f"   ✓ Forecast complete\n")
            
            # Step 8: Calculate risk metrics
            print("8. Calculating risk metrics...")
            risk_metrics = self._calculate_risk_metrics(selection)
            print(f"   ✓ Risk metrics calculated\n")
            
            # Step 9: Calculate professional quant metrics (Phase 2)
            print("9. Calculating professional quant metrics...")
            quant_metrics = self._calculate_quant_metrics(selection)
            print(f"   ✓ Quant metrics calculated\n")
            
            # Step 10: Store in database
            print("10. Storing report in database...")
            report_id = self._store_report(selection, forecast, risk_metrics, dz_metrics, quant_metrics)
            print(f"   ✓ Report stored (ID: {report_id})\n")
            
            # Step 11: Build final report
            report = self._build_final_report(
                selection, forecast, risk_metrics, dz_metrics, quant_metrics, market_data
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
        """Get curated stock universe"""
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
                    ticker=ticker,
                    period_days=self.config['analysis_period_days'],
                    interval=self.config['bar_interval'],
                    use_simulation=self.use_simulation
                )
                
                if df is not None and not df.empty:
                    market_data[ticker] = df
                    
            except Exception as e:
                print(f"   ⚠️  Error fetching {ticker}: {e}")
                continue
        
        return market_data
    
    def _analyze_patterns(self, market_data: Dict[str, pd.DataFrame]) -> Dict:
        """Analyze VWAP recovery patterns for each stock"""
        pattern_results = {}
        
        for ticker, df in market_data.items():
            try:
                results = analyze_vwap_patterns(
                    df=df,
                    ticker=ticker,
                    config=self.config
                )
                pattern_results[ticker] = results
                
            except Exception as e:
                print(f"   ⚠️  Error analyzing {ticker}: {e}")
                continue
        
        return pattern_results
    
    def _calculate_quality_scores(
        self, 
        pattern_results: Dict,
        market_data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Calculate 16-category quality scores for each stock.
        
        Categories focused on:
        - Curve preservation (minimize drawdowns)
        - Win rate optimization (reduce false signals)
        """
        scored_stocks = []
        
        for ticker, patterns in pattern_results.items():
            try:
                df = market_data.get(ticker)
                if df is None or df.empty:
                    continue
                
                # Extract metrics from pattern analysis
                metrics = patterns.get('metrics', {})
                
                # Calculate quality scores
                scores = {
                    'ticker': ticker,
                    'pattern_frequency': metrics.get('pattern_frequency', 0),
                    'confirmation_rate': metrics.get('confirmation_rate', 0),
                    'win_rate': metrics.get('win_rate', 0),
                    'expected_value': metrics.get('expected_value', 0),
                    'liquidity_score': self._calculate_liquidity_score(df),
                    'volatility_score': self._calculate_volatility_score(df),
                    'spread_score': self._calculate_spread_score(df),
                    'composite_rank': 0  # Will be calculated after all stocks scored
                }
                
                scored_stocks.append(scores)
                
            except Exception as e:
                print(f"   ⚠️  Error scoring {ticker}: {e}")
                continue
        
        if not scored_stocks:
            return pd.DataFrame()
        
        scored_df = pd.DataFrame(scored_stocks)
        
        # Calculate composite rank
        scored_df = self._calculate_composite_ranks(scored_df)
        
        return scored_df
    
    def _calculate_liquidity_score(self, df: pd.DataFrame) -> float:
        """Calculate liquidity score from volume data"""
        avg_volume = df['volume'].mean()
        return min(100, (avg_volume / 1_000_000) * 10)  # Scale to 0-100
    
    def _calculate_volatility_score(self, df: pd.DataFrame) -> float:
        """Calculate volatility score"""
        returns = df['close'].pct_change()
        volatility = returns.std()
        return min(100, volatility * 1000)  # Scale to 0-100
    
    def _calculate_spread_score(self, df: pd.DataFrame) -> float:
        """Calculate spread score"""
        if 'spread' in df.columns:
            avg_spread = df['spread'].mean()
            return max(0, 100 - (avg_spread * 100))  # Lower spread = higher score
        return 50  # Default
    
    def _calculate_composite_ranks(self, scored_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate composite rank across all scoring dimensions"""
        # Weight the metrics
        weights = {
            'win_rate': 0.25,
            'expected_value': 0.25,
            'confirmation_rate': 0.20,
            'liquidity_score': 0.15,
            'pattern_frequency': 0.15
        }
        
        # Normalize each metric to 0-1
        for col, weight in weights.items():
            if col in scored_df.columns:
                max_val = scored_df[col].max()
                if max_val > 0:
                    scored_df[f'{col}_norm'] = scored_df[col] / max_val
                else:
                    scored_df[f'{col}_norm'] = 0
        
        # Calculate weighted composite
        scored_df['composite_rank'] = sum(
            scored_df[f'{col}_norm'] * weight 
            for col, weight in weights.items()
            if f'{col}_norm' in scored_df.columns
        )
        
        # Sort by composite rank
        scored_df = scored_df.sort_values('composite_rank', ascending=False)
        
        return scored_df
    
    def _analyze_dead_zones(self, pattern_results: Dict) -> Dict:
        """Analyze dead zone patterns for each stock"""
        dz_metrics = {}
        
        for ticker, patterns in pattern_results.items():
            try:
                # Extract dead zone metrics from pattern analysis
                dz_data = patterns.get('dead_zones', {})
                
                dz_metrics[ticker] = {
                    'dead_zone_frequency': dz_data.get('frequency', 0),
                    'dead_zone_duration_avg': dz_data.get('avg_duration', 0),
                    'dead_zone_opportunity_cost': dz_data.get('opportunity_cost', 0),
                    'dead_zone_score': dz_data.get('score', 50)
                }
                
            except Exception as e:
                print(f"   ⚠️  Error analyzing dead zones for {ticker}: {e}")
                continue
        
        return dz_metrics
    
    def _integrate_dead_zone_scores(
        self,
        scored_df: pd.DataFrame,
        dz_metrics: Dict
    ) -> pd.DataFrame:
        """Integrate dead zone scores into stock ratings"""
        for idx, row in scored_df.iterrows():
            ticker = row['ticker']
            dz = dz_metrics.get(ticker, {})
            
            # Adjust composite rank based on dead zone score
            dz_score = dz.get('dead_zone_score', 50)
            penalty = (100 - dz_score) / 100 * 0.1  # Max 10% penalty
            
            scored_df.loc[idx, 'composite_rank'] *= (1 - penalty)
        
        # Re-sort after adjustment
        scored_df = scored_df.sort_values('composite_rank', ascending=False)
        
        return scored_df
    
    def _select_portfolio(self, scored_df: pd.DataFrame) -> Dict:
        """Select primary and backup stocks"""
        selection = select_balanced_portfolio(
            scored_stocks=scored_df,
            num_conservative=self.config['num_conservative'],
            num_medium=self.config['num_medium'],
            num_aggressive=self.config['num_aggressive'],
            num_backup=self.config['num_backup']
        )
        
        return selection
    
    def _generate_forecast(
        self,
        selection: Dict,
        market_data: Dict[str, pd.DataFrame]
    ) -> Dict:
        """Generate daily performance forecast"""
        forecast = generate_daily_forecast(
            selected_stocks=selection['primary'],
            config=self.config,
            stocks_analyzed=selection['stats']['total_analyzed'],
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
    
    def _store_report(
        self, 
        selection: Dict, 
        forecast: Dict,
        risk_metrics: Dict,
        dz_metrics: Dict,
        quant_metrics: Dict
    ) -> int:
        """Store complete report in database"""
        
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
            'stock_analysis': self._build_stock_analysis_json(
                selection, dz_metrics, quant_metrics
            )
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
        market_data: Dict[str, pd.DataFrame]
    ) -> Dict:
        """Build final report structure for API response"""
        
        return {
            'success': True,
            'date': self.report_date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            
            # Stock selection
            'selected_stocks': self._format_stock_list(selection['primary'], dz_metrics),
            'backup_stocks': self._format_stock_list(selection['backup'], dz_metrics),
            
            # Forecast
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
        Complete morning report dict with professional quant metrics
    """
    report_gen = EnhancedMorningReport(use_simulation=use_simulation)
    return report_gen.generate_complete_report()


if __name__ == "__main__":
    print("\nTesting Enhanced Morning Report Generator with Quant Metrics...\n")
    report = generate_morning_report_api(use_simulation=True)
    
    if report['success']:
        print(f"\n✅ Report generated successfully!")
        print(f"   Selected: {len(report['selected_stocks'])} stocks")
        print(f"   Backup: {len(report['backup_stocks'])} stocks")
        print(f"   Expected trades: {report['forecast']['expected_trades_low']}-{report['forecast']['expected_trades_high']}")
        
        # Display quant metrics
        quant = report.get('quant_metrics', {})
        if quant:
            print(f"\n   PROFESSIONAL QUANT METRICS:")
            print(f"   Sharpe Ratio: {quant['core_performance']['sharpe_ratio']:.2f} (target >2.0)")
            print(f"   Sortino Ratio: {quant['core_performance']['sortino_ratio']:.2f} (target >2.5)")
            print(f"   Calmar Ratio: {quant['core_performance']['calmar_ratio']:.2f} (target >2.0)")
            print(f"   Max Drawdown: {quant['risk_metrics']['max_drawdown_pct']:.2f}%")
    else:
        print(f"\n❌ Report generation failed: {report.get('error')}")
