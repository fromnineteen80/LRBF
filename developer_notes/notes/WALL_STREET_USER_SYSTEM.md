# Wall Street Professional-Level User Management System
## Complete Implementation Instructions

**Date:** October 15, 2025  
**Purpose:** Restructure user management to institutional investment fund standards  
**Estimated Time:** 8-12 hours of development  
**Status:** Ready for Implementation

---

## 🎯 EXECUTIVE SUMMARY

### The Problem
Current system has critical security and organizational issues:
- **Security Flaw:** Public signup page (`/signup`) allows anyone to register
- **Mixed Concerns:** Settings page combines personal profile, system config, and fund management
- **No Capital Tracking:** No way to track contributions, withdrawals, or ownership percentages
- **No Audit Trail:** No historical record of transactions
- **No Role-Based Access:** All users have same permissions

### The Solution
Restructure into 5 separate functional areas matching institutional investment fund standards:

1. **Profile Page** - Personal information only
2. **Settings Page** - System configuration and trading parameters
3. **Fund Page** - Co-founder management, invitations, ownership
4. **Ledger Page** - Capital transactions, statements, tax documents
5. **Documents Page** - Quarterly reports, K-1 forms, audit trail

**Plus:**
- Invitation-only signup system with email/SMS
- Role-based access control (admin vs member)
- Complete capital tracking with transaction history
- Monthly statement generation
- Full audit trail

### Impact
- **Professional-grade fund management**
- **Secure invitation-only access**
- **Clear separation of concerns**
- **Institutional-level capital tracking**
- **Compliance-ready documentation**
- **Wall Street veteran-level user experience**

---

## 📊 DATABASE SCHEMA ADDITIONS

### 1. Add Role to Users Table

```sql
-- Add role column to existing users table
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'member';

-- Roles:
-- 'admin' = Managing partner, can invite, manage fund
-- 'member' = Regular co-founder, view-only access
```

### 2. Create Invitations Table

```sql
CREATE TABLE invitations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    first_name TEXT,
    invite_token TEXT UNIQUE NOT NULL,
    invited_by INTEGER NOT NULL,  -- User ID who sent invite
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT 0,
    used_at TIMESTAMP,
    used_by INTEGER,  -- User ID who used this invite
    FOREIGN KEY (invited_by) REFERENCES users(id)
);

CREATE INDEX idx_invite_token ON invitations(invite_token);
CREATE INDEX idx_invite_email ON invitations(email);
```

### 3. Create Capital Transactions Table

```sql
CREATE TABLE capital_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type TEXT NOT NULL,  -- 'contribution', 'distribution', 'withdrawal'
    amount REAL NOT NULL,
    balance_after REAL NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,  -- Admin who recorded it
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_capital_user ON capital_transactions(user_id);
CREATE INDEX idx_capital_date ON capital_transactions(transaction_date);
```

### 4. Create Monthly Statements Table

```sql
CREATE TABLE monthly_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    statement_date DATE NOT NULL,  -- First day of month
    opening_balance REAL NOT NULL,
    contributions REAL DEFAULT 0,
    distributions REAL DEFAULT 0,
    profit_loss REAL DEFAULT 0,
    closing_balance REAL NOT NULL,
    ownership_pct REAL NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, statement_date)
);

CREATE INDEX idx_statement_user ON monthly_statements(user_id);
CREATE INDEX idx_statement_date ON monthly_statements(statement_date);
```

### 5. Create Audit Log Table

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- 'invite_sent', 'user_joined', 'contribution_added', etc.
    details TEXT,  -- JSON with additional info
    ip_address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
```

### 6. Migration Script

```python
# migrate_to_wall_street.py
import sqlite3
from datetime import datetime, timedelta

def migrate_database():
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    # Add role column to users
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'member'")
        print("✅ Added role column to users table")
    except sqlite3.OperationalError:
        print("⚠️  Role column already exists")
    
    # Create invitations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            first_name TEXT,
            invite_token TEXT UNIQUE NOT NULL,
            invited_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            used_at TIMESTAMP,
            used_by INTEGER,
            FOREIGN KEY (invited_by) REFERENCES users(id)
        )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invite_token ON invitations(invite_token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invite_email ON invitations(email)")
    print("✅ Created invitations table")
    
    # Create capital_transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS capital_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_date DATE NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_capital_user ON capital_transactions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_capital_date ON capital_transactions(transaction_date)")
    print("✅ Created capital_transactions table")
    
    # Create monthly_statements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            statement_date DATE NOT NULL,
            opening_balance REAL NOT NULL,
            contributions REAL DEFAULT 0,
            distributions REAL DEFAULT 0,
            profit_loss REAL DEFAULT 0,
            closing_balance REAL NOT NULL,
            ownership_pct REAL NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, statement_date)
        )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_statement_user ON monthly_statements(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_statement_date ON monthly_statements(statement_date)")
    print("✅ Created monthly_statements table")
    
    # Create audit_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
    print("✅ Created audit_log table")
    
    # Set first user as admin
    cursor.execute("UPDATE users SET role = 'admin' WHERE id = 1")
    print("✅ Set first user as admin")
    
    # Migrate existing fund_contribution to capital_transactions
    cursor.execute("SELECT id, fund_contribution FROM users WHERE fund_contribution > 0")
    existing_contributions = cursor.fetchall()
    
    for user_id, amount in existing_contributions:
        cursor.execute('''
            INSERT INTO capital_transactions 
            (user_id, transaction_date, transaction_type, amount, balance_after, notes)
            VALUES (?, ?, 'contribution', ?, ?, 'Initial capital contribution')
        ''', (user_id, datetime.now().date(), amount, amount))
    
    print(f"✅ Migrated {len(existing_contributions)} existing contributions")
    
    conn.commit()
    conn.close()
    print("\n🎉 Migration complete!")

if __name__ == '__main__':
    migrate_database()
```

---

## 🔐 INVITATION SYSTEM

### Flow Overview

**Step 1: Admin Invites Co-Founder**
```
Fund Page → "Invite Co-Founder" Section
- Enter: email, first_name
- Click: "Send Invitation"
- System generates unique token
- Sends email with signup link
```

**Step 2: Invitee Receives Email**
```
Subject: You're Invited to Join The Luggage Room Boys Fund

Hi Hugo,

You've been invited by [Admin Name] to join The Luggage Room Boys Fund.

Click here to create your account:
https://yourapp.com/signup?invite=inv_a8f3h29fh2983fh

This invitation expires in 7 days.
```

**Step 3: Invitee Signs Up**
```
/signup?invite=inv_a8f3h29fh2983fh

- System validates token (exists, not expired, not used)
- Pre-fills email from invitation
- User completes profile
- SMS verification code sent
- User enters code
- Account created
- Invitation marked as used
```

**Step 4: Admin Notified**
```
Email: Hugo Martinez has joined the fund
SMS: New co-founder joined: Hugo Martinez
```

### Backend Implementation

```python
# modules/auth_helpers.py additions

import secrets
import string
from datetime import datetime, timedelta

def generate_invite_token():
    """Generate secure invitation token."""
    alphabet = string.ascii_letters + string.digits
    return 'inv_' + ''.join(secrets.choice(alphabet) for _ in range(32))

def create_invitation(email, first_name, invited_by_user_id):
    """Create invitation and send email."""
    token = generate_invite_token()
    expires_at = datetime.now() + timedelta(days=7)
    
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO invitations (email, first_name, invite_token, invited_by, expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (email, first_name, token, invited_by_user_id, expires_at))
    
    conn.commit()
    conn.close()
    
    # Send email (implement with SendGrid)
    send_invitation_email(email, first_name, token)
    
    # Log to audit trail
    log_audit_event(invited_by_user_id, 'invite_sent', {
        'email': email,
        'first_name': first_name
    })
    
    return token

def validate_invitation(token):
    """Check if invitation token is valid."""
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, email, first_name, expires_at, used
        FROM invitations
        WHERE invite_token = ?
    ''', (token,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {'valid': False, 'error': 'Invalid invitation token'}
    
    invite_id, email, first_name, expires_at, used = result
    
    if used:
        return {'valid': False, 'error': 'Invitation already used'}
    
    if datetime.now() > datetime.fromisoformat(expires_at):
        return {'valid': False, 'error': 'Invitation expired'}
    
    return {
        'valid': True,
        'email': email,
        'first_name': first_name,
        'invite_id': invite_id
    }

def mark_invitation_used(token, user_id):
    """Mark invitation as used after signup."""
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE invitations
        SET used = 1, used_at = ?, used_by = ?
        WHERE invite_token = ?
    ''', (datetime.now(), user_id, token))
    
    # Update users table with invited_by reference
    cursor.execute('''
        SELECT invited_by FROM invitations WHERE invite_token = ?
    ''', (token,))
    invited_by = cursor.fetchone()[0]
    
    cursor.execute('''
        UPDATE users SET invited_by = ? WHERE id = ?
    ''', (invited_by, user_id))
    
    conn.commit()
    conn.close()

