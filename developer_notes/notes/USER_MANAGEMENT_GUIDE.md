# Co-Founder User Management System - COMPLETE GUIDE

**Status:** âœ… Database & Frontend Complete | âš ï¸ Flask Routes Needed

This document explains the complete co-founder user management system built for The Luggage Room Boys Fund.

---

## ðŸŽ¯ What Was Built

### 1. Database Tables (modules/database.py)

**✅ Users Table**
- Stores all co-founder information
- Fields: username, password_hash, first_name, last_name, email, phone_number
- Timezone, fund_contribution, ownership_pct (auto-calculated)
- Verification status, active status, invited_by tracking

**✅ Sessions Table**
- Secure session management
- Session tokens, expiry timestamps, last activity tracking
- Automatic cleanup of expired sessions

**✅ Deletion Requests Table**
- Tracks account deletion requests
- Payout calculations (fund value at deletion, payout amount)
- Confirmation workflow

### 2. Authentication Helper (modules/auth_helper.py)

**✅ AuthHelper Class**
- `hash_password()` - bcrypt password hashing (12 rounds)
- `verify_password()` - secure password verification
- `generate_session_token()` - 64-character secure tokens
- `generate_verification_code()` - 6-digit SMS codes
- `validate_password_strength()` - enforces strong passwords
- `validate_email()` - email format validation
- `validate_phone()` - US phone number validation
- `validate_username()` - username requirements checking

**✅ NotificationService Class**
- SMS verification codes (Twilio integration ready)
- Email notifications for account deletion
- Welcome emails for new co-founders
- Development mode (prints to console, no API calls)

### 3. Frontend Pages

**✅ Signup Page (templates/signup.html)**
- Material Design 3 styled registration form
- Sections:
  1. Personal Information (first name, last name, email, phone, timezone)
  2. Fund Contribution (dollar amount input)
  3. Account Credentials (username, password with strength validation)
  4. Phone Verification (6-digit code input, shows after registration)
- Real-time password strength indicator
- Form validation with helpful error messages
- Redirects to login after successful signup

**✅ Settings Page (templates/settings.html) - Updated**
- **NEW: Co-Founder Profile Section** at top
- Display mode: Shows all user information (read-only)
- Edit mode: Enables editing of personal info, phone, timezone, fund contribution
- Four subsections:
  1. Personal Information
  2. Fund Ownership (contribution, ownership %, current value)
  3. Account Information (member since, last login, status)
  4. Danger Zone (delete account, change password)
- Save/Cancel buttons appear in edit mode
- Success/error message notifications

**✅ Account Deletion Page (templates/delete_account.html)**
- Warning card with list of consequences
- Account summary (name, username, contribution, ownership %)
- **Payout Calculation Card** (shows exact dollar amount)
- **Withdrawal Process Instructions:**
  1. Immediate actions (account deactivation, notifications)
  2. Liquidation process (1-5 business days)
  3. Payout transfer (5-7 business days, wire/ACH)
  4. Tax considerations (K-1 form, capital gains)
- Total timeline: 10-15 business days
- Confirmation checkbox (must check to enable delete button)
- Final double-confirmation alert before deletion

---

## ðŸ"§ Database Methods (All Implemented)

### User Management
```python
db.create_user(user_data)                    # Create new co-founder
db.get_user_by_username(username)            # Fetch user by username
db.get_user_by_email(email)                  # Fetch user by email
db.get_user_by_id(user_id)                   # Fetch user by ID
db.get_all_users()                           # Get all active co-founders
db.update_user_profile(user_id, updates)     # Update profile fields
db.update_password(user_id, password_hash)   # Change password
db.verify_user(user_id)                      # Mark phone as verified
db.update_last_login(user_id)                # Track login time
db.get_total_fund_value()                    # Sum of all contributions
```

### Session Management
```python
db.create_session(user_id, token, expires_at)  # New session on login
db.get_session(session_token)                  # Validate session
db.update_session_activity(session_token)      # Keep session alive
db.delete_session(session_token)               # Logout
db.delete_expired_sessions()                   # Cleanup job
```

### Account Deletion
```python
db.create_deletion_request(user_id, fund_value, payout, notes)  # Request deletion
db.confirm_deletion_request(request_id)                          # Execute deletion
db.get_deletion_request(user_id)                                 # Check pending request
```

### Automatic Ownership Calculation
- `_recalculate_ownership()` runs automatically when:
  1. New co-founder joins
  2. Fund contribution amount changes
  3. Co-founder account deleted
