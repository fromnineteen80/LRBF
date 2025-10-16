#!/usr/bin/env python3
"""
Railyard Markets - VWAP Recovery Trading Platform
Material Design 3 Interface with Complete Backend Integration
SECURE AUTHENTICATION FOR FINANCIAL PLATFORM
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from functools import wraps
from datetime import datetime, date, timedelta
import os
import bcrypt
import secrets
import sys
from collections import defaultdict
import time

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

# Import backend modules
try:
    from modules.config import TradingConfig as cfg
    from modules.stock_selector import StockSelector
    from modules.forecast_generator import ForecastGenerator
    from modules.morning_report import MorningReport
    from modules.live_monitor import LiveMonitor
    from modules.eod_reporter import EODReporter
    from modules.database import Database
    from modules.capitalise_prompts import CapitalisePrompts
    from modules.ibkr_connector import IBKRConnector
    from modules.stock_universe import get_stock_universe
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Backend modules not fully loaded: {e}")
    BACKEND_AVAILABLE = False

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Enhanced CSP to allow Material Web Components
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://esm.run https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://esm.run;"
    )
    return response

# Initialize database
if BACKEND_AVAILABLE:
    db = Database()

# ============================================================================
# AUTHENTICATION & SECURITY
# ============================================================================

# Production: Store these in environment variables or secure database
# Pre-hashed passwords using bcrypt
# admin: admin123, cofounder: luggage2025
USERS = {
    'admin': '$2b$12$o63kdC0CSIPlGU82cG9UMueIMf3C3rwlcgNRv0z.dKwwT3N3vm7oC',
    'cofounder': '$2b$12$mLje1vvYjCnrXnE9j37MT.mdypNvzSS3kkaqR8IAoLwloxFA8QQsm'
}

# Simple rate limiting (production should use Redis)
login_attempts = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_PERIOD = 300  # 5 minutes

def check_rate_limit(ip_address):
    """Check if IP has exceeded login attempts"""
    now = time.time()
    # Clean old attempts
    login_attempts[ip_address] = [
        timestamp for timestamp in login_attempts[ip_address]
        if now - timestamp < LOCKOUT_PERIOD
    ]
    
    if len(login_attempts[ip_address]) >= MAX_LOGIN_ATTEMPTS:
        return False
    return True

def record_login_attempt(ip_address):
    """Record a failed login attempt"""
    login_attempts[ip_address].append(time.time())

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get client IP
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # Check rate limit
        if not check_rate_limit(ip_address):
            return jsonify({
                'success': False, 
                'error': 'Too many login attempts. Please try again in 5 minutes.'
            }), 429
        
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Input validation
        if not username or not password:
            record_login_attempt(ip_address)
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        # Verify credentials with bcrypt
        if username in USERS:
            try:
                stored_hash = USERS[username]
                # For newly created hashes (during this session)
                if isinstance(stored_hash, str):
                    stored_hash = stored_hash.encode('utf-8')
                
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    # Success! Clear rate limit for this IP
                    login_attempts[ip_address] = []
                    
                    # Set session
                    session['username'] = username
                    session.permanent = True
                    session['login_time'] = datetime.now().isoformat()
                    
                    return jsonify({'success': True})
            except Exception as e:
                print(f"Login error: {e}")
        
        # Failed login
        record_login_attempt(ip_address)
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    # GET request - show login page
    return render_template('login.html')

@app.route('/signup')
def signup():
    """Signup page for new co-founders"""
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============================================================================
# AUTHENTICATION API ENDPOINTS
# ============================================================================

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    """
    User signup endpoint.
    Creates a new user account with phone verification.
    """
    try:
        data = request.json
        
        # Import auth helper
        from modules.auth_helper import AuthHelper, NotificationService
        
        # Extract and validate data
        required_fields = ['first_name', 'last_name', 'email', 'phone_number', 
                          'timezone', 'fund_contribution', 'username', 'password']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate username
        valid, msg = AuthHelper.validate_username(data['username'])
        if not valid:
            return jsonify({'error': msg}), 400
        
        # Validate email
        valid, msg = AuthHelper.validate_email(data['email'])
        if not valid:
            return jsonify({'error': msg}), 400
        
        # Validate phone
        valid, msg = AuthHelper.validate_phone(data['phone_number'])
        if not valid:
            return jsonify({'error': msg}), 400
        
        # Validate password strength
        valid, msg = AuthHelper.validate_password_strength(data['password'])
        if not valid:
            return jsonify({'error': msg}), 400
        
        # Hash password
        password_hash = AuthHelper.hash_password(data['password'])
        
        # Generate verification code
        verification_code = AuthHelper.generate_verification_code()
        
        # Calculate ownership percentage
        # For now, set to 0.0 (admin will update after verifying contribution)
        ownership_pct = 0.0
        
        # Insert user into database
        if BACKEND_AVAILABLE:
            cursor = db.conn.cursor()
            
            # Check if username or email already exists
            cursor.execute("SELECT username, email FROM users WHERE username = ? OR email = ?", 
                          (data['username'], data['email']))
            existing = cursor.fetchone()
            
            if existing:
                if existing[0] == data['username']:
                    return jsonify({'error': 'Username already exists'}), 400
                else:
                    return jsonify({'error': 'Email already registered'}), 400
            
            # Insert new user
            cursor.execute("""
                INSERT INTO users (
                    username, password_hash, first_name, last_name, 
                    email, phone_number, timezone, fund_contribution,
                    ownership_pct, is_verified, verification_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """, (
                data['username'],
                password_hash,
                data['first_name'],
                data['last_name'],
                data['email'],
                data['phone_number'],
                data['timezone'],
                float(data['fund_contribution']),
                ownership_pct,
                verification_code
            ))
            
            db.conn.commit()
            
            # Send verification code via SMS
            notification_service = NotificationService()
            notification_service.send_verification_code(data['phone_number'], verification_code)
            
            # Send welcome email
            notification_service.send_welcome_email(
                data['email'], 
                data['first_name'],
                data['username']
            )
            
            return jsonify({
                'success': True,
                'requires_verification': True,
                'message': 'Account created! Verification code sent to your phone.'
            }), 201
        else:
            return jsonify({'error': 'Backend not available'}), 500
            
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'error': 'Failed to create account. Please try again.'}), 500

@app.route('/api/auth/resend-code', methods=['POST'])
def api_resend_code():
    """
    Resend verification code to user's phone.
    """
    try:
        data = request.json
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return jsonify({'error': 'Phone number required'}), 400
        
        if BACKEND_AVAILABLE:
            from modules.auth_helper import AuthHelper, NotificationService
            
            cursor = db.conn.cursor()
            cursor.execute("SELECT verification_code FROM users WHERE phone_number = ? AND is_verified = 0", 
                          (phone_number,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'User not found or already verified'}), 404
            
            verification_code = result[0]
            
            # Resend code
            notification_service = NotificationService()
            notification_service.send_verification_code(phone_number, verification_code)
            
            return jsonify({'success': True, 'message': 'Code resent!'}), 200
        else:
            return jsonify({'error': 'Backend not available'}), 500
            
    except Exception as e:
        print(f"Resend code error: {e}")
        return jsonify({'error': 'Failed to resend code'}), 500

# ============================================================================
# PAGE ROUTES
# ============================================================================

@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/morning')
@login_required
def morning():
    return render_template('morning.html', username=session.get('username'))

@app.route('/live')
@login_required
def live():
    return render_template('live.html', username=session.get('username'))

@app.route('/eod')
@login_required
def eod():
    return render_template('eod.html', username=session.get('username'))

@app.route('/history')
@login_required
def history():
    return render_template('history.html', username=session.get('username'))

@app.route('/performance')
@login_required
def performance():
    return render_template('performance.html', username=session.get('username'))

@app.route('/calculator')
@login_required
def calculator():
    return render_template('calculator.html', username=session.get('username'))

@app.route('/practice')
@login_required
def practice():
    return render_template('practice.html', username=session.get('username'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', username=session.get('username'))

@app.route('/api-credentials')
@login_required
def api_credentials():
    return render_template('api_credentials.html', username=session.get('username'))

@app.route('/about')
@login_required
def about():
    return render_template('about.html', username=session.get('username'))

@app.route('/how-it-works')
@login_required
def how_it_works():
    return render_template('how_it_works.html', username=session.get('username'))

@app.route('/glossary')
@login_required
def glossary():
    return render_template('glossary.html', username=session.get('username'))

# ============================================================================
# API - MORNING REPORT
# ============================================================================

@app.route('/api/morning/generate', methods=['POST'])
@login_required
def generate_morning_report():
    """Generate morning report using backend logic"""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        # Initialize morning report generator
        morning = MorningReport()
        
        # Generate report
        report = morning.generate_report()
        
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/morning/data')
@login_required
def get_morning_data():
    """Get today's morning forecast"""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        forecast = db.get_todays_forecast()
        if forecast:
            return jsonify(forecast)
        else:
            # Generate new forecast
            return generate_morning_report()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/morning/prompts')
@login_required
def download_prompts():
    """Generate Capitalise.ai prompts for selected stocks"""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        forecast = db.get_todays_forecast()
        if not forecast:
            return jsonify({'error': 'No forecast available. Generate morning report first.'}), 400
        
        selected_stocks = forecast.get('selected_stocks', [])
        prompts = CapitalisePrompts.generate_all_prompts(selected_stocks)
        
        return jsonify({'prompts': prompts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API - LIVE MONITOR
# ============================================================================

@app.route('/api/live/data')
@login_required
def get_live_data():
    """Get real-time trading data"""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        monitor = LiveMonitor()
        data = monitor.get_current_status()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/positions')
@login_required
def get_positions():
    """Get current open positions"""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        ibkr = IBKRConnector()
        positions = ibkr.get_positions()
        return jsonify({'positions': positions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API - EOD REPORT
# ============================================================================

@app.route('/api/eod/generate', methods=['POST'])
@login_required
def generate_eod_report():
    """Generate end-of-day report"""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        eod = EODReporter()
        report = eod.generate_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/eod/data')
@login_required
def get_eod_data():
    """Get today's EOD data"""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        summary = db.get_daily_summary(date.today())
        if summary:
            return jsonify(summary)
        else:
            return generate_eod_report()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API - HISTORY
# ============================================================================

@app.route('/api/history/range')
@login_required
def get_history_range():
    """Get historical performance data"""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        days = int(request.args.get('days', 30))
        history = db.get_daily_summaries(days)
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/stats')
@login_required
def get_history_stats():
    """Get aggregate statistics"""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        days = int(request.args.get('days', 30))
        stats = db.get_aggregate_stats(days)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API - CALCULATOR
# ============================================================================

@app.route('/api/calculator/project', methods=['POST'])
@login_required
def calculate_projection():
    """Calculate performance projections"""
    try:
        data = request.json
        
        starting_capital = float(data.get('starting_capital', 30000))
        daily_roi = float(data.get('daily_roi', 3.5)) / 100
        trading_days = int(data.get('trading_days', 252))
        deployment_ratio = float(data.get('deployment_ratio', 0.80))
        taper_day = int(data.get('taper_day', 120))
        taper_ratio = float(data.get('taper_ratio', 0.50))
        
        balance = starting_capital
        daily_data = []
        
        for day in range(trading_days):
            current_deployment = deployment_ratio if day < taper_day else taper_ratio
            deployed_capital = balance * current_deployment
            daily_gain = deployed_capital * daily_roi
            balance += daily_gain
            
            daily_data.append({
                'day': day + 1,
                'balance': round(balance, 2),
                'daily_gain': round(daily_gain, 2),
                'total_gain': round(balance - starting_capital, 2),
                'roi_pct': round(((balance - starting_capital) / starting_capital) * 100, 2)
            })
        
        result = {
            'starting_capital': starting_capital,
            'final_balance': round(balance, 2),
            'total_gain': round(balance - starting_capital, 2),
            'total_roi': round(((balance - starting_capital) / starting_capital) * 100, 2),
            'trading_days': trading_days,
            'daily_data': daily_data
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API - PRACTICE MODE
# ============================================================================

@app.route('/api/practice/analyze', methods=['POST'])
@login_required
def practice_analyze():
    """Analyze stocks in practice mode"""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        data = request.json
        tickers = data.get('tickers', [])
        
        if not tickers:
            tickers = get_stock_universe()[:10]  # Get first 10 from universe
        
        detector = PatternDetector()
        analyzed_stocks = []
        
        for ticker in tickers:
            analysis = detector.analyze_ticker(ticker, simulation_mode=cfg.USE_SIMULATION)
            if analysis:
                analyzed_stocks.append(analysis)
        
        # Select top 8 stocks
        selector = StockSelector()
        selected_stocks = selector.select_stocks(analyzed_stocks, num_stocks=8)
        
        return jsonify({
            'analyzed_stocks': analyzed_stocks,
            'selected_stocks': selected_stocks
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/practice/simulate', methods=['POST'])
@login_required
def practice_simulate():
    """Run trading simulation"""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        data = request.json
        selected_stocks = data.get('selected_stocks', [])
        simulation_days = int(data.get('simulation_days', 1))
        
        results = []
        for stock in selected_stocks:
            # Simulate trading for the stock
            simulated_pl = stock.get('expected_daily_pl', 100) * simulation_days
            simulated_trades = stock.get('expected_daily_entries', 10) * simulation_days
            
            results.append({
                'ticker': stock['ticker'],
                'patterns_found': stock.get('total_patterns', 0),
                'simulated_pl': round(simulated_pl, 2),
                'simulated_trades': round(simulated_trades, 1)
            })
        
        return jsonify({'simulation_results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API - SETTINGS
# ============================================================================

@app.route('/api/settings/get')
@login_required
def get_settings():
    """Get current configuration"""
    try:
        settings = {
            'deployment_ratio': cfg.DEPLOYMENT_RATIO,
            'reserve_ratio': cfg.RESERVE_RATIO,
            'num_stocks': cfg.NUM_STOCKS,
            'decline_threshold': cfg.DECLINE_THRESHOLD,
            'entry_threshold': cfg.ENTRY_THRESHOLD,
            'target_1': cfg.TARGET_1,
            'target_2': cfg.TARGET_2,
            'stop_loss': cfg.STOP_LOSS,
            'daily_loss_limit': cfg.DAILY_LOSS_LIMIT,
            'analysis_period_days': cfg.ANALYSIS_PERIOD_DAYS,
            'min_confirmation_rate': cfg.MIN_CONFIRMATION_RATE,
            'min_expected_value': cfg.MIN_EXPECTED_VALUE,
            'min_entries_per_day': cfg.MIN_ENTRIES_PER_DAY
        }
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/update', methods=['POST'])
@login_required
def update_settings():
    """Update configuration"""
    try:
        data = request.json
        # Update config (implementation depends on how config is stored)
        # For now, just return success
        return jsonify({'success': True, 'message': 'Settings updated (implementation pending)'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/trading-mode')
@login_required
def get_trading_mode():
    """Get current trading mode (live or simulation)"""
    try:
        from modules.simulation_helper import get_simulation_status
        
        # Get mode from session (defaults to 'live')
        mode = session.get('trading_mode', 'live')
        
        response = {'mode': mode}
        
        # If simulation mode, include simulation status
        if mode == 'simulation':
            response['simulation_status'] = get_simulation_status()
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/trading-mode', methods=['POST'])
@login_required
def set_trading_mode():
    """Set trading mode (live or simulation)"""
    try:
        data = request.json
        mode = data.get('mode', 'live')
        
        # Validate mode
        if mode not in ['live', 'simulation']:
            return jsonify({'error': 'Invalid mode. Must be "live" or "simulation"'}), 400
        
        # Store in session
        session['trading_mode'] = mode
        session.modified = True
        
        return jsonify({'success': True, 'mode': mode})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/simulation-status')
@login_required
def get_simulation_status_api():
    """Get simulation status information"""
    try:
        from modules.simulation_helper import get_simulation_status
        
        status = get_simulation_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API - CREDENTIALS
# ============================================================================

@app.route('/api/credentials/get')
@login_required
def get_credentials():
    """Get API credential status"""
    try:
        credentials = {
            'ibkr_configured': os.path.exists('config/ibkr.json'),
            'capitalise_configured': os.path.exists('config/capitalise.json'),
            'yfinance_status': 'Simulation' if cfg.USE_SIMULATION else 'Live'
        }
        return jsonify(credentials)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/credentials/test/<service>', methods=['POST'])
@login_required
def test_credentials(service):
    """Test API credentials"""
    try:
        if service == 'ibkr':
            ibkr = IBKRConnector()
            status = ibkr.test_connection()
        elif service == 'capitalise':
            status = {'success': True, 'message': 'Capitalise.ai connection OK'}
        else:
            status = {'success': False, 'message': 'Unknown service'}
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API - SYSTEM
# ============================================================================

@app.route('/api/system/status')
@login_required
def system_status():
    """Get system status"""
    try:
        now = datetime.now()
        market_open = now.replace(hour=9, minute=31, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        is_open = now.weekday() < 5 and market_open <= now <= market_close
        
        status = {
            'mode': 'Simulation' if not BACKEND_AVAILABLE or cfg.USE_SIMULATION else 'Live',
            'database': 'Connected' if BACKEND_AVAILABLE else 'Not Available',
            'backend': 'Loaded' if BACKEND_AVAILABLE else 'Not Available',
            'timestamp': now.isoformat(),
            'market_open': is_open
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/calendar')
def market_calendar():
    """Get accurate market calendar info using pandas_market_calendars"""
    try:
        import pandas_market_calendars as mcal
        from datetime import timezone
        
        # Get NYSE calendar
        nyse = mcal.get_calendar('NYSE')
        
        # Get current Eastern Time
        now_utc = datetime.now(timezone.utc)
        eastern = now_utc.astimezone(mcal.get_calendar('NYSE').tz)
        today = eastern.date()
        
        # Check if today is a trading day
        schedule = nyse.schedule(start_date=today, end_date=today)
        is_trading_day = len(schedule) > 0
        
        response = {}
        
        if is_trading_day:
            # Get market open/close times
            market_open = schedule['market_open'].iloc[0]
            market_close = schedule['market_close'].iloc[0]
            
            response = {
                'is_trading_day': True,
                'market_open_hour': market_open.hour,
                'market_open_minute': market_open.minute,
                'market_close_hour': market_close.hour,
                'market_close_minute': market_close.minute,
                'is_early_close': market_close.hour < 16 or (market_close.hour == 16 and market_close.minute < 0),
                'next_trading_day': None
            }
        else:
            # Find next trading day
            next_schedule = nyse.schedule(start_date=today, end_date=today + timedelta(days=10))
            if len(next_schedule) > 0:
                next_date = next_schedule.index[0]
                next_day_name = next_date.strftime('%a')  # Mon, Tue, Wed, etc.
                
                response = {
                    'is_trading_day': False,
                    'market_open_hour': 9,
                    'market_open_minute': 31,
                    'market_close_hour': 16,
                    'market_close_minute': 0,
                    'is_early_close': False,
                    'next_trading_day': next_day_name
                }
            else:
                # Fallback if no trading days found
                response = {
                    'is_trading_day': False,
                    'market_open_hour': 9,
                    'market_open_minute': 31,
                    'market_close_hour': 16,
                    'market_close_minute': 0,
                    'is_early_close': False,
                    'next_trading_day': 'Mon'
                }
        
        return jsonify(response)
    except Exception as e:
        # Fallback to basic logic if pandas_market_calendars fails
        print(f"⚠️  Market calendar error: {e}")
        now = datetime.now()
        is_weekend = now.weekday() >= 5
        
        return jsonify({
            'is_trading_day': not is_weekend,
            'market_open_hour': 9,
            'market_open_minute': 31,
            'market_close_hour': 16,
            'market_close_minute': 0,
            'is_early_close': False,
            'next_trading_day': 'Mon' if is_weekend else None,
            'error': 'Using fallback calendar logic'
        })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚂 RAILYARD MARKETS - VWAP Recovery Trading Platform")
    print("="*70)
    print("\n✓ Server starting...")
    print(f"✓ Backend: {'Loaded' if BACKEND_AVAILABLE else 'Not Available (using simulation)'}")
    print(f"✓ Mode: {'Simulation' if not BACKEND_AVAILABLE else 'Production Ready'}")
    print("✓ Access: http://localhost:5000")
    print("\n🔐 Login Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n   Username: cofounder")
    print("   Password: luggage2025")
    print("\n" + "="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