def get_pending_invitations(user_id):
    """Get all pending invitations sent by this user."""
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT email, first_name, created_at, expires_at
        FROM invitations
        WHERE invited_by = ? AND used = 0
        ORDER BY created_at DESC
    ''', (user_id,))
    
    invites = cursor.fetchall()
    conn.close()
    
    return [{
        'email': inv[0],
        'first_name': inv[1],
        'sent_date': inv[2],
        'expires_date': inv[3]
    } for inv in invites]
```

### Email Integration (SendGrid)

```python
# modules/email_service.py

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@luggageroomboys.com')

def send_invitation_email(to_email, first_name, invite_token):
    """Send invitation email via SendGrid."""
    
    # If no API key, print to console (development mode)
    if not SENDGRID_API_KEY:
        print(f"\n📧 INVITATION EMAIL (Development Mode)")
        print(f"To: {to_email}")
        print(f"Subject: You're Invited to Join The Luggage Room Boys Fund")
        print(f"Link: http://localhost:5000/signup?invite={invite_token}")
        print(f"Expires: 7 days\n")
        return
    
    # Production: Send real email
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject="You're Invited to Join The Luggage Room Boys Fund",
        html_content=f'''
        <html>
        <body style="font-family: 'Roboto', sans-serif; padding: 20px;">
            <h2>Hi {first_name},</h2>
            <p>You've been invited to join The Luggage Room Boys Fund.</p>
            <p>Click the button below to create your account:</p>
            <a href="https://yourapp.com/signup?invite={invite_token}" 
               style="display: inline-block; background: #1976D2; color: white; 
                      padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                Join the Fund
            </a>
            <p style="margin-top: 20px; color: #666;">
                This invitation expires in 7 days.
            </p>
        </body>
        </html>
        '''
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"✅ Invitation email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def send_welcome_email(to_email, first_name):
    """Send welcome email after signup."""
    # Similar implementation
    pass
```

### SMS Integration (Twilio)

```python
# modules/sms_service.py

import os
from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

def send_verification_code(phone_number, code):
    """Send SMS verification code."""
    
    # If no Twilio credentials, print to console (development mode)
    if not TWILIO_ACCOUNT_SID:
        print(f"\n📱 SMS CODE (Development Mode)")
        print(f"To: {phone_number}")
        print(f"Code: {code}\n")
        return
    
    # Production: Send real SMS
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your Luggage Room Boys Fund verification code: {code}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f"✅ SMS sent to {phone_number}")
    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")
```

---

## 🏗️ PAGE RESTRUCTURING

### 1. Profile Page

**Purpose:** Personal information only

**URL:** `/profile`

**Sections:**
- Personal Details (name, email, phone)
- Change Password
- Delete Account

**Access:** All authenticated users

**Template:** `templates/profile.html`

```html
<!-- templates/profile.html -->
{% extends "base.html" %}

{% block title %}Profile - Luggage Room Boys Fund{% endblock %}

{% block content %}
<div class="container" style="max-width: 800px; margin-top: 40px;">
    <h1 class="headline-large">Your Profile</h1>
    
    <!-- Personal Details Card -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Personal Details</h2>
        
        <form id="profileForm" style="margin-top: 20px;">
            <div class="text-field-container">
                <label>First Name</label>
                <input type="text" id="firstName" name="first_name" value="{{ user.first_name }}">
            </div>
            
            <div class="text-field-container">
                <label>Last Name</label>
                <input type="text" id="lastName" name="last_name" value="{{ user.last_name }}">
            </div>
            
            <div class="text-field-container">
                <label>Email</label>
                <input type="email" id="email" name="email" value="{{ user.email }}" readonly>
                <span class="helper-text">Email cannot be changed</span>
            </div>
            
            <div class="text-field-container">
                <label>Phone</label>
                <input type="tel" id="phone" name="phone" value="{{ user.phone }}">
            </div>
            
            <button type="submit" class="btn-filled">Save Changes</button>
        </form>
    </div>
    
    <!-- Change Password Card -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Change Password</h2>
        
        <form id="passwordForm" style="margin-top: 20px;">
            <div class="text-field-container">
                <label>Current Password</label>
                <input type="password" id="currentPassword" name="current_password">
            </div>
            
            <div class="text-field-container">
                <label>New Password</label>
                <input type="password" id="newPassword" name="new_password">
            </div>
            
            <div class="text-field-container">
                <label>Confirm New Password</label>
                <input type="password" id="confirmPassword" name="confirm_password">
            </div>
            
            <button type="submit" class="btn-filled">Update Password</button>
        </form>
    </div>
    
    <!-- Delete Account Card -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px; border-left: 4px solid var(--md-sys-color-error);">
        <h2 class="title-large">Delete Account</h2>
        <p class="body-medium" style="margin-top: 12px;">
            Once you delete your account, there is no going back. Please be certain.
        </p>
        <button onclick="location.href='/delete-account'" class="btn-text" style="color: var(--md-sys-color-error); margin-top: 12px;">
            Delete My Account
        </button>
    </div>
</div>

<script src="{{ url_for('static', filename='js/profile.js') }}"></script>
{% endblock %}
```

### 2. Settings Page

**Purpose:** System configuration and trading parameters

**URL:** `/settings`

**Sections:**
- Trading Mode (simulation vs live)
- Strategy Configuration
- API Credentials
- Notification Preferences

**Access:** All authenticated users (admins can modify, members view-only)

**Template:** `templates/settings.html` (already exists, needs role-based editing)

### 3. Fund Page (NEW)

**Purpose:** Co-founder management and fund overview

**URL:** `/fund`

**Sections:**
- Fund Overview (total capital, ownership distribution)
- Co-Founders List (names, contributions, ownership %)
- Invite Co-Founder (admin only)
- Pending Invitations (admin only)

**Access:** All authenticated users (invite section admin-only)

**Template:** `templates/fund.html`

```html
<!-- templates/fund.html -->
{% extends "base.html" %}

{% block title %}Fund Management - Luggage Room Boys Fund{% endblock %}

{% block content %}
<div class="container" style="max-width: 1200px; margin-top: 40px;">
    <h1 class="headline-large">Fund Management</h1>
    
    <!-- Fund Overview -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Fund Overview</h2>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px;">
            <div>
                <div class="label-small" style="color: var(--md-sys-color-on-surface-variant);">Total Capital</div>
                <div class="headline-medium" id="totalCapital">$0</div>
            </div>
            <div>
                <div class="label-small" style="color: var(--md-sys-color-on-surface-variant);">Co-Founders</div>
                <div class="headline-medium" id="cofounderCount">0</div>
            </div>
            <div>
                <div class="label-small" style="color: var(--md-sys-color-on-surface-variant);">Your Ownership</div>
                <div class="headline-medium" id="yourOwnership">0%</div>
            </div>
        </div>
    </div>
    
    <!-- Co-Founders List -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Co-Founders</h2>
        
        <table class="data-table" style="margin-top: 20px;">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Contribution</th>
                    <th>Ownership</th>
                    <th>Joined</th>
                </tr>
            </thead>
            <tbody id="cofoundersTable">
                <!-- Populated by JavaScript -->
            </tbody>
        </table>
    </div>
    
    {% if user.role == 'admin' %}
    <!-- Invite Co-Founder (Admin Only) -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Invite Co-Founder</h2>
        
        <form id="inviteForm" style="margin-top: 20px; max-width: 500px;">
            <div class="text-field-container">
                <label>Email Address</label>
                <input type="email" id="inviteEmail" name="email" required>
            </div>
            
            <div class="text-field-container">
                <label>First Name</label>
                <input type="text" id="inviteFirstName" name="first_name" required>
            </div>
            
            <button type="submit" class="btn-filled">Send Invitation</button>
        </form>
    </div>
    
    <!-- Pending Invitations -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Pending Invitations</h2>
        
        <table class="data-table" style="margin-top: 20px;">
            <thead>
                <tr>
                    <th>Email</th>
                    <th>Name</th>
                    <th>Sent Date</th>
                    <th>Expires</th>
                </tr>
            </thead>
            <tbody id="pendingInvitesTable">
                <!-- Populated by JavaScript -->
            </tbody>
        </table>
    </div>
    {% endif %}
</div>

<script src="{{ url_for('static', filename='js/fund.js') }}"></script>
{% endblock %}
```

### 4. Ledger Page (NEW)

**Purpose:** Capital transaction history and statements

**URL:** `/ledger`

**Sections:**
- Account Summary (current balance, YTD profit/loss)
- Transaction History (contributions, distributions, withdrawals)
- Monthly Statements (download PDFs)
- Tax Documents (K-1 forms, 1099s)

**Access:** All authenticated users (view own data only)

**Template:** `templates/ledger.html`

```html
<!-- templates/ledger.html -->
{% extends "base.html" %}

{% block title %}Ledger - Luggage Room Boys Fund{% endblock %}

{% block content %}
<div class="container" style="max-width: 1200px; margin-top: 40px;">
    <h1 class="headline-large">Your Ledger</h1>
    
    <!-- Account Summary -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Account Summary</h2>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px;">
            <div>
                <div class="label-small" style="color: var(--md-sys-color-on-surface-variant);">Current Balance</div>
                <div class="headline-medium" id="currentBalance">$0</div>
            </div>
            <div>
                <div class="label-small" style="color: var(--md-sys-color-on-surface-variant);">Total Contributions</div>
                <div class="headline-medium" id="totalContributions">$0</div>
            </div>
            <div>
                <div class="label-small" style="color: var--md-sys-color-on-surface-variant);">YTD Profit/Loss</div>
                <div class="headline-medium" id="ytdPL">$0</div>
            </div>
            <div>
                <div class="label-small" style="color: var(--md-sys-color-on-surface-variant);">Ownership</div>
                <div class="headline-medium" id="ownership">0%</div>
            </div>
        </div>
    </div>
    
    <!-- Transaction History -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Transaction History</h2>
        
        {% if user.role == 'admin' %}
        <button onclick="openTransactionModal()" class="btn-filled" style="margin-top: 12px;">
            Record Transaction
        </button>
        {% endif %}
        
        <table class="data-table" style="margin-top: 20px;">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Type</th>
                    <th>Amount</th>
                    <th>Balance After</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody id="transactionsTable">
                <!-- Populated by JavaScript -->
            </tbody>
        </table>
    </div>
    
    <!-- Monthly Statements -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Monthly Statements</h2>
        
        <div id="statementsGrid" style="margin-top: 20px;">
            <!-- Populated by JavaScript -->
        </div>
    </div>
</div>

<!-- Record Transaction Modal (Admin Only) -->
{% if user.role == 'admin' %}
<div id="transactionModal" class="modal">
    <div class="modal-content">
        <h2 class="title-large">Record Capital Transaction</h2>
        
        <form id="transactionForm">
            <div class="text-field-container">
                <label>Co-Founder</label>
                <select id="transactionUser" name="user_id" required>
                    <!-- Populated by JavaScript -->
                </select>
            </div>
            
            <div class="text-field-container">
                <label>Transaction Type</label>
                <select id="transactionType" name="transaction_type" required>
                    <option value="contribution">Contribution</option>
                    <option value="distribution">Distribution</option>
                    <option value="withdrawal">Withdrawal</option>
                </select>
            </div>
            
            <div class="text-field-container">
                <label>Amount ($)</label>
                <input type="number" id="transactionAmount" name="amount" step="0.01" required>
            </div>
            
            <div class="text-field-container">
                <label>Date</label>
                <input type="date" id="transactionDate" name="transaction_date" required>
            </div>
            
            <div class="text-field-container">
                <label>Notes (optional)</label>
                <textarea id="transactionNotes" name="notes" rows="3"></textarea>
            </div>
            
            <div style="display: flex; gap: 12px; margin-top: 20px;">
                <button type="submit" class="btn-filled">Record Transaction</button>
                <button type="button" onclick="closeTransactionModal()" class="btn-outlined">Cancel</button>
            </div>
        </form>
    </div>
</div>
{% endif %}

<script src="{{ url_for('static', filename='js/ledger.js') }}"></script>
{% endblock %}
```

### 5. Documents Page (NEW)

**Purpose:** Quarterly reports, tax documents, audit trail

**URL:** `/documents`

**Sections:**
- Quarterly Performance Reports
- Annual K-1 Tax Forms
- Fund Documents (operating agreement, etc.)
- Audit Trail (admin only)

**Access:** All authenticated users (audit trail admin-only)

**Template:** `templates/documents.html`

```html
<!-- templates/documents.html -->
{% extends "base.html" %}

{% block title %}Documents - Luggage Room Boys Fund{% endblock %}

{% block content %}
<div class="container" style="max-width: 1200px; margin-top: 40px;">
    <h1 class="headline-large">Documents</h1>
    
    <!-- Quarterly Reports -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Quarterly Performance Reports</h2>
        
        <div id="quarterlyReportsGrid" style="margin-top: 20px;">
            <!-- Populated by JavaScript -->
        </div>
    </div>
    
    <!-- Tax Documents -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Tax Documents</h2>
        
        <div id="taxDocumentsGrid" style="margin-top: 20px;">
            <!-- Populated by JavaScript -->
        </div>
    </div>
    
    <!-- Fund Documents -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Fund Documents</h2>
        
        <div style="margin-top: 20px;">
            <div class="document-item">
                <span class="material-icons">description</span>
                <span>Operating Agreement</span>
                <button class="btn-text">Download</button>
            </div>
            <div class="document-item">
                <span class="material-icons">description</span>
                <span>Investment Policy Statement</span>
                <button class="btn-text">Download</button>
            </div>
        </div>
    </div>
    
    {% if user.role == 'admin' %}
    <!-- Audit Trail (Admin Only) -->
    <div class="surface elevation-1" style="padding: 24px; margin: 20px 0; border-radius: 12px;">
        <h2 class="title-large">Audit Trail</h2>
        
        <table class="data-table" style="margin-top: 20px;">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Details</th>
                    <th>IP Address</th>
                </tr>
            </thead>
            <tbody id="auditTable">
                <!-- Populated by JavaScript -->
            </tbody>
        </table>
    </div>
    {% endif %}
</div>

<script src="{{ url_for('static', filename='js/documents.js') }}"></script>
{% endblock %}
```

---

## 🔧 BACKEND API ENDPOINTS

### Authentication Endpoints

```python
# app_unified.py additions

@app.route('/api/auth/send-invitation', methods=['POST'])
@login_required
def api_send_invitation():
    """Send invitation to new co-founder (admin only)."""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    email = data.get('email')
    first_name = data.get('first_name')
    
    if not email or not first_name:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'User with this email already exists'}), 400
    conn.close()
    
    # Create invitation
    token = create_invitation(email, first_name, session['user_id'])
    
    return jsonify({
        'success': True,
        'message': f'Invitation sent to {email}'
    })

@app.route('/api/auth/validate-invitation', methods=['POST'])
def api_validate_invitation():
    """Validate invitation token."""
    data = request.json
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Token required'}), 400
    
    result = validate_invitation(token)
    return jsonify(result)

@app.route('/api/auth/pending-invitations', methods=['GET'])
@login_required
def api_pending_invitations():
    """Get pending invitations (admin only)."""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    invites = get_pending_invitations(session['user_id'])
    return jsonify(invites)

@app.route('/api/auth/update-profile', methods=['POST'])
@login_required
def api_update_profile():
    """Update user profile."""
    data = request.json
    user_id = session['user_id']
    
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users
        SET first_name = ?, last_name = ?, phone = ?
        WHERE id = ?
    ''', (data.get('first_name'), data.get('last_name'), data.get('phone'), user_id))
    
    conn.commit()
    conn.close()
    
    log_audit_event(user_id, 'profile_updated', {})
    
    return jsonify({'success': True})
