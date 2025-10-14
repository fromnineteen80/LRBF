"""
Live Monitor - Phase 3, Checkpoints 3.7 & 3.8

Real-time trading dashboard that monitors performance vs. forecast.
Auto-refreshes every 5 seconds during market hours.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
sys.path.append('/home/claude/railyard')

import time
from datetime import datetime, date
from typing import Dict, Optional
from config import TradingConfig as cfg
from modules.ibkr_connector import IBKRConnector
from modules.database import TradingDatabase
from modules.metrics_calculator import MetricsCalculator


def generate_live_dashboard_html(
    account_data: Dict,
    metrics: Dict,
    forecast: Dict,
    comparison: Dict,
    connection_health: Dict,
    per_stock_data: Dict,
    system_events: list,
    timestamp: datetime
) -> str:
    """
    Generate HTML for live monitoring dashboard.
    
    Args:
        account_data: From IBKR get_account_balance()
        metrics: From MetricsCalculator
        forecast: From database morning_forecasts
        comparison: From MetricsCalculator compare_to_forecast()
        connection_health: From IBKR check_connection()
        per_stock_data: Per-ticker breakdown
        system_events: Recent system events
        timestamp: Current time
    
    Returns:
        HTML string
    """
    
    # Status indicators
    connection_status = "🟢 Connected" if connection_health['connected'] else "🔴 Disconnected"
    latency_color = "green" if connection_health.get('latency_ms', 100) < 50 else "orange"
    
    # Forecast comparison colors
    trades_color = _get_comparison_color(comparison['trades']['vs_forecast'])
    pl_color = _get_comparison_color(comparison['pl']['vs_forecast'])
    
    # Daily loss limit check
    roi_pct = metrics['roi_pct']
    loss_limit_pct = cfg.DAILY_LOSS_LIMIT
    at_risk = roi_pct <= (loss_limit_pct * 0.8)  # Warning at 80% of limit
    
    # System status
    if at_risk:
        system_status = "⚠️ WARNING: Approaching Daily Loss Limit"
        status_color = "#ff9800"
    elif not comparison['on_track']:
        system_status = "ℹ️ Performance Outside Expected Range"
        status_color = "#2196F3"
    else:
        system_status = "✅ Operating Normally"
        status_color = "#4CAF50"
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="5">
    <title>Live Monitor | The Luggage Room Boys Fund</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #ffffff;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 2.5em;
            font-weight: 300;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .timestamp {{
            font-size: 0.9em;
            opacity: 0.7;
            margin-top: 10px;
        }}
        
        .status-bar {{
            background: {status_color};
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-size: 1.1em;
            font-weight: 500;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        .card h2 {{
            font-size: 1.3em;
            font-weight: 400;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }}
        
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .metric:last-child {{
            border-bottom: none;
        }}
        
        .metric-label {{
            opacity: 0.8;
        }}
        
        .metric-value {{
            font-weight: 600;
            font-size: 1.2em;
        }}
        
        .positive {{
            color: #4CAF50;
        }}
        
        .negative {{
            color: #f44336;
        }}
        
        .warning {{
            color: #ff9800;
        }}
        
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        .table th {{
            text-align: left;
            padding: 10px;
            background: rgba(255, 255, 255, 0.1);
            font-weight: 500;
        }}
        
        .table td {{
            padding: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }}
        
        .progress-fill {{
            height: 100%;
            background: #4CAF50;
            transition: width 0.3s ease;
        }}
        
        .event-log {{
            max-height: 200px;
            overflow-y: auto;
            font-size: 0.9em;
        }}
        
        .event-item {{
            padding: 8px;
            margin-bottom: 5px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
            border-left: 3px solid #2196F3;
        }}
        
        .event-item.warning {{
            border-left-color: #ff9800;
        }}
        
        .event-item.error {{
            border-left-color: #f44336;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Live Monitor</h1>
            <div class="subtitle">The Luggage Room Boys Fund</div>
            <div class="timestamp">Last updated: {timestamp.strftime('%I:%M:%S %p ET')} | Auto-refresh: 5s</div>
        </header>
        
        <div class="status-bar">
            {system_status}
        </div>
        
        <div class="grid">
            <!-- Account Overview -->
            <div class="card">
                <h2>Account Overview</h2>
                <div class="metric">
                    <span class="metric-label">Total Balance</span>
                    <span class="metric-value">${account_data['total_balance']:,.2f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Deployed Capital</span>
                    <span class="metric-value">${account_data['deployed_capital']:,.2f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Reserve</span>
                    <span class="metric-value">${account_data['reserve_capital']:,.2f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Connection</span>
                    <span class="metric-value">{connection_status}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Latency</span>
                    <span class="metric-value" style="color: {latency_color}">{connection_health.get('latency_ms', 0):.1f}ms</span>
                </div>
            </div>
            
            <!-- Today's Performance -->
            <div class="card">
                <h2>Today's Performance</h2>
                <div class="metric">
                    <span class="metric-label">Realized P&L</span>
                    <span class="metric-value {'positive' if metrics['realized_pl'] > 0 else 'negative'}">${metrics['realized_pl']:,.2f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">ROI</span>
                    <span class="metric-value {'positive' if roi_pct > 0 else 'negative'}">{roi_pct:.2f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Trades Executed</span>
                    <span class="metric-value">{metrics['trade_count']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Win Rate</span>
                    <span class="metric-value">{metrics['win_rate']*100:.1f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Wins / Losses</span>
                    <span class="metric-value">{metrics['win_count']} / {metrics['loss_count']}</span>
                </div>
            </div>
            
            <!-- Forecast Comparison -->
            <div class="card">
                <h2>vs. Morning Forecast</h2>
                <div class="metric">
                    <span class="metric-label">Expected Trades</span>
                    <span class="metric-value">{comparison['trades']['expected_low']}-{comparison['trades']['expected_high']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Actual Trades</span>
                    <span class="metric-value" style="color: {trades_color}">{comparison['trades']['actual']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Expected P&L</span>
                    <span class="metric-value">${comparison['pl']['expected_low']:,.0f}-${comparison['pl']['expected_high']:,.0f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Actual P&L</span>
                    <span class="metric-value" style="color: {pl_color}">${comparison['pl']['actual']:,.2f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Status</span>
                    <span class="metric-value">{'✅ On Track' if comparison['on_track'] else '⚠️ Off Track'}</span>
                </div>
            </div>
        </div>
        
        <!-- Per-Stock Performance -->
        <div class="card">
            <h2>Per-Stock Performance</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Trades</th>
                        <th>P&L</th>
                        <th>Win Rate</th>
                        <th>W/L</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add per-stock rows
    for ticker, data in sorted(per_stock_data.items(), key=lambda x: x[1]['realized_pl'], reverse=True):
        pl_class = 'positive' if data['realized_pl'] > 0 else 'negative'
        html += f"""
                    <tr>
                        <td><strong>{ticker}</strong></td>
                        <td>{data['trade_count']}</td>
                        <td class="{pl_class}">${data['realized_pl']:,.2f}</td>
                        <td>{data['win_rate']*100:.1f}%</td>
                        <td>{data['win_count']}/{data['loss_count']}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
        
        <!-- System Events -->
        <div class="card">
            <h2>Recent Events</h2>
            <div class="event-log">
    """
    
    # Add system events
    for event in system_events[-10:]:  # Last 10 events
        event_class = event.get('severity', 'LOW').lower()
        # Parse timestamp if it's a string
        if isinstance(event['timestamp'], str):
            ts = datetime.fromisoformat(event['timestamp'])
        else:
            ts = event['timestamp']
        html += f"""
                <div class="event-item {event_class}">
                    <strong>{ts.strftime('%H:%M:%S')}</strong> | {event['event_type']} | {event['message']}
                </div>
        """
    
    html += """
            </div>
        </div>
        
    </div>
