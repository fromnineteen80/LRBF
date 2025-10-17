#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railyard Markets - VWAP Recovery Trading Platform
Material Design 3 Interface with Complete Backend Integration
SECURE AUTHENTICATION FOR FINANCIAL PLATFORM
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
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
    from modules import stock_selector
    from modules import forecast_generator
    from modules import morning_report
    from modules import live_monitor
    from modules import eod_reporter
    from modules.database import Database
    from modules import capitalise_prompts
    from modules import ibkr_connector
    from modules.stock_universe import get_stock_universe
    from modules.auth_helper import AuthHelper
    from modules.email_service import EmailService
    from modules.sms_service import SMSService
    from modules.scheduler import scheduler
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¯ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¸ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  Backend modules not fully loaded: {e}")
    BACKEND_AVAILABLE = False

app = Flask(__name__)
# Development: Use fixed key so sessions persist across Flask reloads
# Production: Use environment variable
app.secret_key = os.environ.get('SECRET_KEY', 'dev-railyard-secret-key-DO-NOT-USE-IN-PRODUCTION')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Initialize scheduler for automatic morning report generation
if BACKEND_AVAILABLE:
    try:
        scheduler.init_app(app)
        scheduler.start()
        print("ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ Morning report scheduler started - generates at 12:01 AM EST")
    except Exception as e:
        print(f"ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¯ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¸ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  Scheduler failed to start: {e}")

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
    email_service = EmailService()
    sms_service = SMSService()

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
        session.permanent = True  # Refresh session on every request
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        
        # Check if user has admin role
        if session.get('role') != 'admin':
            # For API routes, return JSON error
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Access denied. Admin privileges required.'
                }), 403
            
            # For page routes, redirect to dashboard with error message
            flash('Access denied. This page requires administrator privileges.', 'error')
            return redirect(url_for('dashboard'))
        
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
        # First check hardcoded users (for backwards compatibility)
        if username in USERS:
            try:
                stored_hash = USERS[username]
                # For newly created hashes (during this session)
                if isinstance(stored_hash, str):
                    stored_hash = stored_hash.encode('utf-8')
                
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    # Success! Clear rate limit for this IP
                    login_attempts[ip_address] = []
                    
                    # Set session (hardcoded users are treated as admin)
                    session['username'] = username
                    session['role'] = 'admin'
                    session['first_name'] = username  # Use username as first_name for hardcoded users
                    session['full_name'] = username
                    session['profile_image'] = None  # No profile image for hardcoded users
                    session.permanent = True
                    session['login_time'] = datetime.now().isoformat()
                    
                    return jsonify({'success': True})
            except Exception as e:
                print(f"Login error (hardcoded users): {e}")
        
        # Check database users
        if BACKEND_AVAILABLE:
            try:
                user = db.get_user_by_username(username)
                
                if user:
                    # Check if user is active
                    if not user.get('is_active', False):
                        record_login_attempt(ip_address)
                        return jsonify({'success': False, 'error': 'Account is inactive'}), 401
                    
                    # Verify password
                    stored_hash = user['password_hash']
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                        # Check if user is verified
                        if not user.get('is_verified', False):
                            record_login_attempt(ip_address)
                            return jsonify({
                                'success': False, 
                                'error': 'Please verify your phone number before logging in',
                                'requires_verification': True
                            }), 403
                        
                        # Success! Clear rate limit for this IP
                        login_attempts[ip_address] = []
                        
                        # Update last login
                        db.update_last_login(user['id'])
                        
                        # Set session with user ID, username, role, first_name, and profile_image
                        session['user_id'] = user['id']
                        session['username'] = username
                        session['role'] = user.get('role', 'member')
                        session['first_name'] = user.get('first_name', username)
                        session['full_name'] = user.get('full_name') or user.get('first_name', username)
                        session['profile_image'] = user.get('profile_image')
                        session.permanent = True
                        session['login_time'] = datetime.now().isoformat()
                        
                        return jsonify({'success': True})
            except Exception as e:
                print(f"Login error (database): {e}")
        
        # Failed login
        record_login_attempt(ip_address)
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    # GET request - show login page
    return render_template('login.html')