```

### Fund Management Endpoints

```python
@app.route('/api/fund/overview', methods=['GET'])
@login_required
def api_fund_overview():
    """Get fund overview data."""
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    # Total capital
    cursor.execute("SELECT SUM(fund_contribution) FROM users")
    total_capital = cursor.fetchone()[0] or 0
    
    # Co-founder count
    cursor.execute("SELECT COUNT(*) FROM users")
    cofounder_count = cursor.fetchone()[0]
    
    # Current user's ownership
    cursor.execute("SELECT ownership_pct FROM users WHERE id = ?", (session['user_id'],))
    user_ownership = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        'total_capital': total_capital,
        'cofounder_count': cofounder_count,
        'user_ownership': user_ownership
    })

@app.route('/api/fund/cofounders', methods=['GET'])
@login_required
def api_cofounders():
    """Get list of all co-founders."""
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT first_name, last_name, email, fund_contribution, ownership_pct, created_at
        FROM users
        ORDER BY created_at ASC
    ''')
    
    cofounders = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'name': f"{cf[0]} {cf[1]}",
        'email': cf[2],
        'contribution': cf[3],
        'ownership': cf[4],
        'joined_date': cf[5]
    } for cf in cofounders])
```

### Ledger Endpoints

```python
@app.route('/api/ledger/summary', methods=['GET'])
@login_required
def api_ledger_summary():
    """Get user's ledger summary."""
    user_id = session['user_id']
    
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    # Current balance
    cursor.execute("SELECT fund_contribution FROM users WHERE id = ?", (user_id,))
    current_balance = cursor.fetchone()[0] or 0
    
    # Total contributions
    cursor.execute('''
        SELECT SUM(amount) FROM capital_transactions
        WHERE user_id = ? AND transaction_type = 'contribution'
    ''', (user_id,))
    total_contributions = cursor.fetchone()[0] or 0
    
    # YTD profit/loss (placeholder - implement later)
    ytd_pl = 0
    
    # Ownership
    cursor.execute("SELECT ownership_pct FROM users WHERE id = ?", (user_id,))
    ownership = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        'current_balance': current_balance,
        'total_contributions': total_contributions,
        'ytd_pl': ytd_pl,
        'ownership': ownership
    })

@app.route('/api/ledger/transactions', methods=['GET'])
@login_required
def api_ledger_transactions():
    """Get user's transaction history."""
    user_id = session['user_id']
    
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT transaction_date, transaction_type, amount, balance_after, notes
        FROM capital_transactions
        WHERE user_id = ?
        ORDER BY transaction_date DESC
    ''', (user_id,))
    
    transactions = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'date': tx[0],
        'type': tx[1],
        'amount': tx[2],
        'balance_after': tx[3],
        'notes': tx[4]
    } for tx in transactions])

