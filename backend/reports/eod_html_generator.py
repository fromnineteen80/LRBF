"""
EOD HTML Generator - Phase 4
Beautiful HTML report generation with Material Design 3.

Generates comprehensive EOD report with:
1. Forecast vs. Actual Comparison
2. Execution Quality Breakdown
3. Win Rate Analysis
4. Decision Tree Recommendation

Author: The Luggage Room Boys Fund
Date: October 2025
"""

from typing import Dict


def generate_eod_html(report: Dict, output_path: str) -> str:
    """
    Generate beautiful HTML EOD report.
    
    Args:
        report: Report dictionary from eod_reporter
        output_path: Where to save HTML file
    
    Returns:
        Path to generated HTML file
    """
    
    html = _build_html(report)
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    return output_path


def _build_html(report: Dict) -> str:
    """Build complete HTML document from report data."""
    
    meta = report['metadata']
    forecast = report['forecast']
    actual = report['actual']
    evaluation = report['evaluation']
    decision = report['decision_tree']
    trends = report['trends']
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EOD Report - {meta['date']}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            color: #1a202c;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 36px;
            font-weight: 700;
            color: #1a202c;
            margin-bottom: 8px;
        }}
        
        .header .subtitle {{
            font-size: 18px;
            color: #718096;
        }}
        
        .section {{
            background: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 700;
            color: #1a202c;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .section-title .number {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: 700;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}
        
        .metric-card {{
            background: #f7fafc;
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }}
        
        .metric-label {{
            font-size: 14px;
            color: #718096;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        
        .metric-value {{
            font-size: 28px;
            font-weight: 700;
            color: #1a202c;
        }}
        
        .metric-value.positive {{
            color: #48bb78;
        }}
        
        .metric-value.negative {{
            color: #f56565;
        }}
        
        .gap-analysis {{
            background: #fff5f5;
            border-radius: 12px;
            padding: 24px;
            border-left: 4px solid #f56565;
            margin-top: 20px;
        }}
        
        .gap-analysis.low {{
            background: #f0fff4;
            border-left-color: #48bb78;
        }}
        
        .gap-analysis.medium {{
            background: #fffaf0;
            border-left-color: #ed8936;
        }}
        
        .gap-label {{
            font-size: 16px;
            font-weight: 600;
            color: #1a202c;
            margin-bottom: 12px;
        }}
        
        .gap-value {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .gap-value.low {{
            color: #48bb78;
        }}
        
        .gap-value.medium {{
            color: #ed8936;
        }}
        
        .gap-value.high {{
            color: #f56565;
        }}
        
        .execution-flow {{
            background: #f7fafc;
            border-radius: 12px;
            padding: 24px;
            margin-top: 20px;
        }}
        
        .flow-item {{
            display: flex;
            align-items: center;
            padding: 16px;
            background: white;
            border-radius: 8px;
            margin-bottom: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .flow-item:last-child {{
            margin-bottom: 0;
        }}
        
        .flow-label {{
            flex: 1;
            font-weight: 600;
            color: #2d3748;
        }}
        
        .flow-value {{
            font-size: 20px;
            font-weight: 700;
            color: #1a202c;
            margin-right: 12px;
        }}
        
        .flow-delta {{
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
        }}
        
        .flow-delta.negative {{
            background: #fed7d7;
            color: #c53030;
        }}
        
        .flow-delta.neutral {{
            background: #e2e8f0;
            color: #4a5568;
        }}
        
        .causes-list {{
            margin-top: 16px;
            padding: 20px;
            background: #f7fafc;
            border-radius: 8px;
        }}
        
        .causes-list ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .causes-list li {{
            padding: 8px 0;
            padding-left: 24px;
            position: relative;
        }}
        
        .causes-list li:before {{
            content: "•";
            position: absolute;
            left: 8px;
            color: #667eea;
            font-weight: 700;
            font-size: 18px;
        }}
        
        .decision-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 32px;
            margin-top: 20px;
        }}
        
        .decision-box.low {{
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        }}
        
        .decision-box.medium {{
            background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
        }}
        
        .decision-box.high {{
            background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
        }}
        
        .decision-badge {{
            display: inline-block;
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 16px;
        }}
        
        .decision-action {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 20px;
        }}
        
        .justification-list {{
            margin-bottom: 24px;
        }}
        
        .justification-list li {{
            padding: 8px 0;
            padding-left: 24px;
            position: relative;
        }}
        
        .justification-list li:before {{
            content: "âœ"";
            position: absolute;
            left: 0;
            font-weight: 700;
        }}
        
        .next-steps {{
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            padding: 20px;
        }}
        
        .next-steps h4 {{
            margin-bottom: 12px;
            font-size: 16px;
        }}
        
        .next-steps ol {{
            padding-left: 24px;
        }}
        
        .next-steps li {{
            padding: 6px 0;
        }}
        
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .comparison-table th {{
            background: #f7fafc;
            padding: 16px;
            text-align: left;
            font-weight: 600;
            color: #2d3748;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        .comparison-table td {{
            padding: 16px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .comparison-table tr:hover {{
            background: #f7fafc;
        }}
        
        .trend-card {{
            background: #f7fafc;
            border-radius: 12px;
            padding: 24px;
            margin-top: 20px;
        }}
        
        .trend-metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .trend-metric:last-child {{
            border-bottom: none;
        }}
        
        .trend-label {{
            font-weight: 600;
            color: #2d3748;
        }}
        
        .trend-value {{
            font-size: 20px;
            font-weight: 700;
            color: #1a202c;
        }}
        
        .bottleneck-highlight {{
            background: #fff5f5;
            border-left: 4px solid #f56565;
            padding: 16px;
            border-radius: 8px;
            margin-top: 16px;
        }}
        
        .bottleneck-highlight.low {{
            background: #f0fff4;
            border-left-color: #48bb78;
        }}
        
        .bottleneck-label {{
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 8px;
        }}
        
        .bottleneck-description {{
            color: #4a5568;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>End of Day Report</h1>
            <div class="subtitle">
                {meta['date']} | Generated {meta['generated_at'][:19]}
            </div>
        </div>
        
        <!-- Section 1: Forecast vs. Actual -->
        <div class="section">
            <div class="section-title">
                <span class="number">1</span>
                <span>FORECAST VS. ACTUAL COMPARISON</span>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">MORNING FORECAST</div>
                    <div class="metric-value">
                        {forecast['expected_trades_low']}-{forecast['expected_trades_high']} trades
                    </div>
                    <div class="metric-label" style="margin-top: 12px;">Expected P&L</div>
                    <div class="metric-value" style="font-size: 20px;">
                        ${forecast['expected_pl_low']:.0f}-${forecast['expected_pl_high']:.0f}
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">ACTUAL RESULTS</div>
                    <div class="metric-value">
                        {actual['trade_count']} trades
                    </div>
                    <div class="metric-label" style="margin-top: 12px;">Realized P&L</div>
                    <div class="metric-value {'positive' if actual['realized_pl'] > 0 else 'negative'}" style="font-size: 20px;">
                        ${actual['realized_pl']:.2f}
                    </div>
                </div>
            </div>
            
            {_build_gap_analysis_section(forecast, actual)}
        </div>
        
        <!-- Section 2: Execution Quality Breakdown -->
        <div class="section">
            <div class="section-title">
                <span class="number">2</span>
                <span>EXECUTION QUALITY BREAKDOWN</span>
            </div>
            
            <div class="gap-label" style="font-size: 18px; margin-bottom: 20px;">
                📊 Where Did We Lose Trades?
            </div>
            
            <div class="execution-flow">
                <div class="flow-item">
                    <div class="flow-label">Morning Backtest Found:</div>
                    <div class="flow-value">{evaluation['backtest']['patterns_found']}</div>
                    <div class="flow-delta neutral">patterns</div>
                </div>
                
                <div class="flow-item">
                    <div class="flow-label">├─ Capitalise.ai Detected:</div>
                    <div class="flow-value">{evaluation['actual']['patterns_detected']}</div>
                    <div class="flow-delta {'negative' if evaluation['gaps']['pattern_detection_gap_pct'] > 5 else 'neutral'}">
                        ({'-' if evaluation['gaps']['pattern_detection_gap_pct'] > 0 else ''}{evaluation['gaps']['pattern_detection_gap_pct']:.0f}%)
                    </div>
                </div>
                
                <div class="flow-item">
                    <div class="flow-label">├─ Entry Confirmed:</div>
                    <div class="flow-value">{evaluation['actual']['entries_executed']}</div>
                    <div class="flow-delta {'negative' if evaluation['gaps']['entry_confirmation_gap_pct'] > 5 else 'neutral'}">
                        ({'-' if evaluation['gaps']['entry_confirmation_gap_pct'] > 0 else ''}{evaluation['gaps']['entry_confirmation_gap_pct']:.0f}%)
                    </div>
                </div>
                
                <div class="flow-item">
                    <div class="flow-label">└─ Trades Executed:</div>
                    <div class="flow-value">{actual['trade_count']}</div>
                    <div class="flow-delta neutral">
                        (100%)
                    </div>
                </div>
            </div>
            
            {_build_bottleneck_section(evaluation['bottleneck'])}
        </div>
        
        <!-- Section 3: Win Rate Analysis -->
        <div class="section">
            <div class="section-title">
                <span class="number">3</span>
                <span>WIN RATE ANALYSIS</span>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">EXPECTED WIN RATE</div>
                    <div class="metric-value">
                        {evaluation['backtest']['win_rate']*100:.1f}%
                    </div>
                    <div class="metric-label" style="margin-top: 8px; font-size: 12px;">
                        (from backtest)
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">ACTUAL WIN RATE</div>
                    <div class="metric-value {'positive' if evaluation['gaps']['win_rate_delta'] >= 0 else 'negative'}">
                        {evaluation['actual']['win_rate']*100:.1f}%
                    </div>
                    <div class="metric-label" style="margin-top: 8px; font-size: 12px;">
                        ({evaluation['gaps']['win_rate_delta']*100:+.1f}%)
                    </div>
                </div>
            </div>
            
            {_build_win_rate_causes(evaluation['gaps'])}
        </div>
        
        <!-- Section 4: Decision Tree Recommendation -->
        <div class="section">
            <div class="section-title">
                <span class="number">4</span>
                <span>DECISION TREE RECOMMENDATION</span>
            </div>
            
            {_build_decision_box(decision)}
        </div>
        
        <!-- Trends Section -->
        {_build_trends_section(trends)}
        
        <!-- Per-Stock Performance -->
        {_build_per_stock_section(actual['per_stock'])}
    </div>
</body>
</html>
"""
    
    return html


def _build_gap_analysis_section(forecast: Dict, actual: Dict) -> str:
    """Build the gap analysis display."""
    
    expected_mid = forecast['expected_trades_mid']
    actual_trades = actual['trade_count']
    
    if expected_mid > 0:
        gap_pct = ((actual_trades - expected_mid) / expected_mid) * 100
    else:
        gap_pct = 0.0
    
    # Determine severity
    abs_gap = abs(gap_pct)
    if abs_gap < 10:
        severity_class = "low"
        severity_label = "LOW"
    elif abs_gap < 25:
        severity_class = "medium"
        severity_label = "MEDIUM"
    else:
        severity_class = "high"
        severity_label = "HIGH"
    
    return f"""
    <div class="gap-analysis {severity_class}">
        <div class="gap-label">Gap Analysis</div>
        <div class="gap-value {severity_class}">{gap_pct:+.0f}%</div>
        <div style="color: #4a5568; font-size: 14px;">
            {'Above' if gap_pct > 0 else 'Below'} forecast (Severity: {severity_label})
        </div>
    </div>
    """


def _build_bottleneck_section(bottleneck: Dict) -> str:
    """Build the bottleneck highlight section."""
    
    severity = bottleneck['severity_pct']
    
    if severity < 15:
        severity_class = "low"
    elif severity < 30:
        severity_class = "medium"
    else:
        severity_class = "high"
    
    return f"""
    <div class="bottleneck-highlight {severity_class}">
        <div class="bottleneck-label">PRIMARY BOTTLENECK: {bottleneck['primary'].replace('_', ' ').title()} ({severity:.0f}%)</div>
        <div class="bottleneck-description">{bottleneck['description']}</div>
    </div>
    """


def _build_win_rate_causes(gaps: Dict) -> str:
    """Build possible causes section for win rate delta."""
    
    delta = gaps['win_rate_delta']
    
    if abs(delta) < 0.03:  # Less than 3% difference
        causes = [
            "Win rate is tracking closely to backtest expectations",
            "Execution quality is maintaining edge",
            "No significant degradation detected"
        ]
    else:
        causes = [
            "Slippage may be eating into edge" if delta < 0 else "Execution quality exceeding expectations",
            "Exit logic performance vs. backtest" if delta < 0 else "Better exit timing than backtested",
            "Market conditions may differ from backtest period"
        ]
    
    causes_html = '\n'.join(f'<li>{cause}</li>' for cause in causes)
    
    return f"""
    <div class="causes-list">
        <div class="gap-label" style="margin-bottom: 12px;">Possible Causes:</div>
        <ul>
            {causes_html}
        </ul>
    </div>
    """


def _build_decision_box(decision: Dict) -> str:
    """Build the decision recommendation box."""
    
    severity = decision['severity'].lower().replace('-', '')
    
    action_text = {
        'continue_capitalise': 'âœ… RECOMMENDED ACTION: Continue with Capitalise.ai',
        'monitor_closely': '⚠️ RECOMMENDED ACTION: Monitor closely, collect more data',
        'consider_custom_engine': 'ðŸ"§ RECOMMENDED ACTION: Consider building custom execution engine',
        'build_custom_engine': 'ðŸš€ RECOMMENDED ACTION: Build custom execution engine (HIGH PRIORITY)'
    }
    
    action_display = action_text.get(decision['recommended_action'], decision['recommended_action'])
    
    justification_html = '\n'.join(f'<li>{item}</li>' for item in decision['justification'])
    next_steps_html = '\n'.join(f'<li>{step}</li>' for step in decision['next_steps'])
    
    improvement_low, improvement_high = decision['estimated_improvement_pct']
    
    return f"""
    <div class="decision-box {severity}">
        <div class="decision-badge">Gap Size: {decision['gap_size_pct']:.0f}% ({decision['severity']})</div>
        <div class="decision-action">{action_display}</div>
        
        <div class="justification-list">
            <strong>Justification:</strong>
            <ul>
                {justification_html}
            </ul>
        </div>
        
        <div style="margin-bottom: 20px;">
            <strong>Estimated Improvement with Custom Engine:</strong> {improvement_low:.0f}%-{improvement_high:.0f}%
        </div>
        
        <div class="next-steps">
            <h4>Next Steps:</h4>
            <ol>
                {next_steps_html}
            </ol>
        </div>
    </div>
    """


def _build_trends_section(trends: Dict) -> str:
    """Build the trends section."""
    
    if trends['days_tracked'] == 0:
        return """
        <div class="section">
            <div class="section-title">
                <span class="number">5</span>
                <span>TRENDS</span>
            </div>
            <p>Not enough historical data for trend analysis.</p>
        </div>
        """
    
    last_5 = trends['last_5_days']
    
    return f"""
    <div class="section">
        <div class="section-title">
            <span class="number">5</span>
            <span>TRENDS (LAST 5 DAYS)</span>
        </div>
        
        <div class="trend-card">
            <div class="trend-metric">
                <div class="trend-label">Total P&L:</div>
                <div class="trend-value {'positive' if last_5['total_pl'] > 0 else 'negative'}">
                    ${last_5['total_pl']:.2f}
                </div>
            </div>
            
            <div class="trend-metric">
                <div class="trend-label">Average ROI:</div>
                <div class="trend-value {'positive' if last_5['avg_roi_pct'] > 0 else 'negative'}">
                    {last_5['avg_roi_pct']:.2f}%
                </div>
            </div>
            
            <div class="trend-metric">
                <div class="trend-label">Average Win Rate:</div>
                <div class="trend-value">
                    {last_5['avg_win_rate']*100:.1f}%
                </div>
            </div>
            
            <div class="trend-metric">
                <div class="trend-label">Total Trades:</div>
                <div class="trend-value">
                    {last_5['total_trades']}
                </div>
            </div>
        </div>
    </div>
    """


def _build_per_stock_section(per_stock: Dict) -> str:
    """Build per-stock performance table."""
    
    if not per_stock:
        return ""
    
    rows = ""
    for ticker, data in sorted(per_stock.items()):
        pl_class = 'positive' if data['realized_pl'] > 0 else 'negative'
        
        rows += f"""
        <tr>
            <td><strong>{ticker}</strong></td>
            <td>{data['trades']}</td>
            <td>{data['wins']}</td>
            <td>{data['losses']}</td>
            <td>{data['win_rate']*100:.1f}%</td>
            <td class="{pl_class}"><strong>${data['realized_pl']:.2f}</strong></td>
        </tr>
        """
    
    return f"""
    <div class="section">
        <div class="section-title">
            <span class="number">6</span>
            <span>PER-STOCK PERFORMANCE</span>
        </div>
        
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Trades</th>
                    <th>Wins</th>
                    <th>Losses</th>
                    <th>Win Rate</th>
                    <th>Realized P&L</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """
