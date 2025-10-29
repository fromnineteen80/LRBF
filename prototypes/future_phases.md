

---

## **BETA ADVANCED FEATURES - BACKEND ONLY**

*All frontend .html and css files are alpha and will be rebuilt*

**Core Trading Dashboards:** Morning Report / Railyard / EOD Report

---

## **BACKEND COMPLETE ✅**

**Phase 1: User Management**
- Database: `users`, `sessions`, `deletion_requests`
- Auth: login, signup, password management, sessions
- Profile updates
- Account deletion

**Phase 2: Invitation System**
- Database: `invitations` table
- API: Create, validate, track invitations
- Token generation (7-day expiry)

**Phase 3: Fund Management**
- Database methods: `get_fund_overview()`, `get_all_cofounders()`
- Auto-calculate ownership %
- Total capital tracking

**Phase 4: Ledger & Transactions**
- Database: `capital_transactions` table
- API: Record transactions, get history, ledger summary
- Transaction types: contribution, distribution, withdrawal

**Phase 5: Monthly Statements**
- Database: `monthly_statements` table
- Logic: `generate_monthly_statement()`
- Auto-calculation (opening, contributions, distributions, P&L, closing)

**Phase 6: Audit Log**
- Database: `audit_log` table
- Tracking: All actions (logins, transactions, invites, settings changes)
- API: `log_audit_event()`, `get_audit_log()`

---

## **BACKEND TODO 🔨**

### **Phase 7: Expense Management**

**Database:**
```sql
CREATE TABLE expenses (
  id INTEGER PRIMARY KEY,
  date DATE NOT NULL,
  description TEXT NOT NULL,
  amount REAL NOT NULL,
  category TEXT NOT NULL,
  is_recurring BOOLEAN DEFAULT 0,
  recurrence_period TEXT,  -- 'monthly', 'quarterly', 'yearly'
  created_by INTEGER,
  created_at TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id)
)
```

**Categories:** Technology, Legal, R&D, Infrastructure, Professional Services

**Methods:**
- `record_expense(date, description, amount, category, is_recurring, period)`
- `get_expenses(start_date, end_date, category=None)`
- `get_recurring_expenses()`
- `allocate_expenses_to_members(month)` → Returns dict of {user_id: allocated_amount}
- `get_gross_net_breakdown(month)` → Returns {gross_profit, total_expenses, net_profit}

**API Endpoints:**
- `POST /api/expenses/record`
- `GET /api/expenses/list`
- `GET /api/expenses/allocation/{month}`
- `POST /api/expenses/recurring`
- `DELETE /api/expenses/{id}`

---

### **Phase 8: Fund Rules**

**Database:**
```sql
CREATE TABLE fund_rules (
  id INTEGER PRIMARY KEY,
  category TEXT NOT NULL,  -- 'withdrawal', 'capital_call', 'voting', 'distribution'
  rule_text TEXT NOT NULL,
  version INTEGER DEFAULT 1,
  effective_date DATE NOT NULL,
  created_by INTEGER,
  created_at TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id)
)

CREATE TABLE rule_history (
  id INTEGER PRIMARY KEY,
  rule_id INTEGER,
  old_text TEXT,
  new_text TEXT,
  changed_by INTEGER,
  changed_at TIMESTAMP,
  FOREIGN KEY (rule_id) REFERENCES fund_rules(id),
  FOREIGN KEY (changed_by) REFERENCES users(id)
)
```

**Methods:**
- `get_current_rules()` → Returns all active rules by category
- `update_rule(rule_id, new_text, changed_by)` → Updates rule, logs history
- `get_rule_history(rule_id)` → Returns version history

**API Endpoints:**
- `GET /api/fund-rules/all`
- `POST /api/fund-rules/update` (admin only)
- `GET /api/fund-rules/history/{rule_id}`

---

### **Phase 9: Documents Management**

**Database:**
```sql
CREATE TABLE documents (
  id INTEGER PRIMARY KEY,
  filename TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  file_path TEXT NOT NULL,
  category TEXT NOT NULL,  -- 'tax', 'report', 'legal', 'agreement', 'other'
  file_size INTEGER,
  mime_type TEXT,
  uploaded_by INTEGER,
  uploaded_at TIMESTAMP,
  version INTEGER DEFAULT 1,
  is_active BOOLEAN DEFAULT 1,
  FOREIGN KEY (uploaded_by) REFERENCES users(id)
)

CREATE TABLE document_downloads (
  id INTEGER PRIMARY KEY,
  document_id INTEGER,
  user_id INTEGER,
  downloaded_at TIMESTAMP,
  FOREIGN KEY (document_id) REFERENCES documents(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
)
```

**Methods:**
- `upload_document(file, category, uploaded_by)` → Saves file, returns doc_id
- `get_documents(category=None)` → Lists documents
- `get_document_path(doc_id)` → Returns file path for download
- `delete_document(doc_id, deleted_by)` → Soft delete
- `log_download(doc_id, user_id)`

**API Endpoints:**
- `POST /api/documents/upload`
- `GET /api/documents/list`
- `GET /api/documents/download/{doc_id}`
- `DELETE /api/documents/{doc_id}` (admin only)
- `GET /api/documents/audit/{doc_id}` (download history)

---

### **Phase 10: Checklist System**

