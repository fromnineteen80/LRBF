"""
Morning Report HTML Generator - Phase 2, Checkpoint 2.5

Generates beautiful HTML morning report from forecast data.
Uses Material Design 3 principles for professional appearance.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
sys.path.append('/home/claude/railyard')

from typing import Dict
from datetime import datetime
from backend.models.database import TradingDatabase




# ============================================================================
# MorningReport Class - Phase 1 Implementation
# Added: October 17, 2025
# Purpose: Orchestrate morning workflow with backup stocks support
# ============================================================================

class MorningReport:
    """
    Morning Report Generator
    
    Orchestrates the complete morning workflow:
    1. Analyze stock universe
    2. Select primary + backup stocks
    3. Generate forecast
    4. Store in database
    5. Return report data for API
    """
    
    def __init__(self, use_simulation=True):
        """
        Initialize morning report generator.
        
        Args:
            use_simulation: Use simulated data (True for testing)
        """
        self.use_simulation = use_simulation
        self.db = TradingDatabase()
    
    def generate_report(self):
        """
        Generate complete morning report with backup stocks.
        
        Returns:
            Dictionary with report data including:
            - selected_stocks: List of primary stock selections
            - backup_stocks: List of 4 backup stocks
            - forecast_data: Expected performance
            - metadata: Report generation info
        """
        try:
            from backend.core.batch_analyzer import analyze_batch, calculate_quality_scores
            from backend.core.stock_selector import select_balanced_portfolio
            from backend.core.forecast_generator import generate_daily_forecast
            from backend.data.stock_universe import get_sample_tickers
            
            # Step 1: Get stock universe
            tickers = get_sample_tickers(20)
            
            # Step 2: Analyze stocks
            results = analyze_batch(
                tickers,
                period="20d",
                interval="1m",
                entry_confirmation_pct=1.5,
                verbose=False,
                use_simulation=self.use_simulation
            )
            
            results = calculate_quality_scores(results)
            
            # Step 3: Select balanced portfolio with backups
            selection = select_balanced_portfolio(
                results,
                n_conservative=2,
                n_medium=4,
                n_aggressive=2
            )
            
            # Extract primary stocks
            selected_stocks = selection['selected']
            selected_tickers = selected_stocks['ticker'].tolist()
            
            # Extract backup stocks (THIS IS THE KEY FIX)
            backup_stocks = selection['backup']
            backup_tickers = backup_stocks['ticker'].tolist()
            
            # Step 4: Generate forecast (with both selected and backup)
            forecast = generate_daily_forecast(
                selected_stocks_df=selected_stocks,
                total_stocks_scanned=selection['total_analyzed'],
                stocks_qualified=selection['total_analyzed'] - selection['rejected_count'],
                backup_stocks_df=backup_stocks
            )
            
            # Step 5: Build stock analysis dict
            stock_analysis = {}
            for _, stock in selected_stocks.iterrows():
                ticker = stock['ticker']
                stock_analysis[ticker] = {
                    'patterns_total': stock.get('vwap_occurred_20d', 0),
                    'entries_total': stock.get('entries_20d', 0),
                    'wins': stock.get('wins_20d', 0),
                    'losses': stock.get('losses_20d', 0),
                    'win_rate': stock.get('win_rate', 0),
                    'avg_win_pct': stock.get('avg_win_pct', 0),
                    'avg_loss_pct': stock.get('avg_loss_pct', 0)
                }
            
            # Step 6: Prepare forecast data for database
            forecast_data = {
                'date': datetime.strptime(forecast['metadata']['date'], '%Y-%m-%d').date(),
                'generated_at': datetime.now(),
                'selected_stocks': selected_tickers,
                'backup_stocks': backup_tickers,  # CRITICAL: Include backup stocks
                'expected_trades_low': forecast['ranges']['trades']['low'],
                'expected_trades_high': forecast['ranges']['trades']['high'],
                'expected_pl_low': forecast['ranges']['profit']['low'],
                'expected_pl_high': forecast['ranges']['profit']['high'],
                'stock_analysis': stock_analysis
            }
            
            # Step 7: Store in database
            forecast_id = self.db.insert_morning_forecast(forecast_data)
            
            # Step 8: Build response
            return {
                'success': True,
                'forecast_id': forecast_id,
                'date': forecast['metadata']['date'],
                'generated_at': datetime.now().isoformat(),
                'selected_stocks': [
                    {
                        'ticker': row['ticker'],
                        'category': row['category'],
                        'quality_score': float(row['quality_score']),
                        'patterns_20d': int(row.get('vwap_occurred_20d', 0)),
                        'win_rate': float(row.get('win_rate', 0)),
                        'atr_pct': float(row.get('atr_pct', 0.02)),
                        'adaptive_threshold': float(row.get('adaptive_threshold', 0.75)),
                        'volatility_category': row.get('volatility_category', 'medium')
                    }
                    for _, row in selected_stocks.iterrows()
                ],
                'backup_stocks': [
                    {
                        'ticker': row['ticker'],
                        'category': row['category'],
                        'quality_score': float(row['quality_score']),
                        'patterns_20d': int(row.get('vwap_occurred_20d', 0)),
                        'win_rate': float(row.get('win_rate', 0)),
                        'atr_pct': float(row.get('atr_pct', 0.02)),
                        'adaptive_threshold': float(row.get('adaptive_threshold', 0.75)),
                        'volatility_category': row.get('volatility_category', 'medium')
                    }
                    for _, row in backup_stocks.iterrows()
                ],
                'forecast': {
                    'expected_trades_low': forecast_data['expected_trades_low'],
                    'expected_trades_high': forecast_data['expected_trades_high'],
                    'expected_pl_low': forecast_data['expected_pl_low'],
                    'expected_pl_high': forecast_data['expected_pl_high']
                },
                'metadata': forecast['metadata']
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        finally:
            self.db.close()


# ============================================================================
# Helper Functions (Original Code Below)
# ============================================================================


def generate_morning_html(forecast: Dict, output_path: str = None) -> str:
    """
    Generate HTML morning report from forecast data.
    NOW ALSO stores forecast in database for live monitor integration.
    
    Args:
        forecast: Forecast dictionary from forecast_generator
        output_path: Where to save HTML (default: output/morning_report_YYYY-MM-DD.html)
    
    Returns:
        Path to generated HTML file
        
    Example:
        >>> from backend.core.forecast_generator import generate_daily_forecast
        >>> from backend.reports.morning_report import generate_morning_html
        >>> 
        >>> forecast = generate_daily_forecast(...)
        >>> html_path = generate_morning_html(forecast)
        >>> print(f"Report: {html_path}")
    """
    
    # === CRITICAL: STORE FORECAST IN DATABASE FOR LIVE MONITOR ===
    # This connects morning report â live monitor â EOD report
    db = TradingDatabase()
    try:
        # Extract selected stock tickers
        selected_tickers = [stock['ticker'] for stock in forecast['stocks']]
        
        # Build stock_analysis dict with per-stock backtest data
        stock_analysis = {}
        for stock in forecast['stocks']:
            ticker = stock['ticker']
            stock_analysis[ticker] = {
                'patterns_total': stock.get('vwap_occurred_20d', 0),  # Total patterns found in backtest
                'patterns_per_day': stock.get('expected_patterns_today', 0),  # Average patterns per day
                'confirmation_rate': stock.get('confirmation_rate', 0),  # Entry confirmation rate
                'expected_entries_per_day': stock.get('expected_entries_today', 0),  # Expected confirmed entries
                'wins': stock.get('wins', 0),  # Winning trades in backtest
                'losses': stock.get('losses', 0),  # Losing trades in backtest
                'win_rate': stock.get('win_rate', 0),  # Win rate from backtest
                'avg_win_pct': stock.get('avg_win_pct', 0),  # Average win %
                'avg_loss_pct': stock.get('avg_loss_pct', 0)  # Average loss %
            }
        
        # Prepare forecast data for database
        forecast_data = {
            'date': datetime.strptime(forecast['metadata']['date'], '%Y-%m-%d').date(),
            'generated_at': datetime.now(),
            'selected_stocks': selected_tickers,
            'backup_stocks': backup_tickers,
            'expected_trades_low': forecast['ranges']['trades']['low'],
            'expected_trades_high': forecast['ranges']['trades']['high'],
            'expected_pl_low': forecast['ranges']['profit']['low'],
            'expected_pl_high': forecast['ranges']['profit']['high'],
            'stock_analysis': stock_analysis  # NEW: Per-stock backtest data
        }
        
        
        # Store in database
        db.insert_morning_forecast(forecast_data)
        print(f"   â Forecast stored in database")
        print(f"      Selected stocks: {', '.join(selected_tickers)}")
        print(f"      Expected trades: {forecast_data['expected_trades_low']}-{forecast_data['expected_trades_high']}")
        print(f"      Expected P&L: ${forecast_data['expected_pl_low']:.0f}-${forecast_data['expected_pl_high']:.0f}")
        print(f"      Stock analysis: {len(stock_analysis)} stocks")
        
    except Exception as e:
        print(f"   â ï¸  Warning: Failed to store forecast in database: {e}")
        print(f"      Continuing with HTML generation...")
    finally:
        db.close()
    # === END DATABASE STORAGE ===
    
    if output_path is None:
        date_str = forecast['metadata']['date']
        output_path = f"/home/claude/railyard/output/morning_report_{date_str}.html"
    
    html = _build_html(forecast)
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    return output_path


def _build_html(forecast: Dict) -> str:
    """Build complete HTML document from forecast data."""
    
    meta = forecast['metadata']
    scan = forecast['scanning']
    summary = forecast['summary']
    stocks = forecast['stocks']
    portfolio = forecast['portfolio']
    ranges = forecast['ranges']
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Morning Report - {meta['date']}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        {_get_css()}
    </style>
</head>
<body>
    <div class="container">
        {_build_header(meta, scan)}
        {_build_summary_cards(summary)}
        {_build_stock_cards(stocks)}
        {_build_forecast_section(ranges, portfolio)}
        {_build_fund_status()}
        {_build_footer()}
    </div>
</body>
</html>"""
    
    return html