- Calculates each user's ownership % based on: `(contribution / total_fund) × 100`
- Updates all active users' ownership_pct field

---

## âš ï¸ What Needs To Be Implemented (Flask Routes in app.py)

You now need to add these API endpoints to `app.py`:

### 1. Signup Route
```python
@app.route('/signup', methods=['GET'])
def signup():
    """Render signup page"""
    return render_template('signup.html')

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    """
    Handle user registration
    
    Steps:
    1. Validate all input fields (use AuthHelper validators)
    2. Check if username/email already exists
    3. Hash password with AuthHelper.hash_password()
    4. Generate verification code
    5. Store user in database with db.create_user()
    6. Send verification SMS (NotificationService.send_verification_code())
    7. Store verification code temporarily (in session or database)
    8. Return success with requires_verification flag
    """
    pass

@app.route('/api/auth/verify-phone', methods=['POST'])
def verify_phone():
    """
    Verify phone number with 6-digit code
    
    Steps:
    1. Get code from request
    2. Compare with stored verification code
    3. Mark user as verified with db.verify_user()
    4. Send welcome email
    5. Return success
    """
    pass

@app.route('/api/auth/resend-code', methods=['POST'])
def resend_code():
    """Resend verification code to phone"""
    pass
```

### 2. Login Route (Update Existing)
```python
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """
    Update existing login to use database
    
    Steps:
    1. Get username/password from request
    2. Fetch user with db.get_user_by_username()
    3. Verify password with AuthHelper.verify_password()
    4. Check if user is_active and is_verified
    5. Generate session token with AuthHelper.generate_session_token()
    6. Calculate expiry with AuthHelper.get_session_expiry(days=30)
    7. Store session with db.create_session()
    8. Update last login with db.update_last_login()
    9. Set session cookie
    10. Return success
    """
    pass
```

### 3. Profile Management Routes
```python
@app.route('/api/auth/update-profile', methods=['POST'])
@login_required
def update_profile():
    """
    Update user profile
    
    Steps:
    1. Get current user from session
    2. Validate updates (use AuthHelper validators)
    3. Update with db.update_user_profile(user_id, updates)
    4. If fund_contribution changed, ownership % auto-recalculates
    5. Send email notification to other co-founders about contribution change
    6. Return success
    """
    pass

@app.route('/api/auth/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Change user password
    
    Steps:
    1. Get current_password and new_password from request
    2. Verify current password
    3. Validate new password strength
    4. Hash new password
    5. Update with db.update_password()
    6. Invalidate all existing sessions (optional security measure)
    7. Return success
    """
    pass
```

### 4. Account Deletion Routes
```python
@app.route('/delete-account', methods=['GET'])
@login_required
def delete_account():
    """
    Render account deletion page
    
    Steps:
    1. Get current user
    2. Calculate current fund value (from IBKR or last EOD balance)
    3. Calculate payout: user.ownership_pct * current_fund_value / 100
    4. Render template with user, current_fund_value, payout_amount
    """
    pass

@app.route('/api/auth/delete-account', methods=['POST'])
@login_required
def api_delete_account():
    """
    Process account deletion request
    
    Steps:
    1. Get current user
    2. Calculate fund value and payout
    3. Create deletion request with db.create_deletion_request()
    4. Get all other co-founders with db.get_all_users()
    5. Send email notification with NotificationService
    6. Confirm deletion with db.confirm_deletion_request()
    7. Log out user (delete session)
    8. Return success
    """
    pass
```

### 5. Settings Route (Update Existing)
```python
@app.route('/settings', methods=['GET'])
@login_required
def settings():
    """
    Render settings page with user profile
    
    Steps:
    1. Get current user from session
    2. Get total fund value with db.get_total_fund_value()
    3. Get current balance from IBKR or database
    4. Render template with user, total_fund_value, current_balance
    """
    pass
```

---

## 🔐 Authentication Flow

### New User Signup
1. User fills out signup form
2. Frontend validates password strength in real-time
3. On submit, POST to `/api/auth/signup`
4. Backend validates all fields
5. Backend generates verification code
6. Backend sends SMS to phone number
7. Verification code input appears
8. User enters 6-digit code
9. POST to `/api/auth/verify-phone`
10. Account marked as verified
11. Welcome email sent
12. Redirect to login page

### Login
1. User enters username/password
2. POST to `/api/auth/login`
3. Backend verifies password (bcrypt)
4. Backend checks if account is active and verified
5. Backend creates session (30-day expiry)
6. Session token stored in cookie
7. User redirected to dashboard