**Database:**
```sql
CREATE TABLE checklist_items (
  id INTEGER PRIMARY KEY,
  type TEXT NOT NULL,  -- 'roadmap' or 'daily'
  category TEXT,  -- For roadmap: 'legal', 'tech', 'capital', 'team', 'trading', 'marketing'
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'not_started',  -- 'not_started', 'in_progress', 'complete', 'blocked'
  assigned_to INTEGER,
  deadline DATE,
  depends_on INTEGER,  -- ID of another task (dependency)
  created_by INTEGER,
  created_at TIMESTAMP,
  completed_at TIMESTAMP,
  completed_by INTEGER,
  FOREIGN KEY (assigned_to) REFERENCES users(id),
  FOREIGN KEY (depends_on) REFERENCES checklist_items(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  FOREIGN KEY (completed_by) REFERENCES users(id)
)

CREATE TABLE checklist_notes (
  id INTEGER PRIMARY KEY,
  item_id INTEGER,
  note_text TEXT,
  created_by INTEGER,
  created_at TIMESTAMP,
  FOREIGN KEY (item_id) REFERENCES checklist_items(id),
  FOREIGN KEY (created_by) REFERENCES users(id)
)

CREATE TABLE daily_checklist_template (
  id INTEGER PRIMARY KEY,
  time TEXT NOT NULL,  -- '08:00', '09:00', etc.
  title TEXT NOT NULL,
  description TEXT,
  sort_order INTEGER
)
```

**Methods:**
- `create_checklist_item(type, category, title, assigned_to, deadline, depends_on)`
- `update_item_status(item_id, status, user_id)`
- `get_roadmap_items(category=None, status=None)`
- `generate_daily_checklist()` → Creates today's checklist from template
- `get_todays_checklist()`
- `check_item(item_id, user_id, completed=True)`
- `add_note(item_id, note_text, user_id)`

**API Endpoints:**
- `POST /api/checklist/roadmap/create`
- `POST /api/checklist/roadmap/update`
- `GET /api/checklist/roadmap`
- `GET /api/checklist/daily`
- `POST /api/checklist/daily/check`
- `POST /api/checklist/notes/add`

---

### **Phase 11: Message Center**

**Database:**
```sql
CREATE TABLE message_threads (
  id INTEGER PRIMARY KEY,
  thread_type TEXT NOT NULL,  -- 'system', 'claude', 'team', 'reminders', 'votes'
  title TEXT NOT NULL,
  created_at TIMESTAMP
)

CREATE TABLE messages (
  id INTEGER PRIMARY KEY,
  thread_id INTEGER,
  sender_id INTEGER,  -- NULL for system/claude messages
  sender_type TEXT,  -- 'user', 'system', 'claude'
  message_text TEXT NOT NULL,
  is_read BOOLEAN DEFAULT 0,
  created_at TIMESTAMP,
  FOREIGN KEY (thread_id) REFERENCES message_threads(id),
  FOREIGN KEY (sender_id) REFERENCES users(id)
)

CREATE TABLE message_reads (
  id INTEGER PRIMARY KEY,
  message_id INTEGER,
  user_id INTEGER,
  read_at TIMESTAMP,
  FOREIGN KEY (message_id) REFERENCES messages(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
)
```

**Service Class:**
```python
class MessageService:
    def send_system_message(thread_type, message_text)
    def send_user_message(user_id, thread_type, message_text)
    def get_thread_messages(thread_type, limit=50)
    def get_unread_count(user_id, thread_type=None)
    def mark_read(message_id, user_id)
    def auto_log_trading_event(event_type, details)
```

**Auto-Generated Messages:**
- Trading paused (daily limit hit)
- Positions closed (end of day)
- API disconnect/reconnect
- EOD report complete

**API Endpoints:**
- `GET /api/messages/threads`
- `GET /api/messages/{thread_type}`
- `POST /api/messages/send`
- `POST /api/messages/mark-read`
- `GET /api/messages/unread-count`

---

### **Phase 12: Claude AI Integration**

**Service Class:**
```python
class ClaudeAdvisorService:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def get_context(self):
        """Build context from database for Claude"""
        # Total capital, cofounders, ownership
        # Recent performance (today, week, month)
        # Trading parameters
        # Historical patterns
    
    def ask_question(self, question, user_id):
        """User asks Claude a question"""
    
    def generate_proactive_insight(self):
        """Claude analyzes current state and sends insight"""
    
    def analyze_eod_performance(self):
        """After EOD, Claude sends performance summary"""
    
    def check_risk_alerts(self):
        """During trading, check for risk conditions"""
```

**Scheduled Tasks:**
- Hourly during trading: Generate proactive insights
- After EOD: Performance summary
- Every 30 min: Risk check

**API Endpoints:**
- `POST /api/claude/ask`
- `POST /api/claude/generate-insight` (internal trigger)

---

### **Phase 13: Voting System**

**Database:**
```sql
CREATE TABLE proposals (
  id INTEGER PRIMARY KEY,
  proposal_type TEXT NOT NULL,  -- 'rule_change', 'expense', 'parameter_change', 'new_member', 'withdrawal'
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  vote_threshold REAL NOT NULL,  -- 0.51 (51%), 0.67 (67%), etc.
  created_by INTEGER,
  created_at TIMESTAMP,
  voting_closes_at TIMESTAMP,
  status TEXT DEFAULT 'open',  -- 'open', 'passed', 'failed'
  FOREIGN KEY (created_by) REFERENCES users(id)
)

CREATE TABLE votes (
  id INTEGER PRIMARY KEY,
  proposal_id INTEGER,
  user_id INTEGER,
  vote TEXT NOT NULL,  -- 'approve', 'reject', 'abstain'
  voted_at TIMESTAMP,
  FOREIGN KEY (proposal_id) REFERENCES proposals(id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE(proposal_id, user_id)
)
```

**Methods:**
- `create_proposal(type, title, description, threshold, created_by, closes_at)`
- `cast_vote(proposal_id, user_id, vote)`
- `get_proposal_results(proposal_id)` → {approve_count, reject_count, approve_pct, status}
- `close_proposal(proposal_id)` → Checks if passed/failed, updates status
- `get_active_proposals()`
- `get_proposal_history()`

**Auto-Actions:**
- On proposal creation → Send message to Message Center (Votes thread)
- On vote cast → Update message with vote count
- On close → Send results message

**API Endpoints:**
- `POST /api/votes/create-proposal`
- `POST /api/votes/cast`
- `GET /api/votes/active`
- `GET /api/votes/results/{proposal_id}`
- `GET /api/votes/history`

---

### **Phase 14: Performance Analytics**

**Methods to Add:**

```python
# backend/reports/performance_analyzer.py

class PerformanceAnalyzer:
    def get_fund_health(self, days=30):
        """Equity curve, win rate trends, risk metrics"""
    
    def compare_strategies(self, days=30):
        """Compare 7 forecasts: accuracy, performance"""
    
    def get_stock_history(self):
        """All stocks traded since launch, per-stock metrics"""
    
    def get_best_worst_stocks(self, limit=10):
        """Top/bottom performers"""
    
    def get_strategy_accuracy(self, forecast_key):
        """Forecast vs actual comparison"""
```

**API Endpoints:**
- `GET /api/performance/fund-health`
- `GET /api/performance/strategy-comparison`
- `GET /api/performance/stock-history`
- `GET /api/performance/best-stocks`
- `GET /api/performance/worst-stocks`

---

### **Phase 15: Email & SMS Services**

**Configure:**
- SendGrid API key
- Twilio API key

**Email Templates:**
- Invitation email
- Monthly statement (with PDF attachment)
- Daily EOD summary
- Risk alert
- Vote notification

**SMS Templates:**
- Phone verification code
- Risk alert (daily limit approaching)
- Vote reminder

**Methods:**
- `send_invitation_email(email, first_name, invite_token)`
- `send_monthly_statement(user_id, pdf_path)`
- `send_eod_summary(user_id, summary_data)`
- `send_verification_code(phone_number, code)`
- `send_risk_alert(user_id, alert_message)`

---

### **Phase 16: Monthly Statement PDF Generation**

**Library:** ReportLab

**Method:**
```python
def generate_monthly_statement_pdf(user_id, month):
    """
    Generates PDF with:
    - Header (fund name, user name, month)
    - Opening balance
    - Contributions
    - Distributions
    - Gross profit
    - Allocated expenses
    - Net profit
    - Closing balance
    - Ownership %
    - Footer (signature line)
    
    Returns: PDF file path
    """
```

**Schedule:** Auto-generate on 1st of month, email to all members

---

## 🎯 **BACKEND BUILD ORDER**

**Week 1-2: Financial Infrastructure**
1. Expense Management (database + methods + API)
2. Monthly Statement PDF generation
3. Email service configuration

**Week 3-4: Governance & Collaboration**
4. Fund Rules (database + methods + API)
5. Voting System (database + methods + API)
6. Message Center (database + service + API)

**Week 5-6: Productivity & AI**
7. Checklist System (database + methods + API)
8. Claude AI Integration (service + API)
9. Documents Management (database + file handling + API)

**Week 7-8: Analytics & Polish**
10. Performance Analytics (methods + API)
11. SMS service configuration
12. Backend testing & optimization

---
**The following phases address VPN setup and the Front End work we need to finish. Front end suggestions are not complete and we will need to vet with what we already have suggested in backend code and alpha hmtl files.**

## **PHASE 17: Multi-User Remote Deployment**

**Purpose:** Deploy LRBF app on remote server near market for low-latency trading, accessible by multiple co-founders via web browser

---

### **Infrastructure Requirements**

**Server Specs:**
- **CPU:** 4+ cores (concurrent user handling)
- **RAM:** 8GB+ (IB Gateway + Flask + PostgreSQL)
- **Storage:** 100GB SSD (database, logs, documents)
- **Network:** 1Gbps+ connection
- **Location:** <15ms from NYSE (New York, New Jersey, Virginia)

**Recommended Providers:**

| Provider | Location | Latency | Cost/Month | Notes |
|----------|----------|---------|------------|-------|
| Equinix NY4 | Secaucus, NJ | 1-2ms | $200-500 | Industry standard |
| AWS EC2 (us-east-1) | Virginia | 5-10ms | $50-200 | Scalable, easy |
| DigitalOcean NYC3 | New York | 10-15ms | $48-96 | Simple setup |
| Vultr NJ | New Jersey | 5-10ms | $24-96 | Good value |

---

### **Database Migration (SQLite → PostgreSQL)**

**Why PostgreSQL:**
- Multi-user concurrent access
- Connection pooling
- Better performance under load
- Industry standard for production

**Migration Script:**
```python
# migrate_to_postgres.py
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

def migrate_database():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect('data/trading.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host='localhost',
        database='lrbfund',
        user='lrbf_user',
        password='secure_password'
    )
    pg_cursor = pg_conn.cursor()
    
    # Tables to migrate
    tables = [
        'users', 'sessions', 'deletion_requests', 'invitations',
        'capital_transactions', 'monthly_statements', 'audit_log',
        'daily_summaries', 'fills', 'morning_forecasts', 'system_events'
    ]
    
    for table in tables:
        print(f"Migrating {table}...")
        
        # Get SQLite data
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            continue
        
        # Get column names
        sqlite_cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in sqlite_cursor.fetchall()]
        
        # Insert into PostgreSQL
        insert_query = f"""
            INSERT INTO {table} ({','.join(columns)})
            VALUES %s
        """
        execute_values(pg_cursor, insert_query, rows)
        
        print(f"  ✅ Migrated {len(rows)} rows")
    
    pg_conn.commit()
    print("\n✅ Migration complete!")

if __name__ == '__main__':
    migrate_database()
```

**PostgreSQL Setup:**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE lrbfund;
CREATE USER lrbf_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE lrbfund TO lrbf_user;
\q
EOF
```

---

### **Server Setup Script**

**`deploy_server.sh`:**
```bash
#!/bin/bash
set -e

echo "🚀 LRBF Fund - Server Deployment"
echo "================================"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt install -y \
    python3 python3-pip python3-venv \
    postgresql postgresql-contrib \
    nginx \
    git \
    ufw \
    htop \
    certbot python3-certbot-nginx

# Clone repository
echo "📂 Cloning LRBF repository..."
cd /home/ubuntu
git clone https://github.com/fromnineteen80/LRBF.git
cd LRBF