@app.route('/signup')
def signup():
    """
    Signup page for new co-founders (invitation-only).
    Requires valid invitation token in query parameter.
    """
    # Get invitation token from query parameter
    invite_token = request.args.get('invite', '').strip()
    
    if not invite_token:
        # No invitation token provided
        return render_template('signup.html', error='Invitation required. Please use the invitation link sent to your email.')
    
    # Validate invitation token
    if BACKEND_AVAILABLE:
        invitation = db.get_invitation_by_token(invite_token)
        
        if not invitation:
            return render_template('signup.html', error='Invalid invitation token. Please check your invitation link.')
        
        # Check if invitation is valid (not expired, not used)
        is_valid, error_msg = AuthHelper.validate_invitation_token(
            token=invite_token,
            expires_at=invitation['expires_at'],
            used=invitation['used']
        )
        
        if not is_valid:
            return render_template('signup.html', error=error_msg)
        
        # Pass invitation data to template for pre-filling
        return render_template('signup.html', 
                             invite_token=invite_token,
                             email=invitation['email'],
                             first_name=invitation['first_name'] or '')
    else:
        return render_template('signup.html', error='System temporarily unavailable. Please try again later.')

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
    User signup endpoint with invitation-only access.
    Creates a new user account with phone verification.
    Requires valid invitation token.
    """
    try:
        data = request.json
        
        # CRITICAL: Require invitation token for signup
        invite_token = data.get('invite_token', '').strip()
        if not invite_token:
            return jsonify({'error': 'Invitation token required'}), 400
        
        # Validate invitation
        if BACKEND_AVAILABLE:
            invitation = db.get_invitation_by_token(invite_token)
            
            if not invitation:
                return jsonify({'error': 'Invalid invitation token'}), 400
            
            # Check if invitation is valid
            is_valid, error_msg = AuthHelper.validate_invitation_token(
                token=invite_token,
                expires_at=invitation['expires_at'],
                used=invitation['used']
            )
            
            if not is_valid:
                return jsonify({'error': error_msg}), 400
            
            # Email must match invitation
            if data.get('email', '').strip().lower() != invitation['email'].lower():
                return jsonify({'error': 'Email does not match invitation'}), 400
        else:
            return jsonify({'error': 'Backend not available'}), 503
        
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
        valid, msg = AuthHelper.validate_phone_number(data['phone_number'])
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
            
            # Get the new user's ID
            user_id = cursor.lastrowid
            
            # Mark invitation as used
            db.mark_invitation_used(invite_token, user_id)
            
            # Update user's invited_by field
            cursor.execute("""
                UPDATE users SET invited_by = (
                    SELECT invited_by FROM invitations WHERE invite_token = ?
                ) WHERE id = ?
            """, (invite_token, user_id))
            db.conn.commit()
            
            # Send verification code via SMS
            sms_service.send_verification_code(data['phone_number'], verification_code)
            
            # Send welcome email
            email_service.send_welcome_email(
                to_email=data['email'], 
                first_name=data['first_name']
            )
            
            # Send welcome SMS
            sms_service.send_welcome_sms(
                to_phone=data['phone_number'],
                first_name=data['first_name']
            )
            
            # Notify admin who sent the invitation
            invited_by_id = invitation['invited_by']
            admin_user = db.get_user_by_id(invited_by_id)
            if admin_user and admin_user.get('phone_number'):
                sms_service.send_new_cofounder_alert(
                    to_phone=admin_user['phone_number'],
                    new_cofounder_name=f"{data['first_name']} {data['last_name']}"
                )
            
            # Log audit event
            import json
            db.log_audit_event(
                user_id=user_id,
                action='user_joined',
                details=json.dumps({
                    'invited_by': invited_by_id,
                    'email': data['email'],
                    'username': data['username']
                }),
                ip_address=request.remote_addr
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

@app.route('/api/auth/verify-phone', methods=['POST'])
def api_verify_phone():
    """
    Verify phone number with 6-digit code.
    Marks user as verified in database after successful verification.
    """
    try:
        data = request.json
        phone_number = data.get('phone_number')
        code = data.get('code')
        
        if not phone_number or not code:
            return jsonify({'error': 'Phone number and code required'}), 400
        
        if BACKEND_AVAILABLE:
            from modules.auth_helper import NotificationService
            
            cursor = db.conn.cursor()
            
            # Get user by phone number
            cursor.execute("""
                SELECT id, verification_code, first_name, email, username 
                FROM users 
                WHERE phone_number = ? AND is_verified = 0
            """, (phone_number,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'User not found or already verified'}), 404
            
            user_id, stored_code, first_name, email, username = result
            
            # Verify code matches
            if stored_code != code:
                return jsonify({'error': 'Invalid verification code'}), 400
            
            # Mark user as verified
            db.verify_user(user_id)
            
            # Send welcome email
            notification_service = NotificationService()
            notification_service.send_welcome_email(email, first_name, username)
            
            return jsonify({
                'success': True,
                'message': 'Phone verified! You can now log in.'
            }), 200
        else:
            return jsonify({'error': 'Backend not available'}), 500
            
    except Exception as e:
        print(f"Verify phone error: {e}")
        return jsonify({'error': 'Failed to verify phone'}), 500

@app.route('/api/auth/update-profile', methods=['POST'])
@login_required
def api_update_profile():
    """
    Update user profile information.
    Handles: first_name, last_name, email, phone_number, timezone, fund_contribution.
    Auto-recalculates ownership percentages if fund_contribution changes.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.json
        user_id = session['user_id']
        
        # Validate allowed fields
        allowed_fields = ['first_name', 'last_name', 'email', 'phone_number', 'timezone', 'fund_contribution']
        updates = {}
        
        for field in allowed_fields:
            if field in data:
                value = data[field]
                
                # Validate email if provided
                if field == 'email' and value:
                    from modules.auth_helper import AuthHelper
                    valid, msg = AuthHelper.validate_email(value)
                    if not valid:
                        return jsonify({'error': msg}), 400
                    
                    # Check if email already exists (for different user)
                    cursor = db.conn.cursor()
                    cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (value, user_id))
                    if cursor.fetchone():
                        return jsonify({'error': 'Email already in use'}), 400
                
                # Validate phone if provided
                if field == 'phone_number' and value:
                    from modules.auth_helper import AuthHelper
                    valid, msg = AuthHelper.validate_phone(value)
                    if not valid:
                        return jsonify({'error': msg}), 400
                    
                    # Check if phone already exists (for different user)
                    cursor = db.conn.cursor()
                    cursor.execute("SELECT id FROM users WHERE phone_number = ? AND id != ?", (value, user_id))
                    if cursor.fetchone():
                        return jsonify({'error': 'Phone number already in use'}), 400
                
                # Validate fund contribution
                if field == 'fund_contribution':
                    try:
                        value = float(value)
                        if value < 0:
                            return jsonify({'error': 'Fund contribution cannot be negative'}), 400
                    except ValueError:
                        return jsonify({'error': 'Invalid fund contribution amount'}), 400
                
                updates[field] = value
        
        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update profile
        success = db.update_user_profile(user_id, updates)
        
        if success:
            # If fund_contribution changed, notify other co-founders
            if 'fund_contribution' in updates:
                from modules.auth_helper import NotificationService
                notification_service = NotificationService()
                
                # Get updated user info
                user = db.get_user_by_id(user_id)
                
                # Get all other active co-founders
                all_users = db.get_all_users()
                other_users = [u for u in all_users if u['id'] != user_id]
                
                # Send notification emails to other co-founders
                for other_user in other_users:
                    notification_service.send_contribution_change_notification(
                        other_user['email'],
                        other_user['first_name'],
                        user['first_name'],
                        user['last_name'],
                        updates['fund_contribution'],
                        other_user['ownership_pct']
                    )
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to update profile'}), 500
            
    except Exception as e:
        print(f"Update profile error: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@app.route('/api/auth/change-password', methods=['POST'])
@login_required
def api_change_password():
    """
    Change user password.
    Requires current password verification before setting new password.
    Optionally invalidates all existing sessions for security.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords required'}), 400
        
        from modules.auth_helper import AuthHelper
        
        user_id = session['user_id']
        
        # Get user to verify current password
        user = db.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        if not AuthHelper.verify_password(current_password, user['password_hash']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password strength
        valid, msg = AuthHelper.validate_password_strength(new_password)
        if not valid:
            return jsonify({'error': msg}), 400
        
        # Hash new password
        new_password_hash = AuthHelper.hash_password(new_password)
        
        # Update password in database
        success = db.update_password(user_id, new_password_hash)
        
        if success:
            # Optional: Invalidate all existing sessions except current one
            # (Enhanced security - user must log in again on other devices)
            # Uncomment below to enable:
            # cursor = db.conn.cursor()
            # cursor.execute("DELETE FROM sessions WHERE user_id = ? AND session_token != ?", 
            #                (user_id, session.get('session_token')))
            # db.conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Password changed successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to change password'}), 500
            
    except Exception as e:
        print(f"Change password error: {e}")
        return jsonify({'error': 'Failed to change password'}), 500

@app.route('/delete-account')
@login_required
def delete_account_page():
    """
    Render account deletion page with payout calculation.
    Shows current fund value, ownership percentage, and calculated payout amount.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return redirect(url_for('settings'))
        
        user_id = session['user_id']
        user = db.get_user_by_id(user_id)
        
        if not user:
            return redirect(url_for('settings'))
        
        # Get current fund value (from IBKR or last EOD balance)
        # Try to get from IBKR first
        try:
            ibkr = IBKRConnector()
            current_fund_value = ibkr.get_account_balance()
        except Exception as e:
            print(f"Could not get IBKR balance: {e}")
            # Fallback: Use total fund contributions as estimate
            current_fund_value = db.get_total_fund_value()
        
        # Calculate payout based on ownership percentage
        payout_amount = (user['ownership_pct'] / 100) * current_fund_value
        
        # Check if there's already a pending deletion request
        existing_request = db.get_deletion_request(user_id)
        
        return render_template(
            'delete_account.html',
            username=session.get('username'),
            user=user,
            current_fund_value=current_fund_value,
            payout_amount=payout_amount,
            pending_request=existing_request
        )
        
    except Exception as e:
        print(f"Delete account page error: {e}")
        return redirect(url_for('settings'))

@app.route('/api/auth/delete-account', methods=['POST'])
@login_required
def api_delete_account():
    """
    Handle account deletion request.
    Creates deletion request in database with payout calculation.
    Sends notifications to all co-founders about account deletion.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        user = db.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user has confirmed (from request)
        data = request.json
        confirmed = data.get('confirmed', False)
        
        if not confirmed:
            return jsonify({'error': 'Must confirm account deletion'}), 400
        
        # Get current fund value
        try:
            ibkr = IBKRConnector()
            current_fund_value = ibkr.get_account_balance()
        except Exception as e:
            print(f"Could not get IBKR balance: {e}")
            current_fund_value = db.get_total_fund_value()
        
        # Calculate payout
        payout_amount = (user['ownership_pct'] / 100) * current_fund_value
        
        # Create deletion request
        notes = f"User {user['username']} requested account deletion. Payout: ${payout_amount:,.2f}"
        request_id = db.create_deletion_request(user_id, current_fund_value, payout_amount, notes)
        
        # Send notifications to all other co-founders
        from modules.auth_helper import NotificationService
        notification_service = NotificationService()
        
        all_users = db.get_all_users()
        other_users = [u for u in all_users if u['id'] != user_id]
        
        for other_user in other_users:
            notification_service.send_deletion_notification(
                other_user['email'],
                other_user['first_name'],
                user['first_name'],
                user['last_name'],
                payout_amount,
                other_user['ownership_pct']  # Updated ownership after this user leaves
            )
        
        # Immediately mark user as inactive (but keep in database for records)
        cursor = db.conn.cursor()
        cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        db.conn.commit()
        
        # Confirm deletion request automatically (since we deactivate immediately)
        db.confirm_deletion_request(request_id)
        
        # Log out user
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Account deletion request submitted. You will be logged out.',
            'redirect': url_for('login')
        }), 200
        
    except Exception as e:
        print(f"Delete account error: {e}")
        return jsonify({'error': 'Failed to delete account'}), 500

# ============================================================================
# INVITATION SYSTEM API ENDPOINTS
# ============================================================================

@app.route('/api/auth/send-invitation', methods=['POST'])
@login_required
@admin_required
def api_send_invitation():
    """
    Send invitation to new co-founder (admin only).
    Creates invitation token and sends email with signup link.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        user = db.get_user_by_id(user_id)
        
        # Check if user is admin
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Unauthorized - Admin access required'}), 403
        
        data = request.json
        email = data.get('email', '').strip().lower()
        first_name = data.get('first_name', '').strip()
        
        if not email or not first_name:
            return jsonify({'error': 'Email and first name are required'}), 400
        
        # Validate email format
        is_valid, error_msg = AuthHelper.validate_email(email)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Check if user already exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Check if invitation already sent
        if db.check_invitation_exists(email):
            return jsonify({'error': 'Invitation already sent to this email'}), 400
        
        # Generate invitation token
        invite_token = AuthHelper.generate_invite_token()
        expires_at = AuthHelper.get_invitation_expiry(days=7)
        
        # Create invitation in database
        invitation_id = db.create_invitation(
            email=email,
            first_name=first_name,
            invite_token=invite_token,
            invited_by=user_id,
            expires_at=expires_at
        )
        
        # Send invitation email
        invited_by_name = f"{user['first_name']} {user['last_name']}"
        app_url = request.host_url.rstrip('/')
        
        email_sent = email_service.send_invitation_email(
            to_email=email,
            first_name=first_name,
            invite_token=invite_token,
            invited_by_name=invited_by_name,
            app_url=app_url
        )
        
        # Log audit event
        import json
        db.log_audit_event(
            user_id=user_id,
            action='invite_sent',
            details=json.dumps({
                'email': email,
                'first_name': first_name,
                'invitation_id': invitation_id
            }),
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': f'Invitation sent to {email}',
            'email_sent': email_sent
        }), 200
        
    except Exception as e:
        print(f"Send invitation error: {e}")
        return jsonify({'error': 'Failed to send invitation'}), 500

