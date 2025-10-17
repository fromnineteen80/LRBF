# RapidAPI Market Data - Complete Implementation Plan

**Date:** October 16, 2025
**Purpose:** Systematic integration of RapidAPI Yahoo Finance throughout entire application
**Estimated Time:** 20-30 hours across 8 weeks
**Token Budget:** ~80,000 tokens across 4-5 sessions
**Quality Standard:** Wall Street professional level with Material Design 3

---

## EXECUTIVE SUMMARY

### Current State
COMPLETED:
- RapidAPI data_provider.py module created
- batch_analyzer.py integrated with RapidAPI
- config.py has API credentials
- requirements.txt updated

NOT STARTED:
- Stock selection with N+4 backups
- Automatic morning report at 12:01 AM
- Market calendar integration
- Practice mode, Test mode
- MD3 list components
- History/Calculator/Performance pages

### What This Delivers
1. Complete Morning Report - Auto-generates at 12:01 AM with N+4 backup stocks
2. Real Market Calendar - NYSE trading days and accurate hours
3. MD3 Component Library - Reusable stock lists, cards, tables
4. Practice Mode - Per-user safe testing
5. Test Mode - 2-week simulation with KPI tracking
6. Live Data Everywhere Needed

---

## IMPLEMENTATION PHASES

### PHASE 1: Stock Selection with Backups
**Priority:** CRITICAL | **Time:** 4-6 hours | **Tokens:** 8,000

**Files:** stock_selector.py, morning_report.py, database.py, morning.html, morning.js

**Goal:** Select N primary + 4 backup stocks, display with timestamp

**Key Implementation:**
- Modify stock_selector to return {primary: [], backup: []}
- Add backup_stocks_json column to database
- Create MD3 list components for display
- Show timestamp on morning page

**Testing:**
- Generate with 8 stocks -> 8 primary + 4 backup
- Generate with 16 stocks -> 16 primary + 4 backup
- Mobile responsive

---

### PHASE 2: Automatic Morning Generation
**Priority:** CRITICAL | **Time:** 3-4 hours | **Tokens:** 6,000

**Files:** scheduler.py (NEW), market_calendar.py (NEW), app.py

**Goal:** Auto-generate at 12:01 AM on trading days

**Implementation:**
- APScheduler background task
- pandas_market_calendars for trading days
- Timezone: US/Eastern
- Manual trigger endpoint for testing

**Testing:**
- Scheduler starts with Flask
- Trading day detection works
- Generates on trading days only
- Skips weekends/holidays

---

### PHASE 3: Market Progress Bar
**Priority:** HIGH | **Time:** 2-3 hours | **Tokens:** 4,000

**Files:** base.html, market_calendar.py, market-status.js (NEW)

**Goal:** Real-time market status in header/sidebar

**Features:**
- Status indicator (open/closed/pre-market/after-hours)
- Progress bar (% through trading day)
- Time remaining display
- Updates every 30 seconds

---

### PHASE 4: MD3 Stock Components
**Priority:** CRITICAL | **Time:** 3-4 hours | **Tokens:** 7,000

**Files:** stock-components.css (NEW), stock-components.js (NEW)

**Components:**
1. Stock List Item (md-list-item with three-line layout)
2. Stock Card (md-elevated-card for details)
3. Stock Table (md-data-table for comparisons)

**Reference:** https://m3.material.io/components/lists/overview

---

### PHASE 5: Live Monitor Enhancement
**Priority:** HIGH | **Time:** 2-3 hours | **Tokens:** 5,000

**Goal:** Add RapidAPI fallback if IBKR unavailable

**Implementation:**
- Try IBKR first for live prices
- Fall back to RapidAPI if IBKR fails
- Show data source indicator

---

### PHASE 6: Practice Mode
**Priority:** HIGH | **Time:** 6-8 hours | **Tokens:** 12,000

**Files:** practice.html, practice.js, practice_session.py (NEW)

**Features:**
- User-specific practice sessions
- Configurable strategy parameters
- Historical data simulation
- Save/load sessions
- Results dashboard