# Create virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Setup PostgreSQL
echo "🗄️ Setting up PostgreSQL..."
sudo -u postgres psql << EOF
CREATE DATABASE lrbfund;
CREATE USER lrbf_user WITH PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE lrbfund TO lrbf_user;
\q
EOF

# Create .env file
echo "⚙️ Creating environment configuration..."
cat > .env << EOF
FLASK_ENV=production
DATABASE_URL=postgresql://lrbf_user:${DB_PASSWORD}@localhost/lrbfund
SECRET_KEY=${SECRET_KEY}
IBKR_HOST=localhost
IBKR_PORT=4002
SENDGRID_API_KEY=${SENDGRID_API_KEY}
TWILIO_SID=${TWILIO_SID}
TWILIO_TOKEN=${TWILIO_TOKEN}
CLAUDE_API_KEY=${CLAUDE_API_KEY}
EOF

# Run database migrations
echo "🔄 Running database migrations..."
python migrate_to_postgres.py

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/lrbf.service > /dev/null << EOF
[Unit]
Description=LRBF Fund Application
After=network.target postgresql.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/LRBF
Environment="PATH=/home/ubuntu/LRBF/venv/bin"
ExecStart=/home/ubuntu/LRBF/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/lrbf > /dev/null << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME};

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /home/ubuntu/LRBF/frontend/static;
        expires 30d;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/lrbf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Configure firewall
echo "🔒 Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Start services
echo "▶️ Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable lrbf
sudo systemctl start lrbf

# Setup SSL (optional, requires domain)
if [ ! -z "${DOMAIN_NAME}" ]; then
    echo "🔐 Setting up SSL certificate..."
    sudo certbot --nginx -d ${DOMAIN_NAME} --non-interactive --agree-tos -m admin@${DOMAIN_NAME}
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Access your app at: http://${DOMAIN_NAME}"
echo "📊 Monitor logs: sudo journalctl -u lrbf -f"
echo "🔄 Restart service: sudo systemctl restart lrbf"
```

**Usage:**
```bash
# Set environment variables
export DB_PASSWORD="your_secure_password"
export SECRET_KEY="your_secret_key"
export DOMAIN_NAME="lrbfund.com"  # Optional
export SENDGRID_API_KEY="..."
export TWILIO_SID="..."
export TWILIO_TOKEN="..."
export CLAUDE_API_KEY="..."

# Run deployment
chmod +x deploy_server.sh
./deploy_server.sh
```

---

### **VPN Setup (WireGuard)**

**`setup_vpn.sh`:**
```bash
#!/bin/bash
set -e

echo "🔒 Setting up WireGuard VPN"
echo "==========================="

# Install WireGuard
sudo apt install -y wireguard

# Generate server keys
cd /etc/wireguard
umask 077
wg genkey | tee server_private.key | wg pubkey > server_public.key

SERVER_PRIVATE_KEY=$(cat server_private.key)
SERVER_PUBLIC_KEY=$(cat server_public.key)

# Configure WireGuard
sudo tee /etc/wireguard/wg0.conf > /dev/null << EOF
[Interface]
PrivateKey = ${SERVER_PRIVATE_KEY}
Address = 10.0.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Peer 1 (Co-founder 1)
[Peer]
PublicKey = PEER1_PUBLIC_KEY
AllowedIPs = 10.0.0.2/32

# Peer 2 (Co-founder 2)
[Peer]
PublicKey = PEER2_PUBLIC_KEY
AllowedIPs = 10.0.0.3/32

# Add more peers as needed
EOF

# Enable IP forwarding
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Start VPN
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

# Allow VPN through firewall
sudo ufw allow 51820/udp

echo ""
echo "✅ VPN setup complete!"
echo ""
echo "Server Public Key: ${SERVER_PUBLIC_KEY}"
echo ""
echo "Client configuration template:"
echo "------------------------------"
cat << EOF
[Interface]
PrivateKey = CLIENT_PRIVATE_KEY
Address = 10.0.0.2/32

[Peer]
PublicKey = ${SERVER_PUBLIC_KEY}
Endpoint = YOUR_SERVER_IP:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
EOF
```

**Client Setup (Co-founder's Computer):**
```bash
# Install WireGuard
# Mac: brew install wireguard-tools
# Windows: Download from wireguard.com
# Linux: sudo apt install wireguard

# Generate client keys
wg genkey | tee client_private.key | wg pubkey > client_public.key

# Create config file
sudo tee /etc/wireguard/wg0.conf > /dev/null << EOF
[Interface]
PrivateKey = CLIENT_PRIVATE_KEY
Address = 10.0.0.2/32

[Peer]
PublicKey = SERVER_PUBLIC_KEY
Endpoint = SERVER_IP:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
EOF

# Connect
sudo wg-quick up wg0

# Access app
# Go to: http://10.0.0.1:5000
```

---

### **IB Gateway Setup**

**`setup_ibkr.sh`:**
```bash
#!/bin/bash
set -e

echo "📈 Installing IB Gateway"
echo "======================="

# Download IB Gateway (headless version)
cd /tmp
wget https://download2.interactivebrokers.com/installers/ibgateway/latest-standalone/ibgateway-latest-standalone-linux-x64.sh

# Install
chmod +x ibgateway-latest-standalone-linux-x64.sh
sudo ./ibgateway-latest-standalone-linux-x64.sh -q

# Create systemd service
sudo tee /etc/systemd/system/ibgateway.service > /dev/null << EOF
[Unit]
Description=Interactive Brokers Gateway
After=network.target

[Service]
Type=forking
User=ubuntu
ExecStart=/opt/ibgateway/ibgateway -inline
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start IB Gateway
sudo systemctl daemon-reload
sudo systemctl enable ibgateway
sudo systemctl start ibgateway

echo "✅ IB Gateway installed"
echo "⚠️ Manual step: Log into IB Gateway and enable API access"
```

---

### **Monitoring & Logging**

**`setup_monitoring.sh`:**
```bash
#!/bin/bash
set -e