@app.route('/api/auth/validate-invitation', methods=['POST'])
def api_validate_invitation():
    """
    Validate invitation token for signup page.
    Returns invitation details if valid.
    """
    try:
        if not BACKEND_AVAILABLE:
            return jsonify({'error': 'Backend not available'}), 503
        
        data = request.json
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({
                'valid': False,
                'error': 'Invitation token required'
            }), 400
        
        # Get invitation from database
        invitation = db.get_invitation_by_token(token)
        
        if not invitation:
            return jsonify({
                'valid': False,
                'error': 'Invalid invitation token'
            }), 400
        
        # Validate invitation status
        is_valid, error_msg = AuthHelper.validate_invitation_token(
            token=token,
            expires_at=invitation['expires_at'],
            used=invitation['used']
        )
        
        if not is_valid:
            return jsonify({
                'valid': False,
                'error': error_msg
            }), 400
        
        return jsonify({
            'valid': True,
            'email': invitation['email'],
            'first_name': invitation['first_name']
        }), 200
        
    except Exception as e:
        print(f"Validate invitation error: {e}")
        return jsonify({
            'valid': False,
            'error': 'Failed to validate invitation'
        }), 500

@app.route('/api/auth/pending-invitations', methods=['GET'])
@login_required
def api_pending_invitations():
    """
    Get pending invitations sent by current admin.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        user = db.get_user_by_id(user_id)
        
        # Check if user is admin
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Unauthorized - Admin access required'}), 403
        
        # Get pending invitations
        invitations = db.get_pending_invitations(user_id)
        
        # Format dates for display
        for invite in invitations:
            invite['sent_date'] = invite['created_at']
            invite['expires_date'] = invite['expires_at']
            del invite['created_at']
            del invite['expires_at']
        
        return jsonify(invitations), 200
        
    except Exception as e:
        print(f"Get pending invitations error: {e}")
        return jsonify({'error': 'Failed to retrieve invitations'}), 500

# ============================================================================
# FUND & LEDGER MANAGEMENT API ENDPOINTS
# ============================================================================

@app.route('/api/fund/overview', methods=['GET'])
@login_required
def api_fund_overview():
    """
    Get fund-level overview data.
    Returns total capital, co-founder count, and user's ownership percentage.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        # Get fund overview from database
        overview = db.get_fund_overview()
        
        if not overview:
            return jsonify({
                'total_capital': 0.0,
                'cofounder_count': 0,
                'user_ownership': 0.0
            }), 200
        
        # Get user's ownership percentage
        user = db.get_user_by_id(user_id)
        user_ownership = user.get('ownership_pct', 0.0) if user else 0.0
        
        return jsonify({
            'total_capital': overview.get('total_capital', 0.0),
            'cofounder_count': overview.get('cofounder_count', 0),
            'user_ownership': round(user_ownership, 2)
        }), 200
        
    except Exception as e:
        print(f"Fund overview error: {e}")
        return jsonify({'error': 'Failed to retrieve fund overview'}), 500