### Session Validation (login_required decorator)
1. Check if session cookie exists
2. Fetch session from database
3. Check if session expired
4. Check if user is still active
5. Update last_activity timestamp
6. Allow access or redirect to login

---

## 📧 Email & SMS Configuration (Production)

### Development Mode (Current)
- All notifications print to console
- SMS: Prints "📱 SMS VERIFICATION CODE: 123456"
- Email: Prints "📧 ACCOUNT DELETION NOTIFICATION"
- No actual API calls

### Production Setup

**1. Twilio (SMS Verification)**
```bash
# Install Twilio
pip install twilio

# Add to .env file
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Uncomment code in modules/auth_helper.py
# Lines 262-275 in NotificationService.send_verification_code()
```

**2. SendGrid (Email Notifications)**
```bash
# Install SendGrid
pip install sendgrid

# Add to .env file
SENDGRID_API_KEY=your_api_key
FROM_EMAIL=noreply@railyardmarkets.com

# Uncomment code in modules/auth_helper.py
# Lines 302-325 in NotificationService.send_account_deletion_notification()
```

**3. Cost Estimates**
- Twilio: ~$0.0075 per SMS (very cheap, ~$0.05 per signup)
- SendGrid: Free tier (100 emails/day) or ~$15/month for 50k emails

---

## 🧪 Testing the System

### 1. Test Database Methods
```bash
cd modules
python database.py  # Runs test suite for all database methods
```

### 2. Test Authentication Helper
```bash
cd modules
python auth_helper.py  # Tests password hashing, validation, tokens
```

### 3. Test Full Signup Flow (After Flask Routes Added)
1. Navigate to `/signup`
2. Fill out form with test data
3. Check console for verification code
4. Enter code to verify phone
5. Check database: `SELECT * FROM users;`
6. Verify ownership_pct was calculated
7. Login with new credentials
8. Check sessions table

### 4. Test Profile Updates
1. Login as co-founder
2. Go to `/settings`
3. Click "Edit Profile"
4. Change email, phone, or contribution
5. Click "Save Changes"
6. Verify database updated
7. If contribution changed, check ownership % recalculated for all users

### 5. Test Account Deletion
1. Login as test co-founder
2. Go to Settings → Danger Zone → Delete Account
3. Review payout calculation
4. Check withdrawal instructions
5. Enable checkbox
6. Confirm deletion
7. Check console for email notifications sent
8. Verify user marked inactive in database
9. Verify ownership % redistributed to remaining users
10. Try to login (should fail - account inactive)

---

## 📊 Database Schema Reference

### users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone_number TEXT NOT NULL,
    timezone TEXT DEFAULT 'America/New_York',
    fund_contribution REAL DEFAULT 0.0,
    ownership_pct REAL DEFAULT 0.0,  -- Auto-calculated
    is_verified BOOLEAN DEFAULT 0,
    verification_code TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    invited_by INTEGER,  -- User ID who invited this co-founder
    FOREIGN KEY (invited_by) REFERENCES users(id)
);
```

### sessions Table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### deletion_requests Table
```sql
CREATE TABLE deletion_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed BOOLEAN DEFAULT 0,
    confirmed_at TIMESTAMP,
    fund_value_at_deletion REAL,
    payout_amount REAL,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 🔒 Security Features