echo "📊 Setting up monitoring"
echo "======================="

# Create log directories
sudo mkdir -p /var/log/lrbf
sudo chown ubuntu:ubuntu /var/log/lrbf

# Configure log rotation
sudo tee /etc/logrotate.d/lrbf > /dev/null << EOF
/var/log/lrbf/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload lrbf > /dev/null 2>&1 || true
    endscript
}
EOF

# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Create health check script
tee /home/ubuntu/health_check.sh > /dev/null << 'EOF'
#!/bin/bash
# Check LRBF service
systemctl is-active --quiet lrbf || echo "❌ LRBF service down"

# Check IB Gateway
systemctl is-active --quiet ibgateway || echo "❌ IB Gateway down"

# Check PostgreSQL
systemctl is-active --quiet postgresql || echo "❌ PostgreSQL down"

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️ Disk usage at ${DISK_USAGE}%"
fi

# Check memory
MEM_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "⚠️ Memory usage at ${MEM_USAGE}%"
fi

echo "✅ All systems operational"
EOF

chmod +x /home/ubuntu/health_check.sh

# Add to cron (check every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/health_check.sh >> /var/log/lrbf/health.log 2>&1") | crontab -

echo "✅ Monitoring configured"
```

---

### **Backup Strategy**

**`setup_backups.sh`:**
```bash
#!/bin/bash
set -e

echo "💾 Setting up automated backups"
echo "==============================="

# Create backup directory
sudo mkdir -p /backups/lrbf
sudo chown ubuntu:ubuntu /backups/lrbf

# Database backup script
tee /home/ubuntu/backup_database.sh > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/lrbf"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/lrbfund_$DATE.sql.gz"

# Backup PostgreSQL
pg_dump -U lrbf_user lrbfund | gzip > $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "✅ Database backup complete: $BACKUP_FILE"
EOF

chmod +x /home/ubuntu/backup_database.sh

# Schedule daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backup_database.sh >> /var/log/lrbf/backup.log 2>&1") | crontab -

# Optional: Sync to cloud storage
# Install rclone for cloud backup
curl https://rclone.org/install.sh | sudo bash

echo "✅ Backup system configured"
echo "⚠️ Configure rclone for off-site backups: rclone config"
```

---

### **SSL Certificate Setup**

**Automatic (Let's Encrypt):**
```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate (interactive)
sudo certbot --nginx -d lrbfund.com

# Auto-renewal (runs twice daily)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

**Manual (Custom Certificate):**
```bash
# If you have your own SSL certificate
sudo cp your_certificate.crt /etc/ssl/certs/lrbf.crt
sudo cp your_private.key /etc/ssl/private/lrbf.key

# Update Nginx config
sudo tee -a /etc/nginx/sites-available/lrbf > /dev/null << EOF
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/lrbf.crt;
    ssl_certificate_key /etc/ssl/private/lrbf.key;
EOF

sudo systemctl restart nginx
```

---

### **Flask Configuration for Production**

**`config/production.py`:**
```python
import os

class ProductionConfig:
    """Production configuration"""
    
    # Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 1800
    
    # Session
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # IBKR
    IBKR_HOST = os.getenv('IBKR_HOST', 'localhost')
    IBKR_PORT = int(os.getenv('IBKR_PORT', 4002))
    IBKR_CLIENT_ID = int(os.getenv('IBKR_CLIENT_ID', 1))
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "redis://localhost:6379"
```

**Update `app.py`:**
```python
import os
from flask import Flask

app = Flask(__name__)

# Load config based on environment
if os.getenv('FLASK_ENV') == 'production':
    app.config.from_object('config.production.ProductionConfig')
else:
    app.config.from_object('config.development.DevelopmentConfig')
```

---

### **Deployment Checklist**

**Pre-Deployment:**
- [ ] Server provisioned (DigitalOcean, AWS, etc.)
- [ ] Domain name purchased (optional)
- [ ] DNS A record pointed to server IP
- [ ] API keys obtained (SendGrid, Twilio, Claude)
- [ ] IB Gateway credentials ready

**Deployment Steps:**
1. [ ] Run `deploy_server.sh`
2. [ ] Run `setup_vpn.sh` (if using VPN)
3. [ ] Run `setup_ibkr.sh`
4. [ ] Run `setup_monitoring.sh`
5. [ ] Run `setup_backups.sh`
6. [ ] Test from co-founder computer
7. [ ] Configure SSL certificate
8. [ ] Run health check: `./health_check.sh`

**Post-Deployment:**
- [ ] Create admin user account
- [ ] Test login from multiple devices
- [ ] Verify IB Gateway connection
- [ ] Test trading functionality
- [ ] Verify database backups working
- [ ] Set up monitoring alerts
- [ ] Document server access credentials

---

### **Maintenance Commands**

**View Logs:**
```bash
# Application logs
sudo journalctl -u lrbf -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# IB Gateway logs
sudo journalctl -u ibgateway -f
```

**Restart Services:**
```bash
# Restart Flask app
sudo systemctl restart lrbf

# Restart Nginx
sudo systemctl restart nginx

# Restart PostgreSQL
sudo systemctl restart postgresql

# Restart IB Gateway
sudo systemctl restart ibgateway
```

**Update Application:**
```bash
cd /home/ubuntu/LRBF
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart lrbf
```

---

### **User Access Instructions**

**Document for Co-Founders:**

