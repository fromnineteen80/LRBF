# LRBF Technical Reference

**Purpose:** Quick reference for what exists in the codebase  
**For workflow guidance:** Use lrbf-skill  
**Last Updated:** 2025-10-30

---

## Quick Facts

- **Repo:** fromnineteen80/LRBF
- **Framework:** Flask 3.0+
- **Database:** SQLite (dev) → PostgreSQL (prod)
- **Data Source:** IBKR API via ib_insync
- **Frontend:** Material Design 3 (alpha - will be rebuilt)

---

## Database Tables

### Core Tables
- **users** - id, username, password_hash, email, role, created_at, last_login
- **sessions** - id, user_id, session_token, expires_at, created_at
- **daily_summaries** - id, date, opening_balance, closing_balance, realized_pl, roi_pct, trade_count, win_rate, sharpe_ratio, sortino_ratio, max_drawdown_pct, stock_performance_json
- **fills** - id, ibkr_execution_id, date, timestamp, ticker, action, quantity, price, realized_pnl, commission, latency_ms, slippage_pct
- **morning_forecasts** - id, date, generated_at, selected_stocks_json, all_forecasts_json, time_profiles_json, news_screening_json, expected_trades_low, expected_trades_high, expected_pl_low, expected_pl_high, active_preset
- **system_events** - id, date, timestamp, event_type, severity, ticker, message

### Future Tables (Not Yet Created)
- invitations, fund_info, cofounders, transactions, monthly_statements, audit_log, expenses, fund_rules, documents, checklist_items, messages, proposals, votes, notification_preferences

---

## API Endpoints

### Trading (Phase 0 - In Progress)
- `GET /api/morning-data` - Morning forecast with 7 scenarios
- `GET /api/live-data` - Real-time Railyard monitoring (needs rebuild)
- `GET /api/eod-data` - End-of-day analysis (needs rebuild)

### Authentication (Phase 1 - Not Started)
- `POST /login`
- `POST /logout`
- `GET /check-session`

### System
- `GET /api/config` - Current configuration
- `POST /api/config` - Update config (admin only)
- `GET /api/ibkr-status` - IBKR connection status

### Future Endpoints
See phase descriptions in lrbf-skill for complete list

---

## Configuration (config.py)

### Capital
```python
DEPLOYMENT_RATIO = 0.80  # 80% deployed
RESERVE_RATIO = 0.20     # 20% reserve
NUM_STOCKS = 8           # Portfolio size
```

### Entry/Exit
```python
DECLINE_THRESHOLD = 1.0   # % decline to trigger pattern
ENTRY_THRESHOLD = 1.5     # % climb to confirm entry
TARGET_1 = 0.75          # First profit target
TARGET_2 = 2.0           # Second profit target
STOP_LOSS = -0.5         # Stop loss
```

### Risk
```python
DAILY_LOSS_LIMIT = -1.5  # % daily loss before auto-pause
```

### Execution
```python
COOLDOWN_MINUTES = 1
MARKET_OPEN = "09:31"
MARKET_CLOSE = "16:00"
ENTRY_CUTOFF = "15:50"
```

---

## Key Backend Modules

### Pattern Detection & Selection
- `backend/core/pattern_detector.py` - Detect 3-Step Geometric & VWAP Breakout
- `backend/core/stock_selector.py` - Select balanced portfolio
- `backend/core/forecast_generator.py` - Calculate expected performance

### Trading Execution
- `backend/core/railyard.py` - Real-time trading engine (needs overhaul)

### Reporting
- `backend/reports/morning_report.py` - Generate morning analysis
- `backend/reports/live_monitor.py` - Real-time monitoring
- `backend/reports/eod_reporter.py` - End-of-day analysis (needs overhaul)

### Data & Integration
- `backend/data/ibkr_connector.py` - IBKR API wrapper
- `backend/data/stock_universe.py` - Curated stock list
- `backend/models/database.py` - Database operations

---

## Trading Strategy Summary

**For complete details:** Read `docs/explainers/trading_strategy_explainer.md`

### Patterns
1. **3-Step Geometric:** Decline → 50% Recovery → 50% Retracement → Entry confirmation
2. **VWAP Breakout:** Drop below VWAP → Stabilize → Break above → Entry confirmation

### Exit Logic
- T1: +0.75% (lock, wait for CROSS)
- CROSS: +1.0% (lock, wait for momentum)
- Momentum: +1.25% (hold for T2)
- T2: +1.75% (exit)
- Dead zone: Adaptive timeouts based on profit level
- Stop loss: -0.5%

### Forecasts
7 presets generated each morning:
- Default, Conservative, Aggressive, Choppy Market, Trending Market, AB Test, VWAP Breakout

---

## File Structure

```
backend/
├── core/          # Pattern detection, Railyard, stock selection
├── data/          # IBKR integration, stock universe
├── models/        # Database operations
├── reports/       # Morning, live, EOD reports
└── api/           # API routes (mostly in app.py currently)

templates/         # HTML pages (alpha, will rebuild)
static/
├── css/          # Material Design 3 styles
└── js/           # Frontend logic

docs/
├── explainers/   # Trading strategy, morning report, data pipeline
├── phases/       # Phase folders (phase_0, phase_1, etc.)
└── project/      # project_state.md

app.py            # Main Flask app
config.py         # Configuration values
```

---

## Current Status

### Phase 0: Railyard + EOD Backend (In Progress)
- Morning report: ✅ Working
- Railyard: ⚠️ Needs complete overhaul
- EOD reporter: ⚠️ Needs complete overhaul
- APIs: Partial (morning-data works, live/eod need work)

### Other Phases: Not Started
- Phases 1-17: Backend features (user management, fund features)
- Phases 18-31: Frontend (deferred until backend complete)

---

## Development Notes

- **Deprecated:** Capitalise.ai, yfinance, RapidAPI (use IBKR only)
- **Frontend:** All HTML is alpha quality, will be rebuilt with MD3
- **Correct template:** `prototypes/react-dashboard.html`
- **Data flow details:** See `docs/explainers/data_pipeline_explainer.md`
- **Workflow guidance:** Use lrbf-skill

---

**For detailed phase descriptions, workflow guidance, and development rules:**  
Use lrbf-skill

**For complete strategy details:**  
Read `docs/explainers/trading_strategy_explainer.md`

**For current project state:**  
Read `docs/project/project_state.md` (via GitHub API)
