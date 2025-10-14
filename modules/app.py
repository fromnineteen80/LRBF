#!/usr/bin/env python3
"""
The Luggage Room Boys Fund - Unified Dashboard Application

This combines:
- Complete backend functionality (IBKR APIs, database, real data)
- Beautiful frontend design (Material Design 3 aesthetic)
- Simulation mode for development
- Production mode for live trading

Version: Unified Architecture
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, date, timedelta
import os
import sys
import json

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

# Import configuration
from config import TradingConfig as cfg

# Configuration
USE_SIMULATION = True  # Set to False when IBKR APIs are available

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# ============================================================================
# SIMULATION DATA GENERATORS (for development without IBKR)
# ============================================================================

def generate_simulated_live_metrics():
    """Generate realistic simulated data for Live Dashboard"""
    now = datetime.now()
    
    # Market session progress (9:31 AM to 4:00 PM)
    market_open = datetime.now().replace(hour=9, minute=31, second=0)
    market_close = datetime.now().replace(hour=16, minute=0, second=0)
    session_elapsed = (now - market_open).total_seconds()
    session_total = (market_close - market_open).total_seconds()
    session_progress = min(max(session_elapsed / session_total * 100, 0), 100)
    
    # Generate metrics
    opening_balance = 30000.00
    current_balance = 31247.89
    pl_today = current_balance - opening_balance
    roi_today = (pl_today / opening_balance) * 100
    
    trades_completed = 42
    wins = 29
    losses = 13
    win_rate = (wins / trades_completed) * 100 if trades_completed > 0 else 0
    
    # Forecast ranges
    forecast_pl_low = 768.00
    forecast_pl_high = 1392.00
    forecast_trades_low = 95
    forecast_trades_high = 120
    
    # Current drawdown (as positive percentage)
    current_drawdown_pct = 0.8  # 0.8% current drawdown
    
    # Helper function to create badge objects
    def create_badge(actual, low, high, metric_name):
        if actual > high:
            return {
                'status': 'above-target',
                'badge_class': 'above-target',
                'icon': 'check_circle',
                'text': 'Above Target',
                'actual': actual,
                'target_low': low,
                'target_high': high,
                'metric_name': metric_name
            }
        elif actual >= low:
            return {
                'status': 'on-pace',
                'badge_class': 'on-pace',
                'icon': 'schedule',
                'text': 'On Pace',
                'actual': actual,
                'target_low': low,
                'target_high': high,
                'metric_name': metric_name
            }
        else:
            return {
                'status': 'falling-behind',
                'badge_class': 'falling-behind',
                'icon': 'warning',
                'text': 'Falling Behind',
                'actual': actual,
                'target_low': low,
                'target_high': high,
                'metric_name': metric_name
            }
    
    # Calculate projected final trades based on session progress
    projected_trades = trades_completed / (session_progress / 100) if session_progress > 0 else trades_completed
    
    return {
        'timestamp': now.isoformat(),
        'market_time': now.strftime('%I:%M:%S %p ET'),
        'session_progress': session_progress,
        
        # Account metrics
        'opening_balance': opening_balance,
        'current_balance': current_balance,
        'pl_today': pl_today,
        'roi_today': roi_today,
        'deployed_capital': opening_balance * cfg.DEPLOYMENT_RATIO,
        
        # Trading activity
        'trades_completed': trades_completed,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'avg_entry_speed_min': 4.2,  # Average time from pattern to entry
        
        # Risk metrics
        'sharpe_ratio': 2.4,
        'sortino_ratio': 3.1,
        'max_drawdown_pct': -0.8,
        'current_drawdown_pct': current_drawdown_pct,  # Frontend expects this field
        'daily_loss_limit': abs(cfg.DAILY_LOSS_LIMIT),  # As positive number
        
        # Execution quality
        'avg_latency_ms': 8.0,
        'avg_slippage_pct': 0.10,
        'target_slippage_pct': 0.10,
        
        # Forecast comparison
        'forecast': {
            'pl_low': forecast_pl_low,
            'pl_high': forecast_pl_high,
            'trades_low': forecast_trades_low,
            'trades_high': forecast_trades_high,
            'win_rate_low': 65.0,
            'win_rate_high': 70.0
        },
        
        # Status badges (frontend expects this structure)
        'badges': {
            'balance': create_badge(
                current_balance,
                opening_balance + forecast_pl_low,
                opening_balance + forecast_pl_high,
                'Balance'
            ),
            'pl': create_badge(
                pl_today,
                forecast_pl_low,
                forecast_pl_high,
                'P&L'
            ),
            'trades': create_badge(
                projected_trades,  # Use projected final count
                forecast_trades_low,
                forecast_trades_high,
                'Trades'
            ),
            'win_rate': create_badge(
                win_rate,
                65.0,
                70.0,
                'Win Rate'
            ),
            'daily_loss_limit': create_badge(
                current_drawdown_pct,
                0,
                abs(cfg.DAILY_LOSS_LIMIT) * 0.7,  # Warning at 70% of limit
                'Daily Loss Limit'
            ),
            'avg_slippage': create_badge(
                0.10,
                0,
                0.12,  # Target slippage
                'Avg Slippage'
            ),
            'sharpe': create_badge(
                2.4,
                2.0,
                3.0,
                'Sharpe Ratio'
            ),
            'max_drawdown': create_badge(
                0.8,  # As positive number
                0,
                1.0,
                'Max Drawdown'
            )
        },
        
        # Stock performance (8 stocks)
        'stocks': [
            {
                'ticker': 'KO',
                'name': 'Coca-Cola',
                'classification': 'Conservative',
                'trades': 4,
                'win_rate': 75.0,
                'pl': 142.30,
                'roi': 4.7,
                'avg_hold_min': 3.8,
                'status': 'active'
            },
            {
                'ticker': 'PG',
                'name': 'Procter & Gamble',
                'classification': 'Conservative',
                'trades': 3,
                'win_rate': 67.0,
                'pl': 98.50,
                'roi': 3.3,
                'avg_hold_min': 4.1,
                'status': 'active'
            },
            {
                'ticker': 'MSFT',
                'name': 'Microsoft',
                'classification': 'Medium',
                'trades': 6,
                'win_rate': 83.0,
                'pl': 310.25,
                'roi': 10.3,
                'avg_hold_min': 3.2,
                'status': 'active'
            },
            {
                'ticker': 'AAPL',
                'name': 'Apple',
                'classification': 'Medium',
                'trades': 8,
                'win_rate': 62.0,
                'pl': 276.80,
                'roi': 9.2,
                'avg_hold_min': 4.5,
                'status': 'active'
            },
            {
                'ticker': 'GOOGL',
                'name': 'Alphabet',
                'classification': 'Medium',
                'trades': 5,
                'win_rate': 80.0,
                'pl': 185.60,
                'roi': 6.2,
                'avg_hold_min': 3.9,
                'status': 'active'
            },
            {
                'ticker': 'NVDA',
                'name': 'NVIDIA',
                'classification': 'Medium',
                'trades': 3,
                'win_rate': 67.0,
                'pl': 127.40,
                'roi': 4.2,
                'avg_hold_min': 5.1,
                'status': 'active'
            },
            {
                'ticker': 'AMZN',
                'name': 'Amazon',
                'classification': 'Aggressive',
                'trades': 7,
                'win_rate': 71.0,
                'pl': 162.30,
                'roi': 5.4,
                'avg_hold_min': 4.7,
                'status': 'active'
            },
            {
                'ticker': 'TSLA',
                'name': 'Tesla',
                'classification': 'Aggressive',
                'trades': 6,
                'win_rate': 67.0,
                'pl': 88.10,
                'roi': 2.9,
                'avg_hold_min': 5.8,
                'status': 'active'
            }
        ]
    }


def generate_simulated_morning_data():
    """Generate simulated morning report data"""
    return {
        'date': date.today().isoformat(),
        'generated_at': datetime.now().strftime('%I:%M:%S %p ET'),
        
        # Configuration
        'config': {
            'num_stocks': cfg.NUM_STOCKS,
            'deployment_ratio': cfg.DEPLOYMENT_RATIO,  # 0.8, not 80
            'entry_threshold': cfg.ENTRY_THRESHOLD,
            'target_1': cfg.TARGET_1,
            'target_2': cfg.TARGET_2,
            'stop_loss': cfg.STOP_LOSS,
            'daily_loss_limit': cfg.DAILY_LOSS_LIMIT
        },
        
        # Selected stocks with analysis
        'stocks': [
            {
                'ticker': 'KO',
                'name': 'Coca-Cola',
                'classification': 'Conservative',
                'patterns_found': 24,
                'confirmation_rate': 0.82,  # decimal, not percentage
                'win_rate': 0.72,  # decimal, not percentage
                'expected_entries_per_day': 3.2,  # corrected key
                'expected_daily_pl': 78.40,  # corrected key
                'avg_win': 0.0138,  # added missing field
                'quality_score': 88.5
            },
            {
                'ticker': 'PG',
                'name': 'Procter & Gamble',
                'classification': 'Conservative',
                'patterns_found': 19,
                'confirmation_rate': 0.79,
                'win_rate': 0.69,
                'expected_entries_per_day': 2.8,
                'expected_daily_pl': 65.20,
                'avg_win': 0.0125,
                'quality_score': 85.0
            },
            {
                'ticker': 'MSFT',
                'name': 'Microsoft',
                'classification': 'Medium',
                'patterns_found': 31,
                'confirmation_rate': 0.85,
                'win_rate': 0.75,
                'expected_entries_per_day': 4.1,
                'expected_daily_pl': 142.80,
                'avg_win': 0.0145,
                'quality_score': 92.0
            },
            {
                'ticker': 'AAPL',
                'name': 'Apple',
                'classification': 'Medium',
                'patterns_found': 38,
                'confirmation_rate': 0.83,
                'win_rate': 0.68,
                'expected_entries_per_day': 4.8,
                'expected_daily_pl': 168.30,
                'avg_win': 0.0142,
                'quality_score': 87.5
            },
            {
                'ticker': 'GOOGL',
                'name': 'Alphabet',
                'classification': 'Medium',
                'patterns_found': 27,
                'confirmation_rate': 0.81,
                'win_rate': 0.71,
                'expected_entries_per_day': 3.5,
                'expected_daily_pl': 98.60,
                'avg_win': 0.0135,
                'quality_score': 89.0
            },
            {
                'ticker': 'NVDA',
                'name': 'NVIDIA',
                'classification': 'Medium',
                'patterns_found': 22,
                'confirmation_rate': 0.77,
                'win_rate': 0.66,
                'expected_entries_per_day': 2.9,
                'expected_daily_pl': 82.40,
                'avg_win': 0.0128,
                'quality_score': 83.5
            },
            {
                'ticker': 'AMZN',
                'name': 'Amazon',
                'classification': 'Aggressive',
                'patterns_found': 34,
                'confirmation_rate': 0.79,
                'win_rate': 0.70,
                'expected_entries_per_day': 4.3,
                'expected_daily_pl': 125.70,
                'avg_win': 0.0148,
                'quality_score': 86.0
            },
            {
                'ticker': 'TSLA',
                'name': 'Tesla',
                'classification': 'Aggressive',
                'patterns_found': 41,
                'confirmation_rate': 0.76,
                'win_rate': 0.64,
                'expected_entries_per_day': 5.1,
                'expected_daily_pl': 142.10,
                'avg_win': 0.0152,
                'quality_score': 81.0
            }
        ],
        
        # Aggregate forecast (corrected key name)
        'forecast_summary': {
            'total_patterns': 236,
            'total_expected_trades_low': 95,  # added 'total_' prefix
            'total_expected_trades_high': 120,  # added 'total_' prefix
            'total_expected_pl_low': 768.00,  # added 'total_' prefix
            'total_expected_pl_high': 1392.00,  # added 'total_' prefix
            'expected_roi_low': 3.2,
            'expected_roi_high': 5.8,
            'expected_win_rate': 68.5
        },
        
        # Market conditions
        'market_conditions': {
            'volatility': 'Normal',
            'liquidity': 'Excellent',
            'spread_quality': 'Good',
            'confidence': 'High'
        }
    }


def generate_simulated_eod_data():
    """Generate simulated EOD report data"""
    return {
        'date': date.today().isoformat(),
        'generated_at': datetime.now().strftime('%I:%M:%S %p ET'),
        
        # Performance summary
        'summary': {
            'opening_balance': 30000.00,
            'closing_balance': 31247.89,
            'pl': 1247.89,
            'roi': 4.16,
            'trades': 98,
            'wins': 67,
            'losses': 31,
            'win_rate': 68.4
        },
        
        # Forecast accuracy
        'forecast_comparison': {
            'trades_forecast': '95-120',
            'trades_actual': 98,
            'trades_accuracy': 'On Target',
            'pl_forecast': '$768-$1,392',
            'pl_actual': 1247.89,
            'pl_accuracy': 'On Target',
            'win_rate_forecast': '65-70%',
            'win_rate_actual': 68.4,
            'win_rate_accuracy': 'On Target'
        },
        
        # Risk metrics
        'risk_metrics': {
            'sharpe_ratio': 2.4,
            'sortino_ratio': 3.1,
            'max_drawdown_pct': -1.2,
            'calmar_ratio': 2.5,
            'volatility': 0.8
        },
        
        # Execution quality
        'execution': {
            'avg_latency_ms': 8.2,
            'avg_slippage_pct': 0.11,
            'fills_within_target': 94.0,
            'avg_hold_time_min': 4.3
        },
        
        # Stock breakdown
        'stocks': [
            {
                'ticker': 'KO',
                'trades': 12,
                'win_rate': 75.0,
                'pl': 287.40,
                'roi': 9.6
            },
            {
                'ticker': 'PG',
                'trades': 9,
                'win_rate': 67.0,
                'pl': 198.30,
                'roi': 6.6
            },
            {
                'ticker': 'MSFT',
                'trades': 15,
                'win_rate': 80.0,
                'pl': 412.80,
                'roi': 13.8
            },
            {
                'ticker': 'AAPL',
                'trades': 18,
                'win_rate': 61.0,
                'pl': 356.70,
                'roi': 11.9
            },
            {
                'ticker': 'GOOGL',
                'trades': 11,
                'win_rate': 73.0,
                'pl': 265.40,
                'roi': 8.8
            },
            {
                'ticker': 'NVDA',
                'trades': 8,
                'win_rate': 63.0,
                'pl': 178.20,
                'roi': 5.9
            },
            {
                'ticker': 'AMZN',
                'trades': 14,
                'win_rate': 71.0,
                'pl': 332.50,
                'roi': 11.1
            },
            {
                'ticker': 'TSLA',
                'trades': 11,
                'win_rate': 64.0,
                'pl': 216.49,
                'roi': 7.2
            }
        ],
        
        # Intraday equity curve (for chart)
        'equity_curve': {
            'timestamps': ['9:30', '10:00', '10:30', '11:00', '11:30', '12:00', 
                          '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00'],
            'balances': [30000, 30142, 30287, 30564, 30721, 30889, 31014, 
                        31156, 31289, 31402, 31567, 31734, 31892, 31248]
        }
    }


# ============================================================================
# REAL DATA FUNCTIONS (used when USE_SIMULATION = False)
# ============================================================================

def get_real_live_metrics():
    """Get real metrics from IBKR API and database"""
    from modules.live_monitor import LiveMonitor
    from modules.database import TradingDatabase
    from modules.metrics_calculator import MetricsCalculator
    
    db = TradingDatabase()
    monitor = LiveMonitor(use_simulation=False)
    metrics = MetricsCalculator()
    
    # Get current account data
    account_data = monitor.get_account_summary()
    
    # Get today's fills
    fills = db.get_fills_for_date(date.today())
    
    # Get today's forecast
    forecast = db.get_todays_forecast()
    
    # Calculate metrics
    live_metrics = metrics.calculate_live_metrics(
        account_data=account_data,
        fills=fills,
        forecast=forecast
    )
    
    return live_metrics


def get_real_morning_data():
    """Get real morning report from database"""
    from modules.database import TradingDatabase
    
    db = TradingDatabase()
    forecast = db.get_todays_forecast()
    
    if not forecast:
        return None
    
    return forecast


def get_real_eod_data():
    """Get real EOD report from database"""
    from modules.database import TradingDatabase
    
    db = TradingDatabase()
    summary = db.get_daily_summary(date.today())
    
    if not summary:
        return None
    
    return summary


# ============================================================================
# API ENDPOINTS (for AJAX updates)
# ============================================================================

@app.route('/api/live-data')
def api_live_data():
    """Live dashboard metrics - updates every 5 seconds"""
    try:
        if USE_SIMULATION:
            data = generate_simulated_live_metrics()
        else:
            data = get_real_live_metrics()
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/morning-data')
def api_morning_data():
    """Morning report data"""
    try:
        if USE_SIMULATION:
            data = generate_simulated_morning_data()
        else:
            data = get_real_morning_data()
        
        if not data:
            return jsonify({'error': 'No morning report available'}), 404
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/eod-data')
def api_eod_data():
    """EOD report data"""
    try:
        if USE_SIMULATION:
            data = generate_simulated_eod_data()
        else:
            data = get_real_eod_data()
        
        if not data:
            return jsonify({'error': 'No EOD report available'}), 404
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/system-status')
def api_system_status():
    """System health check"""
    return jsonify({
        'status': 'online',
        'mode': 'simulation' if USE_SIMULATION else 'production',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected',
        'ibkr_api': 'simulated' if USE_SIMULATION else 'connected'
    })


# ============================================================================
# PAGE ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/how-it-works')
def how_it_works():
    """How It Works page"""
    return render_template('how-it-works.html')


@app.route('/live')
def live():
    """Live Dashboard"""
    return render_template('live.html')


@app.route('/morning')
def morning():
    """Morning Report"""
    return render_template('morning.html')


@app.route('/eod')
def eod():
    """End of Day Report"""
    return render_template('eod.html')


@app.route('/performance')
def performance():
    """Performance Analysis"""
    return render_template('performance.html')


@app.route('/history')
def history():
    """Trading History"""
    return render_template('history.html')


@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')


@app.route('/api-credentials')
def api_credentials():
    """API & Credentials page"""
    return render_template('api.html')


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("THE LUGGAGE ROOM BOYS FUND - UNIFIED DASHBOARD")
    print("=" * 70)
    print(f"\nMode: {'SIMULATION' if USE_SIMULATION else 'PRODUCTION'}")
    print(f"Starting server on http://localhost:5000")
    print()
    print("Available pages:")
    print("  • Landing Page:    http://localhost:5000/")
    print("  • About:           http://localhost:5000/about")
    print("  • How It Works:    http://localhost:5000/how-it-works")
    print("  • Live Dashboard:  http://localhost:5000/live")
    print("  • Morning Report:  http://localhost:5000/morning")
    print("  • EOD Report:      http://localhost:5000/eod")
    print("  • Performance:     http://localhost:5000/performance")
    print("  • History:         http://localhost:5000/history")
    print("  • Settings:        http://localhost:5000/settings")
    print("  • API Credentials: http://localhost:5000/api-credentials")
    print()
    print("API endpoints:")
    print("  • http://localhost:5000/api/live-data")
    print("  • http://localhost:5000/api/morning-data")
    print("  • http://localhost:5000/api/eod-data")
    print("  • http://localhost:5000/api/system-status")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