**Option A: VPN Access**
1. Install WireGuard: [wireguard.com/install](https://www.wireguard.com/install/)
2. Save client config file as `lrbf.conf`
3. Import config into WireGuard
4. Connect to VPN
5. Open browser → `http://10.0.0.1:5000`
6. Login with credentials

**Option B: Direct HTTPS Access**
1. Open browser
2. Go to `https://lrbfund.com`
3. Login with credentials
4. Enable 2FA (SMS verification)

---

### **Security Hardening**

**Additional Steps:**
```bash
# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Install fail2ban (prevents brute force)
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Enable automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

### **Cost Summary**

**Monthly Costs:**
- Server: $48-96 (DigitalOcean 4GB RAM, 2 CPU)
- Domain: $1/month ($12/year)
- Backups: $5-10 (100GB storage)
- VPN: Free (WireGuard self-hosted)
- SSL: Free (Let's Encrypt)

**Total: $55-110/month**

**One-Time Costs:**
- Domain registration: $12/year
- Setup time: ~4 hours

---

## **FRONTEND REBUILD PHASES**

*All existing .html files are alpha prototypes and will be completely rebuilt with Material Design 3*

---

### **Phase 18: Core Trading Dashboards**

**Pages to Build:**
1. `/morning` - Morning Report
2. `/railyard` - Railyard (Live Monitor in alpha)
3. `/eod` - EOD Report

---

#### **Phase 18A: Morning Report Page**

**Purpose:** Daily stock selection, 7 forecasts, time profiles, news screening

**Components:**

**1. Header Section:**
```html
<div class="morning-header">
    <h1>Morning Report</h1>
    <div class="date-status">
        <span class="date">Wednesday, October 30, 2025</span>
        <span class="market-status">Market Opens in 45 minutes</span>
    </div>
</div>
```

**2. Selected Stocks (user selects 8, 12, 16, or 20 stocks with 4 backup Stocks):**
```html
<md-card class="selected-stocks">
    <h2>Today's Selected Stocks</h2>
    <div class="stocks-grid">
        <!-- Repeat for 8 stocks -->
        <div class="stock-card">
            <div class="stock-header">
                <span class="ticker">AAPL</span>
                <span class="price">$175.23</span>
            </div>
            <div class="stock-metrics">
                <span>Expected Patterns: 12</span>
                <span>Win Rate: 68%</span>
                <span>Expected P&L: $142</span>
            </div>
        </div>
    </div>
</md-card>
```

**3. Forecast Tabs (7 Variables for Strategy 1, our 3-Step Geomeric, and Strategy 2, our VWAP Breakout):**
```html
<md-tabs>
    <md-tab label="Default" active></md-tab>
    <md-tab label="Conservative"></md-tab>
    <md-tab label="Aggressive"></md-tab>
    <md-tab label="Choppy"></md-tab>
    <md-tab label="Trending"></md-tab>
    <md-tab label="A/B Test"></md-tab>
    <md-tab label="VWAP Breakout"></md-tab>
</md-tabs>

<div class="forecast-content">
    <div class="forecast-summary">
        <div class="metric">
            <span class="label">Expected Trades</span>
            <span class="value">80-120</span>
        </div>
        <div class="metric">
            <span class="label">Expected P&L</span>
            <span class="value">$600-$1,200</span>
        </div>
        <div class="metric">
            <span class="label">Deployed Capital</span>
            <span class="value">$24,000 (80%)</span>
        </div>
    </div>
</div>
```

**4. Time Profiles (Hourly Breakdown):**
```html
<md-card class="time-profiles">
    <h3>Intraday Activity Profile</h3>
    <canvas id="timeProfileChart"></canvas>
    <table class="profile-table">
        <thead>
            <tr>
                <th>Hour</th>
                <th>Expected Signals</th>
                <th>Typical Win Rate</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>9:30-10:30</td>
                <td>18-22</td>
                <td>65%</td>
            </tr>
            <!-- More hours -->
        </tbody>
    </table>
</md-card>
```

**5. News Screening:**
```html
<md-card class="news-screening">
    <h3>News & Earnings Calendar</h3>
    <div class="news-items">
        <div class="news-item alert">
            <md-icon>warning</md-icon>
            <div class="news-content">
                <span class="stock">AAPL</span>
                <span class="event">Earnings Report 4:00 PM</span>
                <span class="action">Consider removing from selected 8</span>
            </div>
        </div>
    </div>
</md-card>
```

**6. Backup Stocks:**
```html
<md-card class="backup-stocks">
    <h3>Backup Stocks (If Replacement Needed)</h3>
    <div class="backup-list">
        <div class="backup-stock">
            <span class="ticker">MSFT</span>
            <span class="score">Score: 8.2/10</span>
            <md-button>Use This</md-button>
        </div>
        <!-- More backups -->
    </div>
</md-card>
```

**7. Generate Button:**
```html
<div class="actions">
    <md-button class="generate-btn" onclick="generateMorningReport()">
        <md-icon>refresh</md-icon>
        Regenerate Report
    </md-button>
    <md-button class="export-btn" onclick="exportPrompts()">
        <md-icon>download</md-icon>
        Export Prompts
    </md-button>
</div>
```

**API Integration:**
```javascript
async function loadMorningReport() {
    const response = await fetch('/api/morning/data');
    const data = await response.json();
    
    // Populate selected stocks
    renderStocks(data.selected_stocks);
    
    // Populate forecasts
    renderForecasts(data.all_forecasts);
    
    // Populate time profiles
    renderTimeProfiles(data.time_profiles);
    
    // Populate news
    renderNews(data.news_screening);
}
```

---

#### **Phase 18B: Railyard Page (Live Monitor in alpha)**

**Purpose:** Real-time trading monitoring, positions, P&L tracking vs forecast

**Components:**

**1. Live Header:**
```html
<div class="live-header">
    <h1>Live Trading Monitor</h1>
    <div class="time-info">
        <span class="current-time">10:45:23 AM</span>
        <span class="market-status live">Market Open</span>
    </div>
</div>
```

**2. Real-Time Metrics:**
```html
<div class="metrics-grid">
    <md-card class="metric-card">
        <span class="label">Trades Today</span>
        <span class="value">42</span>
        <span class="forecast">Expected: 80-120</span>
        <div class="progress-bar">
            <div class="progress" style="width: 35%"></div>
        </div>
    </md-card>
    
    <md-card class="metric-card">
        <span class="label">Realized P&L</span>
        <span class="value positive">+$384.50</span>
        <span class="forecast">Expected: $600-$1,200</span>
    </md-card>
    
    <md-card class="metric-card">
        <span class="label">Win Rate</span>
        <span class="value">67%</span>
        <span class="forecast">Expected: 65%</span>
    </md-card>
    
    <md-card class="metric-card">
        <span class="label">Account Balance</span>
        <span class="value">$30,384.50</span>
        <span class="change">+1.28% today</span>
    </md-card>
</div>
```

**3. Active Positions:**
```html
<md-card class="active-positions">
    <h3>Active Positions</h3>
    <table>
        <thead>
            <tr>
                <th>Ticker</th>
                <th>Entry</th>
                <th>Current</th>
                <th>P&L</th>
                <th>Time</th>
            </tr>
        </thead>
        <tbody id="positions-table">
            <tr>
                <td>AAPL</td>
                <td>$175.20</td>
                <td>$175.85</td>
                <td class="positive">+$6.50</td>
                <td>2m 34s</td>
            </tr>
        </tbody>
    </table>
</md-card>
```

**4. Recent Fills:**
```html
<md-card class="recent-fills">
    <h3>Recent Fills (Last 20)</h3>
    <div class="fills-list">
        <div class="fill-item win">
            <span class="time">10:43:15</span>
            <span class="ticker">MSFT</span>
            <span class="action">BUY → SELL</span>
            <span class="pl">+$12.30</span>
        </div>
        <!-- More fills -->
    </div>
</md-card>
```

**5. Risk Monitor:**
```html
<md-card class="risk-monitor">
    <h3>Risk Monitor</h3>
    <div class="risk-item">
        <span class="label">Daily Loss Limit</span>
        <div class="progress-bar">
            <div class="progress green" style="width: 5%"></div>
        </div>
        <span class="value">-$45 / -$450 limit</span>
    </div>
    
    <div class="risk-item">
        <span class="label">Deployed Capital</span>
        <span class="value">$24,000 / $30,000 (80%)</span>
    </div>
</md-card>
```

**6. Auto-Refresh:**
```javascript
// Refresh every 5 seconds
setInterval(async () => {
    const response = await fetch('/api/live/data');
    const data = await response.json();
    
    updateMetrics(data.metrics);
    updatePositions(data.positions);
    updateFills(data.recent_fills);
    updateRisk(data.risk);
}, 5000);
```

---

#### **Phase 18C: EOD Report Page**

**Purpose:** Daily summary, performance analysis, charts, stock breakdown

**Components:**

**1. EOD Header:**
```html
<div class="eod-header">
    <h1>End of Day Report</h1>
    <div class="date-nav">
        <md-icon-button onclick="prevDay()">chevron_left</md-icon-button>
        <span class="date">Wednesday, October 30, 2025</span>
        <md-icon-button onclick="nextDay()">chevron_right</md-icon-button>
    </div>
</div>
```

**2. Daily Summary:**
```html
<div class="summary-grid">
    <md-card class="summary-card highlight">
        <h3>Daily ROI</h3>
        <span class="value big">+3.2%</span>
        <span class="detail">$960 profit</span>
    </md-card>
    
    <md-card class="summary-card">
        <h3>Total Trades</h3>
        <span class="value">94</span>
        <span class="forecast">Expected: 80-120</span>
    </md-card>
    
    <md-card class="summary-card">
        <h3>Win Rate</h3>
        <span class="value">68%</span>
        <span class="detail">64 wins, 30 losses</span>
    </md-card>
    
    <md-card class="summary-card">
        <h3>Account Balance</h3>
        <span class="value">$30,960</span>
        <span class="detail">Opening: $30,000</span>
    </md-card>
</div>
```

**3. Equity Curve Chart:**
```html
<md-card class="chart-card">
    <h3>Equity Curve (Last 30 Days)</h3>
    <canvas id="equityCurveChart"></canvas>
</md-card>
```

**4. Stock Performance Breakdown:**
```html
<md-card class="stock-performance">
    <h3>Stock Performance</h3>
    <table>
        <thead>
            <tr>
                <th>Ticker</th>
                <th>Trades</th>
                <th>Win Rate</th>
                <th>Total P&L</th>
                <th>Avg Hold Time</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>AAPL</td>
                <td>12</td>
                <td>75%</td>
                <td class="positive">+$142.50</td>
                <td>3m 21s</td>
            </tr>
            <!-- More stocks -->
        </tbody>
    </table>
</md-card>
```

**5. Risk Metrics:**
```html
<md-card class="risk-metrics">
    <h3>Risk-Adjusted Metrics</h3>
    <div class="metrics-row">
        <div class="metric">
            <span class="label">Sharpe Ratio</span>
            <span class="value">2.4</span>
        </div>
        <div class="metric">
            <span class="label">Sortino Ratio</span>
            <span class="value">3.1</span>
        </div>
        <div class="metric">
            <span class="label">Max Drawdown</span>
            <span class="value">-0.8%</span>
        </div>
    </div>
</md-card>
```

**6. Forecast vs Actual:**
```html
<md-card class="forecast-accuracy">
    <h3>Forecast vs Actual</h3>
    <div class="comparison">
        <div class="item">
            <span class="label">Trades</span>
            <span class="forecast">80-120</span>
            <span class="actual">94 ✓</span>
        </div>
        <div class="item">
            <span class="label">P&L</span>
            <span class="forecast">$600-$1,200</span>
            <span class="actual">$960 ✓</span>
        </div>
        <div class="item">
            <span class="label">Win Rate</span>
            <span class="forecast">65%</span>
            <span class="actual">68% ✓</span>
        </div>
    </div>
</md-card>
```

**7. Export Button:**
```html
<div class="actions">
    <md-button onclick="exportReport()">
        <md-icon>download</md-icon>
        Export Report (PDF)
    </md-button>
</div>
```

---

### **Phase 19: Fund Management Pages**

**Pages to Build:**
1. `/fund` - Fund overview
2. `/ledger` - Transactions & statements
3. `/profile` - User settings

---

#### **Phase 19a: Fund Page**

**Components:**

**1. Fund Overview:**
```html
<md-card class="fund-overview">
    <h2>The Luggage Room Boys Fund</h2>
    <div class="capital-display">
        <span class="label">Total Capital</span>
        <span class="value">$180,000</span>
    </div>
    <div class="stats">
        <div class="stat">
            <span class="label">Co-Founders</span>
            <span class="value">3</span>
        </div>
        <div class="stat">
            <span class="label">YTD Return</span>
            <span class="value positive">+18.2%</span>
        </div>
    </div>
</md-card>
```

**2. Co-Founders List:**
```html
<md-card class="cofounders">
    <h3>Co-Founders</h3>
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Contribution</th>
                <th>Ownership</th>
                <th>Joined</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>John Doe</td>
                <td>john@example.com</td>
                <td>$60,000</td>
                <td>33.33%</td>
                <td>Jan 2025</td>
            </tr>
            <!-- More co-founders -->
        </tbody>
    </table>
</md-card>
```

**3. Send Invitation (Admin Only):**
```html
<md-card class="send-invitation" v-if="user.role === 'admin'">
    <h3>Invite New Co-Founder</h3>
    <form @submit.prevent="sendInvite">
        <md-text-field label="First Name" v-model="invite.firstName"></md-text-field>
        <md-text-field label="Email" v-model="invite.email"></md-text-field>
        <md-button type="submit">Send Invitation</md-button>
    </form>
</md-card>
```

**4. Pending Invitations:**
```html
<md-card class="pending-invitations">
    <h3>Pending Invitations</h3>
    <div class="invitation-list">
        <div class="invitation-item">
            <span class="name">Jane Smith</span>
            <span class="email">jane@example.com</span>
            <span class="expires">Expires in 5 days</span>
        </div>
    </div>
</md-card>
```

---

#### **Phase 19b: Ledger Page**

**Components:**

**1. Personal Balance:**
```html
<md-card class="balance-card">
    <h2>Your Capital Balance</h2>
    <div class="balance-display">
        <span class="amount">$60,000</span>
        <span class="ownership">33.33% ownership</span>
    </div>
    <div class="balance-breakdown">
        <div class="item">
            <span class="label">Total Contributions</span>
            <span class="value">$60,000</span>
        </div>
        <div class="item">
            <span class="label">Total Distributions</span>
            <span class="value">$0</span>
        </div>
        <div class="item">
            <span class="label">YTD Profit/Loss</span>
            <span class="value positive">+$10,920</span>
        </div>
    </div>
</md-card>
```

**2. Transaction History:**
```html
<md-card class="transactions">
    <h3>Transaction History</h3>
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Balance After</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Jan 15, 2025</td>
                <td>Contribution</td>
                <td class="positive">+$30,000</td>
                <td>$30,000</td>
                <td>Initial investment</td>
            </tr>
            <!-- More transactions -->
        </tbody>
    </table>
</md-card>
```

**3. Gross vs Net Breakdown:**
```html
<md-card class="gross-net">
    <h3>October 2025 Statement</h3>
    <table class="breakdown-table">
        <tr>
            <td>Gross Profit</td>
            <td class="positive">+$5,400</td>
        </tr>
        <tr>
            <td>Less: Allocated Expenses</td>
            <td class="negative">-$300</td>
        </tr>
        <tr class="total">
            <td><strong>Net Profit</strong></td>
            <td class="positive"><strong>+$5,100</strong></td>
        </tr>
    </table>
</md-card>
```

**4. Monthly Statements:**
```html
<md-card class="statements">
    <h3>Monthly Statements</h3>
    <div class="statement-list">
        <div class="statement-item">
            <span class="month">October 2025</span>
            <md-button onclick="downloadStatement('2025-10')">
                <md-icon>download</md-icon>
                Download PDF
            </md-button>
        </div>
        <!-- More statements -->
    </div>
</md-card>
```

---

#### **Phase 19c: Profile Page**

**Components:**

**1. Personal Info:**
```html
<md-card class="profile-info">
    <h3>Personal Information</h3>
    <form @submit.prevent="updateProfile">
        <md-text-field label="First Name" v-model="profile.firstName"></md-text-field>
        <md-text-field label="Last Name" v-model="profile.lastName"></md-text-field>
        <md-text-field label="Email" v-model="profile.email"></md-text-field>
        <md-text-field label="Phone" v-model="profile.phone"></md-text-field>
        <md-select label="Timezone" v-model="profile.timezone">
            <md-option value="America/New_York">Eastern</md-option>
            <md-option value="America/Chicago">Central</md-option>
            <!-- More timezones -->
        </md-select>
        <md-button type="submit">Save Changes</md-button>
    </form>
</md-card>
```

**2. Change Password:**
```html
<md-card class="change-password">
    <h3>Change Password</h3>
    <form @submit.prevent="changePassword">
        <md-text-field type="password" label="Current Password" v-model="password.current"></md-text-field>
        <md-text-field type="password" label="New Password" v-model="password.new"></md-text-field>
        <md-text-field type="password" label="Confirm New Password" v-model="password.confirm"></md-text-field>
        <md-button type="submit">Update Password</md-button>
    </form>
</md-card>
```

**3. Two-Factor Authentication:**
```html
<md-card class="2fa">
    <h3>Two-Factor Authentication</h3>
    <div class="2fa-status">
        <span class="status-badge enabled">Enabled</span>
        <span class="phone">SMS: (555) 123-4567</span>
    </div>
    <md-button onclick="disable2FA()">Disable 2FA</md-button>
</md-card>
```

**4. Delete Account:**
```html
<md-card class="delete-account danger">
    <h3>Delete Account</h3>
    <p>Permanently delete your account and all associated data.</p>
    <md-button class="danger" onclick="initiateDelete()">
        Delete Account
    </md-button>
</md-card>
```

---

This does not include a base html page phase, the conversations page phase, roadmaps page phase, the user management pages phase, etc.