@app.route('/api/fund/cofounders', methods=['GET'])
@login_required
def api_fund_cofounders():
    """
    Get list of all co-founders with their contributions and ownership.
    Available to all authenticated users.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get all co-founders from database
        cofounders = db.get_all_cofounders()
        
        if not cofounders:
            return jsonify([]), 200
        
        # Format data for frontend
        formatted_cofounders = []
        for cf in cofounders:
            formatted_cofounders.append({
                'user_id': cf.get('id'),
                'name': f"{cf.get('first_name', '')} {cf.get('last_name', '')}".strip(),
                'email': cf.get('email', ''),
                'contribution': round(cf.get('fund_contribution', 0.0), 2),
                'ownership': round(cf.get('ownership_pct', 0.0), 2),
                'joined_date': cf.get('created_at', '')
            })
        
        return jsonify(formatted_cofounders), 200
        
    except Exception as e:
        print(f"Get cofounders error: {e}")
        return jsonify({'error': 'Failed to retrieve co-founders'}), 500

@app.route('/api/ledger/summary', methods=['GET'])
@login_required
def api_ledger_summary():
    """
    Get user's capital ledger summary.
    Returns current balance, total contributions, YTD P&L, and ownership.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        # Get ledger summary from database
        summary = db.get_user_ledger_summary(user_id)
        
        if not summary:
            return jsonify({
                'current_balance': 0.0,
                'total_contributions': 0.0,
                'ytd_pl': 0.0,
                'ownership': 0.0
            }), 200
        
        return jsonify({
            'current_balance': round(summary.get('current_balance', 0.0), 2),
            'total_contributions': round(summary.get('total_contributions', 0.0), 2),
            'ytd_pl': round(summary.get('ytd_pl', 0.0), 2),
            'ownership': round(summary.get('ownership_pct', 0.0), 2)
        }), 200
        
    except Exception as e:
        print(f"Ledger summary error: {e}")
        return jsonify({'error': 'Failed to retrieve ledger summary'}), 500