</body>
</html>
    """
    
    return html


def _get_comparison_color(status: str) -> str:
    """Get color for forecast comparison status."""
    if status == 'within':
        return '#4CAF50'  # Green
    elif status == 'below':
        return '#ff9800'  # Orange
    else:  # above
        return '#2196F3'  # Blue


class LiveMonitor:
    """
    Live monitoring system - main loop.
    
    Runs during market hours, updating dashboard every 5 seconds.
    """
    
    def __init__(
        self,
        use_simulation: bool = True,
        refresh_interval: int = 5
    ):
        """
        Initialize live monitor.
        
        Args:
            use_simulation: Use simulated data (default True)
            refresh_interval: Seconds between updates (default 5)
        """
        self.use_simulation = use_simulation
        self.refresh_interval = refresh_interval
        
        # Initialize components
        self.ibkr = IBKRConnector(use_simulation=use_simulation)
        self.db = TradingDatabase()
        self.calc = MetricsCalculator()
        
        # State
        self.running = False
        self.opening_balance = None
        self.selected_stocks = []  # Track stocks selected in morning report
    
    def start(self):
        """Start the monitoring loop."""
        print("Starting Live Monitor...")
        print("=" * 60)
        
        # Connect to IBKR
        if not self.ibkr.connect():
            print("❌ Failed to connect to IBKR")
            return
        
        print("✅ Connected to IBKR")
        
        # Get opening balance
        account = self.ibkr.get_account_balance()
        self.opening_balance = account['total_balance']
        print(f"📊 Opening balance: ${self.opening_balance:,.2f}")
        
        # Load morning forecast
        today = date.today()
        forecast = self.db.get_morning_forecast(today)
        
        if not forecast:
            print("⚠️  No morning forecast found for today")
            print("   Run morning report first!")
            print("   Continuing with empty forecast (monitoring all fills)...")
            forecast = {
                'expected_trades_low': 0,
                'expected_trades_high': 0,
                'expected_pl_low': 0,
                'expected_pl_high': 0,
                'selected_stocks': []
            }
            self.selected_stocks = []
        else:
            # Extract selected stocks from forecast
            self.selected_stocks = forecast.get('selected_stocks', [])
            print(f"✅ Loaded morning forecast")
            print(f"   📊 Tracking stocks: {', '.join(self.selected_stocks)}")
            print(f"   📈 Expected: {forecast['expected_trades_low']}-{forecast['expected_trades_high']} trades")
            print(f"   💰 Expected P&L: ${forecast['expected_pl_low']:.0f}-${forecast['expected_pl_high']:.0f}")
        
        # Log start event
        self.db.log_event(
            event_type='INFO',
            severity='LOW',
            message=f'Live monitor started - Opening balance: ${self.opening_balance:,.2f}'
        )
        
        print("\n🚀 Monitor running - Press Ctrl+C to stop")
        print(f"📁 Dashboard: /home/claude/railyard/output/live_dashboard.html")
        print("=" * 60)
        
        self.running = True
        
        try:
            while self.running:
                self._update_dashboard(forecast)
                time.sleep(self.refresh_interval)
        
        except KeyboardInterrupt:
            print("\n\n⏸️ Stopping monitor...")
            self.stop()
    
    def _update_dashboard(self, forecast: Dict):
        """Update dashboard with latest data."""
        
        # Get current data
        account = self.ibkr.get_account_balance()
        fills = self.ibkr.get_fills()
        connection_health = self.ibkr.check_connection()
        
        # CRITICAL: Filter fills to only selected stocks if we have a forecast
        # This ensures we're only tracking the stocks from morning analysis
        if self.selected_stocks:
            fills = [
                fill for fill in fills 
                if fill['ticker'] in self.selected_stocks
            ]
        
        # Calculate metrics (now only on selected stocks)
        metrics = self.calc.calculate_daily_metrics(
            fills=fills,
            opening_balance=self.opening_balance,
            closing_balance=account['total_balance']
        )
        
        # Compare to forecast
        comparison = self.calc.compare_to_forecast(metrics, forecast)
        
        # Get system events
        events = self.db.get_events_by_date(date.today())
        
        # Check for daily loss limit
        if metrics['roi_pct'] <= cfg.DAILY_LOSS_LIMIT:
            self.db.log_event(
                event_type='WARNING',
                severity='CRITICAL',
                message=f'Daily loss limit reached: {metrics["roi_pct"]:.2f}% (limit: {cfg.DAILY_LOSS_LIMIT}%)'
            )
            print(f"\n🛑 DAILY LOSS LIMIT REACHED: {metrics['roi_pct']:.2f}%")
            print("   Monitor will continue tracking but trading should be paused")
        
        # Generate HTML
        html = generate_live_dashboard_html(
            account_data=account,
            metrics=metrics,
            forecast=forecast,
            comparison=comparison,
            connection_health=connection_health,
            per_stock_data=metrics['per_stock'],
            system_events=events,
            timestamp=datetime.now()
        )
        
        # Save HTML
        output_path = "/home/claude/railyard/output/live_dashboard.html"
        with open(output_path, 'w') as f:
            f.write(html)
        
        # Print status update
        status = "✅" if comparison['on_track'] else "⚠️"
        print(f"{status} {datetime.now().strftime('%H:%M:%S')} | Trades: {metrics['trade_count']} | P&L: ${metrics['realized_pl']:,.2f} | ROI: {metrics['roi_pct']:.2f}%")
    
    def stop(self):
        """Stop the monitoring loop."""
        self.running = False
        
        # Log stop event
        self.db.log_event(
            event_type='INFO',
            severity='LOW',
            message='Live monitor stopped'
        )
        
        # Disconnect
        self.ibkr.disconnect()
        self.db.close()
        
        print("✅ Monitor stopped")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import os
    
    # Create output directory
    os.makedirs("/home/claude/railyard/output", exist_ok=True)
    
    # Run live monitor in simulation mode
    monitor = LiveMonitor(use_simulation=True, refresh_interval=5)
    monitor.start()