@app.route('/api/ledger/record-transaction', methods=['POST'])
@login_required
def api_record_transaction():
    """Record capital transaction (admin only)."""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    transaction_type = data.get('transaction_type')
    amount = data.get('amount')
    transaction_date = data.get('transaction_date')
    notes = data.get('notes', '')
    
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    # Get current balance
    cursor.execute("SELECT fund_contribution FROM users WHERE id = ?", (user_id,))
    current_balance = cursor.fetchone()[0] or 0
    
    # Calculate new balance
    if transaction_type == 'contribution':
        new_balance = current_balance + amount
    elif transaction_type in ['distribution', 'withdrawal']:
        new_balance = current_balance - amount
    else:
        conn.close()
        return jsonify({'error': 'Invalid transaction type'}), 400
    
    # Insert transaction
    cursor.execute('''
        INSERT INTO capital_transactions 
        (user_id, transaction_date, transaction_type, amount, balance_after, notes, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, transaction_date, transaction_type, amount, new_balance, notes, session['user_id']))
    
    # Update user's fund_contribution
    cursor.execute("UPDATE users SET fund_contribution = ? WHERE id = ?", (new_balance, user_id))
    
    # Recalculate ownership percentages for all users
    _recalculate_ownership(cursor)
    
    conn.commit()
    conn.close()
    
    log_audit_event(session['user_id'], 'transaction_recorded', {
        'user_id': user_id,
        'type': transaction_type,
        'amount': amount
    })
    
    return jsonify({'success': True})

def _recalculate_ownership(cursor):
    """Recalculate ownership percentages for all users."""
    # Get total capital
    cursor.execute("SELECT SUM(fund_contribution) FROM users")
    total_capital = cursor.fetchone()[0] or 1  # Avoid division by zero
    
    # Update each user's ownership percentage
    cursor.execute("SELECT id, fund_contribution FROM users")
    users = cursor.fetchall()
    
    for user_id, contribution in users:
        ownership_pct = (contribution / total_capital) * 100 if total_capital > 0 else 0
        cursor.execute("UPDATE users SET ownership_pct = ? WHERE id = ?", (ownership_pct, user_id))
```

### Documents Endpoints

```python
@app.route('/api/documents/audit-log', methods=['GET'])
@login_required
def api_audit_log():
    """Get audit log (admin only)."""
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.timestamp, u.first_name, u.last_name, a.action, a.details, a.ip_address
        FROM audit_log a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.timestamp DESC
        LIMIT 100
    ''')
    
    logs = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'timestamp': log[0],
        'user': f"{log[1]} {log[2]}",
        'action': log[3],
        'details': log[4],
        'ip_address': log[5]
    } for log in logs])