@app.route('/api/ledger/transactions', methods=['GET'])
@login_required
def api_ledger_transactions():
    """
    Get user's capital transaction history.
    Supports optional pagination via 'limit' query parameter.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        
        # Get limit from query parameters (default: all transactions)
        limit = request.args.get('limit', type=int)
        
        # Get transactions from database
        transactions = db.get_user_transactions(user_id, limit)
        
        if not transactions:
            return jsonify([]), 200
        
        # Format data for frontend
        formatted_transactions = []
        for tx in transactions:
            formatted_transactions.append({
                'date': tx.get('transaction_date', ''),
                'type': tx.get('transaction_type', ''),
                'amount': round(tx.get('amount', 0.0), 2),
                'balance_after': round(tx.get('balance_after', 0.0), 2),
                'notes': tx.get('notes', '')
            })
        
        return jsonify(formatted_transactions), 200
        
    except Exception as e:
        print(f"Get transactions error: {e}")
        return jsonify({'error': 'Failed to retrieve transactions'}), 500

@app.route('/api/ledger/record-transaction', methods=['POST'])
@login_required
@admin_required
def api_record_transaction():
    """
    Record capital transaction (admin only).
    Creates transaction record and updates user balance.
    Recalculates ownership percentages for all co-founders.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        admin_user_id = session['user_id']
        admin_user = db.get_user_by_id(admin_user_id)
        
        # Check if user is admin
        if not admin_user or admin_user.get('role') != 'admin':
            return jsonify({'error': 'Unauthorized - Admin access required'}), 403
        
        data = request.json
        
        # Validate required fields
        user_id = data.get('user_id')
        transaction_type = data.get('transaction_type')
        amount = data.get('amount')
        transaction_date = data.get('transaction_date')
        notes = data.get('notes', '')
        
        if not all([user_id, transaction_type, amount, transaction_date]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate transaction type
        valid_types = ['contribution', 'distribution', 'withdrawal']
        if transaction_type not in valid_types:
            return jsonify({
                'error': f'Invalid transaction type. Must be one of: {", ".join(valid_types)}'
            }), 400
        
        # Validate amount
        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({'error': 'Amount must be greater than zero'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format'}), 400
        
        # Validate date format
        try:
            from datetime import datetime
            datetime.strptime(transaction_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Check if target user exists
        target_user = db.get_user_by_id(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Record transaction in database
        transaction_id = db.record_capital_transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            transaction_date=transaction_date,
            notes=notes,
            created_by=admin_user_id
        )
        
        if not transaction_id:
            return jsonify({'error': 'Failed to record transaction'}), 500
        
        # Log audit event
        import json
        db.log_audit_event(
            user_id=admin_user_id,
            action='transaction_recorded',
            details=json.dumps({
                'transaction_id': transaction_id,
                'target_user_id': user_id,
                'type': transaction_type,
                'amount': amount,
                'date': transaction_date
            }),
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': 'Transaction recorded successfully',
            'transaction_id': transaction_id
        }), 200
        
    except Exception as e:
        print(f"Record transaction error: {e}")
        return jsonify({'error': 'Failed to record transaction'}), 500

@app.route('/api/documents/audit-log', methods=['GET'])
@login_required
def api_audit_log():
    """
    Get audit log entries (admin only).
    Returns system-wide audit trail for compliance.
    """
    try:
        if not BACKEND_AVAILABLE or 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_id = session['user_id']
        user = db.get_user_by_id(user_id)
        
        # Check if user is admin
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Unauthorized - Admin access required'}), 403
        
        # Get limit from query parameters (default: 100)
        limit = request.args.get('limit', default=100, type=int)
        
        # Get audit log from database
        audit_entries = db.get_audit_log(user_id=None, limit=limit)
        
        if not audit_entries:
            return jsonify([]), 200
        
        # Format data for frontend
        formatted_entries = []
        for entry in audit_entries:
            # Get user name for this entry
            entry_user = db.get_user_by_id(entry.get('user_id', 0))
            user_name = 'Unknown User'
            if entry_user:
                user_name = f"{entry_user.get('first_name', '')} {entry_user.get('last_name', '')}".strip()
            
            formatted_entries.append({
                'timestamp': entry.get('timestamp', ''),
                'user': user_name,
                'action': entry.get('action', ''),
                'details': entry.get('details', ''),
                'ip_address': entry.get('ip_address', '')
            })
        
        return jsonify(formatted_entries), 200
        
    except Exception as e:
        print(f"Get audit log error: {e}")
        return jsonify({'error': 'Failed to retrieve audit log'}), 500

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

@app.route('/profile')
@login_required
def profile():
    """Profile page for user personal information management."""
    # Get full user data from database
    user_data = None
    if BACKEND_AVAILABLE and 'user_id' in session:
        user_data = db.get_user_by_id(session['user_id'])
    
    # Fallback to hardcoded data if no database user
    if not user_data:
        username = session.get('username', 'Unknown')
        user_data = {
            'username': username,
            'first_name': username.capitalize(),
            'last_name': 'User',
            'email': f'{username}@example.com',
            'phone_number': '',
            'role': 'member'
        }
    
    return render_template('profile.html', user=user_data)

@app.route('/fund')
@login_required
def fund():
    """Fund management page showing co-founders and ownership."""
    # Get full user data from database
    user_data = None
    if BACKEND_AVAILABLE and 'user_id' in session:
        user_data = db.get_user_by_id(session['user_id'])
    
    # Fallback to hardcoded data if no database user
    if not user_data:
        username = session.get('username', 'Unknown')
        user_data = {
            'username': username,
            'first_name': username.capitalize(),
            'last_name': 'User',
            'email': f'{username}@example.com',
            'role': 'member'
        }
    
    return render_template('fund.html', user=user_data)

@app.route('/ledger')
@login_required
def ledger():
    """Capital ledger page showing transactions and balances."""
    # Get full user data from database
    user_data = None
    if BACKEND_AVAILABLE and 'user_id' in session:
        user_data = db.get_user_by_id(session['user_id'])
    
    # Fallback to hardcoded data if no database user
    if not user_data:
        username = session.get('username', 'Unknown')
        user_data = {
            'username': username,
            'first_name': username.capitalize(),
            'last_name': 'User',
            'email': f'{username}@example.com',
            'phone_number': '(555) 000-0000',
            'timezone': 'America/New_York',
            'fund_contribution': 0.0,
            'ownership_pct': 0.0,
            'role': 'member'
        }
    
    return render_template('ledger.html', user=user_data)

@app.route('/documents')
@login_required
def documents():
    """Documents page showing quarterly reports, tax documents, and audit logs."""
    # Get full user data from database
    user_data = None
    if BACKEND_AVAILABLE and 'user_id' in session:
        user_data = db.get_user_by_id(session['user_id'])
    
    # Fallback to hardcoded data if no database user
    if not user_data:
        username = session.get('username', 'Unknown')
        user_data = {
            'username': username,
            'first_name': username.capitalize(),
            'last_name': 'User',
            'email': f'{username}@example.com',
            'phone_number': '(555) 000-0000',
            'timezone': 'America/New_York',
            'fund_contribution': 0.0,
            'ownership_pct': 0.0,
            'role': 'member'
        }
    
    return render_template('documents.html', user=user_data)

@app.route('/settings')
@login_required
@admin_required
def settings():
    # Get full user data from database
    user_data = None
    if BACKEND_AVAILABLE and 'user_id' in session:
        user_data = db.get_user_by_id(session['user_id'])
    
    # Fallback to hardcoded users if no database user
    if not user_data:
        username = session.get('username', 'Unknown')
        user_data = {
            'username': username,
            'first_name': username.capitalize(),
            'last_name': 'User',
            'email': f'{username}@example.com',
            'phone_number': '(555) 000-0000',
            'timezone': 'America/New_York',
            'fund_contribution': 0.0,
            'ownership_pct': 0.0
        }
    
    return render_template('settings.html', username=session.get('username'), user=user_data)

@app.route('/api-credentials')
@login_required
@admin_required
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



@app.route('/api/scheduler/trigger', methods=['POST'])
@login_required
@admin_required
def trigger_morning_report():
    """Manually trigger morning report generation (admin only)."""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        result = scheduler.trigger_manual_generation()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scheduler/status')
@login_required
def get_scheduler_status():
    """Get scheduler status and next run time."""
    if not BACKEND_AVAILABLE:
        return jsonify({'error': 'Backend modules not available'}), 500
    
    try:
        status = scheduler.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/market-status')
def get_market_status_api():
    """Get current market status and progress information."""
    try:
        from modules.market_calendar import get_market_status
        
        status = get_market_status()
        progress_pct = 0
        time_remaining = "Market Closed"
        time_remaining_seconds = 0
        
        if status['status'] == 'open':
            market_open = status['market_open']
            market_close = status['market_close']
            current_time = status['current_time']
            
            total_duration = (market_close - market_open).total_seconds()
            elapsed = (current_time - market_open).total_seconds()
            progress_pct = min(100, max(0, (elapsed / total_duration) * 100))
            
            remaining = market_close - current_time
            time_remaining_seconds = int(remaining.total_seconds())
            hours = time_remaining_seconds // 3600
            minutes = (time_remaining_seconds % 3600) // 60
            seconds = time_remaining_seconds % 60
            time_remaining = f"{hours}:{minutes:02d}:{seconds:02d}"
        elif status['status'] == 'pre_market':
            time_remaining = "Pre-Market"
        elif status['status'] == 'after_hours':
            time_remaining = "After Hours"
        
        response = {
            'status': status['status'],
            'is_trading_day': status.get('is_trading_day', False),
            'progress_pct': round(progress_pct, 2),
            'time_remaining': time_remaining,
            'time_remaining_seconds': time_remaining_seconds,
            'current_time': status['current_time'].isoformat(),
            'next_trading_day': status.get('next_trading_day').isoformat() if status.get('next_trading_day') else None
        }
        
        if 'market_open' in status:
            response['market_open'] = status['market_open'].isoformat()
            response['market_close'] = status['market_close'].isoformat()
        
        return jsonify(response)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'status': 'error',
            'is_trading_day': False,
            'progress_pct': 0,
            'time_remaining': 'Error'
        }), 500


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
        # Stock selection is now function-based, not class-based
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
@admin_required
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
        print(f"ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¯ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¸ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  Market calendar error: {e}")
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
    print("ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ RAILYARD MARKETS - VWAP Recovery Trading Platform")
    print("="*70)
    print("\nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ Server starting...")
    print(f"ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ Backend: {'Loaded' if BACKEND_AVAILABLE else 'Not Available (using simulation)'}")
    print(f"ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ Mode: {'Simulation' if not BACKEND_AVAILABLE else 'Production Ready'}")
    print("ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ Access: http://localhost:5000")
    print("\nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ Login Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n   Username: cofounder")
    print("   Password: luggage2025")
    print("\n" + "="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