def _get_css() -> str:
    """
    Return CSS styles.
    
    Note: This is temporary styling for Phase 2.
    Will be replaced with unified Material Design 3 system
    when building web app in Phase 5.
    """
    
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #f1f5f9;
            min-height: 100vh;
            padding: 2rem;
            color: #1e293b;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            font-size: 2rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 0.5rem;
        }
        
        .header-subtitle {
            font-size: 1.125rem;
            color: #64748b;
            margin-bottom: 1rem;
        }
        
        .header-meta {
            display: flex;
            gap: 2rem;
            font-size: 0.875rem;
            color: #64748b;
        }
        
        .header-meta-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .summary-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
        }
        
        .summary-card-label {
            font-size: 0.875rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        
        .summary-card-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.25rem;
        }
        
        .summary-card-subtext {
            font-size: 0.875rem;
            color: #64748b;
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: white;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .stocks-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stock-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
            position: relative;
        }
        
        .stock-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }
        
        .stock-ticker {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1e293b;
        }
        
        .category-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .category-conservative {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .category-medium {
            background: #ddd6fe;
            color: #5b21b6;
        }
        
        .category-aggressive {
            background: #fed7aa;
            color: #c2410c;
        }
        
        .stock-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        
        .metric {
            display: flex;
            flex-direction: column;
        }
        
        .metric-label {
            font-size: 0.75rem;
            color: #64748b;
            margin-bottom: 0.25rem;
        }
        
        .metric-value {
            font-size: 1.125rem;
            font-weight: 600;
            color: #1e293b;
        }
        
        .quality-bar {
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #e2e8f0;
        }
        
        .quality-bar-label {
            font-size: 0.75rem;
            color: #64748b;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
        }
        
        .quality-bar-track {
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .quality-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }
        
        .forecast-section {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            color: white;
        }
        
        .forecast-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        
        .forecast-metric {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
        }
        
        .forecast-metric-label {
            font-size: 0.875rem;
            opacity: 0.9;
            margin-bottom: 0.5rem;
        }
        
        .forecast-metric-value {
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        
        .forecast-metric-range {
            font-size: 0.875rem;
            opacity: 0.8;
        }
        
        .fund-status {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            color: white;
        }
        
        .fund-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        
        .fund-metric {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 1.25rem;
            backdrop-filter: blur(10px);
        }
        
        .fund-metric-label {
            font-size: 0.875rem;
            opacity: 0.9;
            margin-bottom: 0.5rem;
        }
        
        .fund-metric-value {
            font-size: 1.5rem;
            font-weight: 700;
        }
        
        .footer {
            text-align: center;
            color: white;
            font-size: 0.875rem;
            padding: 2rem 0;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 1rem;
            }
            
            .summary-grid,
            .stocks-grid,
            .forecast-grid,
            .fund-grid {
                grid-template-columns: 1fr;
            }
        }
    """


def _build_header(meta: Dict, scan: Dict) -> str:
    """Build header section."""
    
    return f"""
    <div class="header">
        <h1>THE LUGGAGE ROOM BOYS FUND</h1>
        <div class="header-subtitle">Daily Stock Selection</div>
        <div class="header-meta">
            <div class="header-meta-item">
                <span>ð</span>
                <span>{meta['date_display']}</span>
            </div>
            <div class="header-meta-item">
                <span>ð</span>
                <span>{meta['time_generated']}</span>
            </div>
            <div class="header-meta-item">
                <span>ð</span>
                <span>{scan['total_scanned']} stocks scanned</span>
            </div>
        </div>
    </div>
    """


def _build_summary_cards(summary: Dict) -> str:
    """Build summary cards section."""
    
    universe = summary.get('universe_scanned', {})
    vwap = summary.get('vwap_occurrences', {})
    trades = summary.get('expected_trades', {})
    wl = summary.get('win_loss_record', {})
    
    return f"""
    <div class="summary-grid">
        <div class="summary-card">
            <div class="summary-card-label">Universe Scanned</div>
            <div class="summary-card-value">{universe.get('value', 0)}</div>
            <div class="summary-card-subtext">{universe.get('subtext', '')}</div>
        </div>
        
        <div class="summary-card">
            <div class="summary-card-label">VWAP Occurrences</div>
            <div class="summary-card-value">{vwap.get('value', 0):,}</div>
            <div class="summary-card-subtext">{vwap.get('subtext', '')}</div>
        </div>
        
        <div class="summary-card">
            <div class="summary-card-label">Expected Trades</div>
            <div class="summary-card-value">{trades.get('low', 0)} - {trades.get('high', 0)}</div>
            <div class="summary-card-subtext">{trades.get('subtext', '')}</div>
        </div>
        
        <div class="summary-card">
            <div class="summary-card-label">Win/Loss Record</div>
            <div class="summary-card-value">{wl.get('wins', 0)} W / {wl.get('losses', 0)} L</div>
            <div class="summary-card-subtext">{wl.get('subtext', '')}</div>
        </div>
    </div>
    """


def _build_stock_cards(stocks: list) -> str:
    """Build individual stock cards."""
    
    html = '<h2 class="section-title">ð Selected Stocks (Ranked by Quality Score)</h2>'
    html += '<div class="stocks-grid">'
    
    for idx, stock in enumerate(stocks, 1):
        ticker = stock['ticker']
        category = stock['category']
        
        category_class = f"category-{category.lower()}"
        
        quality_pct = stock['quality_score'] * 100
        
        html += f"""
        <div class="stock-card">
            <div class="stock-header">
                <div>
                    <div class="stock-ticker">#{idx}. {ticker}</div>
                </div>
                <div class="category-badge {category_class}">{category}</div>
            </div>
            
            <div class="stock-metrics">
                <div class="metric">
                    <div class="metric-label">VWAP Occurred (20d)</div>
                    <div class="metric-value">{stock['vwap_occurred_20d']}</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Expected Today</div>
                    <div class="metric-value">{stock['expected_patterns_today']:.1f}</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value">{stock['win_rate']*100:.1f}%</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Expected Entries</div>
                    <div class="metric-value">{stock['expected_entries_today']:.1f}</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Avg Profit</div>
                    <div class="metric-value">+{stock['avg_win_pct']:.2f}%</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Avg Loss</div>
                    <div class="metric-value">{stock['avg_loss_pct']:.2f}%</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Expected P&L</div>
                    <div class="metric-value">${stock['expected_daily_pl']:,.0f}</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">Volatility (ATR)</div>
                    <div class="metric-value">{stock['volatility_atr_pct']:.2f}%</div>
                </div>
            </div>
            
            <div class="quality-bar">
                <div class="quality-bar-label">
                    <span>Quality Score</span>
                    <span>{stock['quality_score']:.3f}</span>
                </div>
                <div class="quality-bar-track">
                    <div class="quality-bar-fill" style="width: {quality_pct}%"></div>
                </div>
            </div>
        </div>
        """
    
    html += '</div>'
    return html


def _build_forecast_section(ranges: Dict, portfolio: Dict) -> str:
    """Build forecast section."""
    
    trades = ranges.get('trades', {})
    profit = ranges.get('profit', {})
    roi = ranges.get('roi', {})
    
    return f"""
    <div class="forecast-section">
        <h2 class="section-title">ð° Portfolio Forecast (Today's Expected Performance)</h2>
        
        <div class="forecast-grid">
            <div class="forecast-metric">
                <div class="forecast-metric-label">Total Entries Expected</div>
                <div class="forecast-metric-value">{trades.get('expected', 0)} trades</div>
                <div class="forecast-metric-range">Range: {trades.get('display', 'N/A')}</div>
            </div>
            
            <div class="forecast-metric">
                <div class="forecast-metric-label">Deployed Capital</div>
                <div class="forecast-metric-value">${portfolio.get('deployed_capital', 0):,.0f}</div>
                <div class="forecast-metric-range">{portfolio.get('num_positions', 0)} positions Ã ${portfolio.get('position_size', 0):,.0f}</div>
            </div>
            
            <div class="forecast-metric">
                <div class="forecast-metric-label">Expected Daily P&L</div>
                <div class="forecast-metric-value">${profit.get('expected', 0):,.0f}</div>
                <div class="forecast-metric-range">Range: {profit.get('display', 'N/A')}</div>
            </div>
            
            <div class="forecast-metric">
                <div class="forecast-metric-label">Expected Daily ROI</div>
                <div class="forecast-metric-value">{roi.get('expected', 0):.2f}%</div>
                <div class="forecast-metric-range">Range: {roi.get('display', 'N/A')}</div>
            </div>
        </div>
    </div>
    """


def _build_fund_status() -> str:
    """Build fund status section (placeholder data)."""
    
    return """
    <div class="fund-status">
        <h2 class="section-title">ð Fund Status</h2>
        
        <div class="fund-grid">
            <div class="fund-metric">
                <div class="fund-metric-label">Last Trading Day P&L</div>
                <div class="fund-metric-value">$0</div>
            </div>
            
            <div class="fund-metric">
                <div class="fund-metric-label">Principal</div>
                <div class="fund-metric-value">$30,000</div>
            </div>
            
            <div class="fund-metric">
                <div class="fund-metric-label">ROI This Month</div>
                <div class="fund-metric-value">0.00%</div>
            </div>
            
            <div class="fund-metric">
                <div class="fund-metric-label">ROI This Year</div>
                <div class="fund-metric-value">0.00%</div>
            </div>
        </div>
    </div>
    """


def _build_footer() -> str:
    """Build footer."""
    
    return """
    <div class="footer">
        <p>Built with â¤ï¸ for The Luggage Room Boys Fund</p>
        <p>Recovery Engine Trading Strategy | Railyard Markets</p>
    </div>
    """


if __name__ == "__main__":
    print("\n" + "="*80)
    print("MORNING REPORT GENERATOR TEST - Checkpoint 2.5")
    print("="*80)
    print()
    
    # Import dependencies
    from backend.core.batch_analyzer import analyze_batch, calculate_quality_scores
    from backend.core.stock_selector import select_balanced_portfolio, get_portfolio_configurations
    from backend.core.forecast_generator import generate_daily_forecast
    from backend.data.stock_universe import get_sample_tickers
    
    print("Running complete workflow...")
    print()
    
    # Step 1: Analyze stocks
    print("1. Analyzing 20 sample stocks...")
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
    
    results = calculate_quality_scores(results)
    print(f"   â Analyzed {len(results)} stocks")
    
    # Step 2: Select portfolio
    print("2. Selecting portfolio (2/3/3)...")
    configs = get_portfolio_configurations()
    selection = select_balanced_portfolio(
        results,
        **configs['aggressive'],
        min_confirmation_rate=0.25,
        min_expected_value=0.0,
        min_entries_per_day=3.0
    )
    print(f"   â Selected {len(selection['selected'])} stocks")
    
    # Step 3: Generate forecast
    print("3. Generating forecast...")
    forecast = generate_daily_forecast(
        selected_stocks_df=selection['selected'],
        total_stocks_scanned=len(sample_tickers),
        stocks_qualified=len(results)
    )
    print(f"   â Forecast generated")
    
    # Step 4: Generate HTML
    print("4. Generating HTML morning report...")
    html_path = generate_morning_html(forecast)
    print(f"   â HTML saved to: {html_path}")
    
    # Step 5: Generate Capitalise.ai prompts
    print("5. Generating Capitalise.ai prompts...")
    from backend.services.capitalise_prompts import generate_capitalise_prompts
    selected_tickers = [stock['ticker'] for stock in forecast['stocks']]
    prompt_files = generate_capitalise_prompts(selected_tickers)
    print(f"   â Generated {len(prompt_files)} prompts")
    print(f"   ð Saved to: /home/claude/railyard/output/capitalise_prompts/")
    print()
    
    print("="*80)
    print("â MORNING REPORT COMPLETE!")
    print("="*80)
    print()
    print(f"Open the report in your browser:")
    print(f"   file://{html_path}")
    print()
    print("Capitalise.ai prompts ready for deployment:")
    print(f"   {len(prompt_files)} files in output/capitalise_prompts/")
    print()
    print("Or copy to outputs for download:")
    print(f"   cp {html_path} /mnt/user-data/outputs/")
    print(f"   cp output/capitalise_prompts/* /mnt/user-data/outputs/")
    print()