def log_audit_event(user_id, action, details):
    """Log an audit event."""
    conn = sqlite3.connect('data/luggage_room.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO audit_log (user_id, action, details, ip_address)
        VALUES (?, ?, ?, ?)
    ''', (user_id, action, json.dumps(details), request.remote_addr))
    
    conn.commit()
    conn.close()
```

---

## 📱 FRONTEND JAVASCRIPT

### fund.js

```javascript
// static/js/fund.js

document.addEventListener('DOMContentLoaded', function() {
    loadFundOverview();
    loadCofounders();
    
    if (document.getElementById('inviteForm')) {
        loadPendingInvitations();
        
        document.getElementById('inviteForm').addEventListener('submit', function(e) {
            e.preventDefault();
            sendInvitation();
        });
    }
});

async function loadFundOverview() {
    const response = await fetch('/api/fund/overview');
    const data = await response.json();
    
    document.getElementById('totalCapital').textContent = `$${data.total_capital.toLocaleString()}`;
    document.getElementById('cofounderCount').textContent = data.cofounder_count;
    document.getElementById('yourOwnership').textContent = `${data.user_ownership.toFixed(2)}%`;
}

async function loadCofounders() {
    const response = await fetch('/api/fund/cofounders');
    const cofounders = await response.json();
    
    const tbody = document.getElementById('cofoundersTable');
    tbody.innerHTML = '';
    
    cofounders.forEach(cf => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${cf.name}</td>
            <td>${cf.email}</td>
            <td>$${cf.contribution.toLocaleString()}</td>
            <td>${cf.ownership.toFixed(2)}%</td>
            <td>${new Date(cf.joined_date).toLocaleDateString()}</td>
        `;
    });
}

async function sendInvitation() {
    const email = document.getElementById('inviteEmail').value;
    const firstName = document.getElementById('inviteFirstName').value;
    
    const response = await fetch('/api/auth/send-invitation', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, first_name: firstName})
    });
    
    const data = await response.json();
    
    if (data.success) {
        showSnackbar('Invitation sent successfully');
        document.getElementById('inviteForm').reset();
        loadPendingInvitations();
    } else {
        showSnackbar(data.error, 'error');
    }
}

async function loadPendingInvitations() {
    const response = await fetch('/api/auth/pending-invitations');
    const invites = await response.json();
    
    const tbody = document.getElementById('pendingInvitesTable');
    tbody.innerHTML = '';
    
    if (invites.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No pending invitations</td></tr>';
        return;
    }
    
    invites.forEach(inv => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${inv.email}</td>
            <td>${inv.first_name}</td>
            <td>${new Date(inv.sent_date).toLocaleDateString()}</td>
            <td>${new Date(inv.expires_date).toLocaleDateString()}</td>
        `;
    });
}
```

### ledger.js

```javascript
// static/js/ledger.js

document.addEventListener('DOMContentLoaded', function() {
    loadLedgerSummary();
    loadTransactions();
    
    if (document.getElementById('transactionForm')) {
        loadUsersForTransaction();
        
        document.getElementById('transactionForm').addEventListener('submit', function(e) {
            e.preventDefault();
            recordTransaction();
        });
    }
});

async function loadLedgerSummary() {
    const response = await fetch('/api/ledger/summary');
    const data = await response.json();
    
    document.getElementById('currentBalance').textContent = `$${data.current_balance.toLocaleString()}`;
    document.getElementById('totalContributions').textContent = `$${data.total_contributions.toLocaleString()}`;
    document.getElementById('ytdPL').textContent = `$${data.ytd_pl.toLocaleString()}`;
    document.getElementById('ownership').textContent = `${data.ownership.toFixed(2)}%`;
}

async function loadTransactions() {
    const response = await fetch('/api/ledger/transactions');
    const transactions = await response.json();
    
    const tbody = document.getElementById('transactionsTable');
    tbody.innerHTML = '';
    
    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No transactions yet</td></tr>';
        return;
    }
    
    transactions.forEach(tx => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${new Date(tx.date).toLocaleDateString()}</td>
            <td><span class="chip ${tx.type}">${tx.type}</span></td>
            <td>$${tx.amount.toLocaleString()}</td>
            <td>$${tx.balance_after.toLocaleString()}</td>
            <td>${tx.notes || '-'}</td>
        `;
    });
}

async function loadUsersForTransaction() {
    const response = await fetch('/api/fund/cofounders');
    const cofounders = await response.json();
    
    const select = document.getElementById('transactionUser');
    select.innerHTML = '';
    
    cofounders.forEach(cf => {
        const option = document.createElement('option');
        option.value = cf.user_id;
        option.textContent = cf.name;
        select.appendChild(option);
    });
}

function openTransactionModal() {
    document.getElementById('transactionModal').style.display = 'flex';
}

function closeTransactionModal() {
    document.getElementById('transactionModal').style.display = 'none';
    document.getElementById('transactionForm').reset();
}

async function recordTransaction() {
    const formData = new FormData(document.getElementById('transactionForm'));
    const data = Object.fromEntries(formData);
    data.amount = parseFloat(data.amount);
    
    const response = await fetch('/api/ledger/record-transaction', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (result.success) {
        showSnackbar('Transaction recorded successfully');
        closeTransactionModal();
        loadLedgerSummary();
        loadTransactions();
    } else {
        showSnackbar(result.error, 'error');
    }
}
```

### profile.js

```javascript
// static/js/profile.js

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('profileForm').addEventListener('submit', function(e) {
        e.preventDefault();
        updateProfile();
    });
    
    document.getElementById('passwordForm').addEventListener('submit', function(e) {
        e.preventDefault();
        changePassword();
    });
});

async function updateProfile() {
    const formData = new FormData(document.getElementById('profileForm'));
    const data = Object.fromEntries(formData);
    
    const response = await fetch('/api/auth/update-profile', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (result.success) {
        showSnackbar('Profile updated successfully');
    } else {
        showSnackbar(result.error, 'error');
    }
}

async function changePassword() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (newPassword !== confirmPassword) {
        showSnackbar('Passwords do not match', 'error');
        return;
    }
    
    const response = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword
        })
    });
    
    const result = await response.json();
    
    if (result.success) {
        showSnackbar('Password changed successfully');
        document.getElementById('passwordForm').reset();
    } else {
        showSnackbar(result.error, 'error');
    }
}
```

### documents.js

```javascript
// static/js/documents.js

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('auditTable')) {
        loadAuditLog();
    }
});

async function loadAuditLog() {
    const response = await fetch('/api/documents/audit-log');
    const logs = await response.json();
    
    const tbody = document.getElementById('auditTable');
    tbody.innerHTML = '';
    
    logs.forEach(log => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${new Date(log.timestamp).toLocaleString()}</td>
            <td>${log.user}</td>
            <td>${log.action.replace(/_/g, ' ')}</td>
            <td>${log.details || '-'}</td>
            <td>${log.ip_address}</td>
        `;
    });
}
```

---

## 🎨 MATERIAL DESIGN 3 STYLING

All new pages must use existing MD3 components and tokens from `styles.css`:

```css
/* Additional styles for new pages */

/* Chips for transaction types */
.chip {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    text-transform: capitalize;
}

.chip.contribution {
    background: var(--md-sys-color-primary-container);
    color: var(--md-sys-color-on-primary-container);
}

.chip.distribution {
    background: var(--md-sys-color-tertiary-container);
    color: var(--md-sys-color-on-tertiary-container);
}

.chip.withdrawal {
    background: var(--md-sys-color-error-container);
    color: var(--md-sys-color-on-error-container);
}

/* Document items */
.document-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.document-item:last-child {
    border-bottom: none;
}

.document-item .material-icons {
    color: var(--md-sys-color-primary);
}

/* Modal styles */
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: var(--md-sys-color-surface);
    padding: 24px;
    border-radius: 12px;
    max-width: 500px;
    width: 90%;
}
```

---

## 🚀 IMPLEMENTATION PHASES

### Phase 1: Database Migration (1 hour)

1. Run `migrate_to_wall_street.py`
2. Verify all tables created
3. Check first user is set as admin
4. Verify existing contributions migrated

**Testing:**
```bash
sqlite3 data/luggage_room.db "SELECT * FROM invitations LIMIT 1;"
sqlite3 data/luggage_room.db "SELECT * FROM capital_transactions LIMIT 1;"
sqlite3 data/luggage_room.db "SELECT first_name, role FROM users;"
```

---

### Phase 2: Backend API Endpoints (3-4 hours)

1. Add invitation system functions to `modules/auth_helpers.py`
2. Add email service (`modules/email_service.py`)
3. Add SMS service (`modules/sms_service.py`)
4. Add API endpoints to `app_unified.py`:
   - `/api/auth/send-invitation`
   - `/api/auth/validate-invitation`
   - `/api/auth/pending-invitations`
   - `/api/auth/update-profile`
   - `/api/fund/overview`
   - `/api/fund/cofounders`
   - `/api/ledger/summary`
   - `/api/ledger/transactions`
   - `/api/ledger/record-transaction`
   - `/api/documents/audit-log`
5. Add audit logging function

**Testing:**
```bash
# Test with curl or Postman
curl -X POST http://localhost:5000/api/auth/send-invitation \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","first_name":"Test"}'
```

---

### Phase 3: Frontend Pages (4-5 hours)

1. Create `templates/profile.html`
2. Create `templates/fund.html`
3. Create `templates/ledger.html`
4. Create `templates/documents.html`
5. Update `templates/settings.html` (simplify to config only)
6. Create `static/js/profile.js`
7. Create `static/js/fund.js`
8. Create `static/js/ledger.js`
9. Create `static/js/documents.js`
10. Update `base.html` sidebar with new navigation items

**Testing:**
- Visit each page
- Verify API calls work
- Test admin-only features (as admin)
- Test member view (as member)
- Verify responsive design

---

### Phase 4: Signup Flow Restriction (1 hour)

1. Modify `/signup` route to require `invite` query parameter
2. Add token validation on page load
3. Show error if token invalid/expired/used
4. Pre-fill email/name from invitation
5. Mark invitation as used after successful signup

**Testing:**
- Try visiting `/signup` directly (should fail)
- Try with valid token (should work)
- Try with expired token (should fail)
- Try with used token (should fail)

---

### Phase 5: Integration Testing (1-2 hours)

1. Test complete invitation flow:
   - Admin sends invite
   - Email received (or console print)
   - Invitee signs up
   - SMS verification
   - Account created
   - Invitation marked used
2. Test capital transactions:
   - Record contribution
   - Verify balance updated
   - Verify ownership recalculated
   - Check transaction history
3. Test role-based access:
   - Admin can access everything
   - Member cannot send invites
   - Member cannot record transactions
4. Test audit trail logging

---

## ✅ CHECKLIST

### Database
- [ ] Run migration script
- [ ] Verify `invitations` table exists
- [ ] Verify `capital_transactions` table exists
- [ ] Verify `monthly_statements` table exists
- [ ] Verify `audit_log` table exists
- [ ] First user set as admin
- [ ] Existing contributions migrated

### Backend
- [ ] Invitation functions implemented
- [ ] Email service implemented (with dev mode)
- [ ] SMS service implemented (with dev mode)
- [ ] All API endpoints functional
- [ ] Audit logging working
- [ ] Role-based access control enforced

### Frontend
- [ ] Profile page complete
- [ ] Fund page complete
- [ ] Ledger page complete
- [ ] Documents page complete
- [ ] Settings page simplified
- [ ] All JavaScript files functional
- [ ] Navigation updated
- [ ] Mobile responsive

### Signup Flow
- [ ] Public signup route requires invitation token
- [ ] Token validation on page load
- [ ] Email/name pre-filled from invitation
- [ ] Invitation marked used after signup
- [ ] Error messages clear and helpful

### Testing
- [ ] Invitation flow works end-to-end
- [ ] Capital transactions work correctly
- [ ] Ownership percentages recalculate
- [ ] Role-based access enforced
- [ ] Audit trail captures all actions
- [ ] Mobile layout works
- [ ] All Material Design 3 compliant

### Production Readiness
- [ ] SendGrid API key configured
- [ ] Twilio credentials configured
- [ ] Environment variables documented
- [ ] Error handling comprehensive
- [ ] Security tested (SQL injection, XSS, etc.)
- [ ] Performance acceptable
- [ ] Documentation complete

---

## 🎉 RESULT

After completing all phases, you will have:

**✅ Secure invitation-only access**
- No public signup
- Email + SMS invitation flow
- Token-based security
- 7-day expiration

**✅ Professional fund management**
- Fund overview page
- Co-founder list with ownership %
- Capital transaction tracking
- Monthly statements
- Tax document repository

**✅ Role-based access control**
- Admin: Can invite, manage fund, record transactions
- Member: View-only access to own data

**✅ Complete capital tracking**
- Contribution history
- Distribution history
- Ownership percentage auto-calculation
- Balance tracking
- Transaction notes and audit trail

**✅ Institutional-level documentation**
- Monthly statements
- Quarterly reports
- Annual K-1 tax forms
- Audit trail
- Fund documents

**✅ Wall Street veteran-level user experience**
- Clean separation of concerns
- Professional page structure
- Clear navigation
- Material Design 3 throughout
- Mobile responsive

---

## 📞 TROUBLESHOOTING

### Common Issues

**Issue:** "Invitation token required"  
**Solution:** Make sure invite token in URL: `/signup?invite=TOKEN`

**Issue:** "Invitation expired"  
**Solution:** Admin must send new invitation. Tokens expire after 7 days.

**Issue:** "Unauthorized" when sending invitation  
**Solution:** Check user has `role = 'admin'` in database.

**Issue:** Capital transactions not showing  
**Solution:** Run migration script to populate initial transactions.

**Issue:** Ownership percentages wrong  
**Solution:** Run `_recalculate_ownership()` manually or record new transaction.

---

## 🎉 CONCLUSION

This implementation transforms the user management system from a basic authentication system into a Wall Street-grade fund management platform with:

- **Secure invitation-only access**
- **Role-based permissions**
- **Complete capital tracking**
- **Professional statements**
- **Full audit trail**
- **Institutional separation of concerns**

**Estimated Total Time:** 8-12 hours

**Start by running the migration script, then implement Phase 1 (Database), then Phase 2 (Backend), then Phase 3 (Frontend).**

**Good luck! 🚀**

---

**Document Version:** 1.0  
**Last Updated:** October 15, 2025  
**Status:** Ready for Implementation  
**Next Step:** Run `migrate_to_wall_street.py`