### Password Security
- bcrypt hashing with 12 rounds (industry standard)
- Password strength requirements:
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 number
  - At least 1 special character (!@#$%^&*...)

### Session Security
- 64-character random session tokens (secrets.token_hex(32))
- 30-day expiry by default
- Automatic cleanup of expired sessions
- Last activity tracking
- Cascade deletion when user account deleted

### Rate Limiting
- Login rate limiting already implemented in app.py
- 5 failed attempts = 5-minute lockout
- Per-IP address tracking

### Two-Factor Authentication
- Phone verification required for new accounts
- 6-digit SMS codes
- Code regeneration with "Resend Code" button

---

## 🚀 Deployment Checklist

### Before Launch
- [ ] Implement all Flask routes in app.py
- [ ] Test complete signup → login → profile → deletion flow
- [ ] Set up Twilio account and add credentials to .env
- [ ] Set up SendGrid account and add credentials to .env
- [ ] Uncomment production SMS/email code in auth_helper.py
- [ ] Test SMS verification with real phone number
- [ ] Test email notifications with real email addresses
- [ ] Update FROM_EMAIL to actual domain email
- [ ] Configure proper error handling for API failures
- [ ] Set up database backups (users table is critical!)
- [ ] Implement password reset functionality (forgot password link)
- [ ] Add admin dashboard to manage co-founders
- [ ] Test ownership % calculations with multiple users

### First User (You)
1. Manually insert your account into database:
```python
from modules.database import TradingDatabase
from modules.auth_helper import AuthHelper

db = TradingDatabase()

your_data = {
    'username': 'your_username',
    'password_hash': AuthHelper.hash_password('your_password'),
    'first_name': 'Your',
    'last_name': 'Name',
    'email': 'your@email.com',
    'phone_number': '1234567890',
    'timezone': 'America/New_York',
    'fund_contribution': 15000.00,  # Your initial contribution
    'invited_by': None  # You're the first user
}

user_id = db.create_user(your_data)
db.verify_user(user_id)  # Mark as verified

print(f"✅ First user created with ID: {user_id}")
print(f"   Ownership: 100%")
```

2. Login with your credentials
3. Invite Hugo via email
4. Hugo signs up through `/signup` page
5. System auto-calculates ownership split

---

## 💡 Usage Examples

### Scenario 1: You and Hugo Start the Fund
1. **You:** Contribute $15,000
   - Ownership: 100% (only user)
2. **Hugo signs up:** Contributes $15,000
   - Your ownership: 50% (auto-updated)
   - Hugo ownership: 50%
   - Total fund: $30,000

### Scenario 2: Third Co-Founder Joins
1. **New co-founder:** Contributes $30,000
   - Your ownership: 25% ($15k / $60k)
   - Hugo ownership: 25% ($15k / $60k)
   - New co-founder: 50% ($30k / $60k)
   - Total fund: $60,000

### Scenario 3: Someone Leaves
1. **Third co-founder deletes account**
   - Current fund value in IBKR: $75,000
   - Their payout: $75,000 × 50% = $37,500
   - Remaining fund: $37,500
   - Your new ownership: 50% ($15k / $30k of remaining contributions)
   - Hugo new ownership: 50% ($15k / $30k of remaining contributions)

---

## 📝 Next Steps (Priority Order)

### CRITICAL (Do This First)
1. ✅ Read this entire document
2. ⬜ Implement Flask routes in app.py (see section above)
3. ⬜ Test signup flow completely
4. ⬜ Test login with new database users
5. ⬜ Test profile updates
6. ⬜ Test account deletion

### IMPORTANT (Before Launch)
7. ⬜ Set up Twilio account
8. ⬜ Set up SendGrid account
9. ⬜ Enable production SMS/email code
10. ⬜ Test with real phone numbers and emails

### NICE TO HAVE (Post-Launch)
11. ⬜ Add forgot password functionality
12. ⬜ Add password change dialog (currently placeholder)
13. ⬜ Add admin dashboard to view all co-founders
14. ⬜ Add email notifications for profile changes
15. ⬜ Add 2FA for login (not just signup)

---

## 🎯 Summary

**What You Have:**
- ✅ Complete database schema for users, sessions, deletions
- ✅ All database methods implemented and tested
- ✅ Authentication helper with password hashing, validation, tokens
- ✅ Notification service framework (development mode ready)
- ✅ Beautiful MD3 signup page with phone verification
- ✅ Complete profile management in settings
- ✅ Professional account deletion page with payout calculations

**What You Need:**
- ⬜ Flask routes in app.py (authentication endpoints)
- ⬜ Twilio and SendGrid configuration (production)
- ⬜ Testing complete flow

**Estimated Time to Complete:**
- Flask routes: 2-3 hours (straightforward implementation)
- Testing: 1 hour
- Twilio/SendGrid setup: 30 minutes
- **Total: ~4 hours to production-ready**

---

## 📞 Support

If you need help with:
- **Flask routes**: Use the pseudocode provided above
- **Database issues**: Run `python modules/database.py` to test
- **Authentication issues**: Run `python modules/auth_helper.py` to test
- **Twilio setup**: https://www.twilio.com/docs/sms/quickstart/python
- **SendGrid setup**: https://docs.sendgrid.com/for-developers/sending-email/quickstart-python

---

**Version:** 1.0  
**Last Updated:** October 15, 2025  
**Status:** ✅ Database & Frontend Complete | âš ï¸ Flask Routes Needed

**All commits pushed to GitHub:** https://github.com/fromnineteen80/LRBF