**Database:**
CREATE TABLE practice_sessions (...)

---

### PHASE 7: Test Mode - 2 Week Simulation
**Priority:** MEDIUM | **Time:** 8-10 hours | **Tokens:** 15,000

**Files:** test_mode.html, test_session.py (NEW), test_runner.py (NEW)

**Features:**
- Run 10 trading days simulation
- Morning report for each day
- Simulate trades
- EOD analysis
- Calculate Sharpe/Sortino/Max Drawdown
- Forecast accuracy tracking

---

### PHASE 8: History Page
**Priority:** MEDIUM | **Time:** 4-5 hours | **Tokens:** 8,000

**Features:**
- Calendar view of trading days
- Daily summary cards
- Filter by date/ticker/win-loss
- Export to CSV
- Equity curve chart

---

### PHASE 9: Calculator Page
**Priority:** MEDIUM | **Time:** 4-5 hours | **Tokens:** 6,000

**Features:**
- Performance projections
- Use real historical win rates
- Compare scenarios
- Monte Carlo simulation (optional)

---

### PHASE 10: Performance Page
**Priority:** MEDIUM | **Time:** 5-6 hours | **Tokens:** 9,000

**Features:**
- Comprehensive dashboard
- All risk metrics
- Monthly performance table
- Best/worst days
- Per-ticker breakdown

---

## MATERIAL DESIGN 3 GUIDELINES

### Components to Use
- md-list / md-list-item - Stock lists
- md-elevated-card - Content containers
- md-chip - Categories and tags
- md-linear-progress - Loading/progress
- md-filled-button / md-outlined-button - Actions
- md-icon - Material Symbols

### Design Tokens
- --md-sys-color-primary
- --md-sys-color-surface
- --md-sys-color-error
- --md-sys-color-tertiary

### Typography
- headline-large, headline-medium
- title-large, title-medium
- body-large, body-medium
- label-large, label-medium

---

## TESTING STRATEGY

### Unit Tests
- Test data_provider functions
- Mock RapidAPI responses
- Test edge cases

### Integration Tests
- Full morning report flow
- Scheduler with mocked time
- Database transactions

### User Acceptance
1. Generate morning report (8 stocks)
2. Generate morning report (16 stocks)
3. View backup stocks
4. Download prompts
5. Run practice session
6. Start 2-week test
7. View history
8. Use calculator
9. Check performance

---

## SESSION PLANNING

**Session 1 (15K tokens):** Phases 1-2
- Stock selection with backups
- Automatic morning generation

**Session 2 (11K tokens):** Phases 3-4
- Market progress bar
- MD3 components

**Session 3 (17K tokens):** Phases 5-6
- Live monitor enhancement
- Practice mode

**Session 4 (23K tokens):** Phase 7
- Test mode (2-week simulation)

**Session 5 (15K tokens):** Phases 8-10
- History, Calculator, Performance pages

---

## DEPLOYMENT CHECKLIST

Before Production:
- [ ] All phases tested
- [ ] RapidAPI key in environment variables
- [ ] Database migrations run
- [ ] Scheduler configured
- [ ] Error logging configured
- [ ] Performance tested
- [ ] Security audit complete
- [ ] Documentation written

Railway-Specific:
- [ ] Procfile configured
- [ ] Environment variables set
- [ ] Database URL configured
- [ ] Scheduler works in production
- [ ] Logs accessible

---

## CRITICAL REMINDERS

1. RapidAPI Rate Limits - Free tier: 500 requests/month
2. Market Calendar - Always use pandas_market_calendars
3. Timezone - Everything in US/Eastern
4. Data Persistence - Morning forecast must persist
5. Error Handling - Never expose API keys
6. Mobile Responsive - Test on actual devices

---

**Document Version:** 1.0
**Created:** October 16, 2025
**Next Step:** Begin Phase 1 - Stock Selection with Backups
**Author:** The Luggage Room Boys Fund Development Team
