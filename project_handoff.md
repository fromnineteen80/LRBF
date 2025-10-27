LRBFund App – Continuation
Previous Session ID will be provided by user in session_log_new.md

═══════════════════════════════════════════════════════════════
CORE ARCHITECTURE
═══════════════════════════════════════════════════════════════

## Claude Environment & Access

**GitHub Workflow:**
- Token: [REDACTED - See project folder]
- Repo: fromnineteen80/LRBF
- Method: Access repo via GitHub API, edit files, git commit, git push
- NEVER read README.md in repo
- Verify commits land in user's GitHub Desktop before claiming complete

**Critical Verification:**
- Complete work = Database → API → Frontend ALL tested and integrated
- No emulation coding - if you say you built it, it must exist and work

**Sanity Check:**
1. Confirm using GitHub API via fetch()
2. If you think you need Node.js modules, STOP and ask first
3. Test environment if uncertain
4. Check build quality: eliminate duplication, ensure logic flows

**Context:**
- Always reference GitHub repo: fromnineteen80/LRBF
- Ignore outdated .md files in repo - prioritize executable code
- Material Design 3 front-end (vendored components)
- Core Python modules: morning_report.py, eod_archive.py, railyard.py
- Local dev: http://localhost:5000 (app), https://localhost:8000 (IBKR Gateway)

═══════════════════════════════════════════════════════════════
SESSION HANDOFF PROTOCOL
═══════════════════════════════════════════════════════════════

**Active Token Tracking:**
Format: ✅ Task complete. Token Status: [X]k used, [Y]k remaining

**Handoff Trigger:** 130k tokens used (60k remaining)

**When Threshold Reached:**
1. Alert: ⚠️ HANDOFF THRESHOLD REACHED
2. Generate NEW session_log_new.md using session_log_template.md structure
3. Update TECHNICAL_SPECS.md ONLY if new endpoints/features added
4. Update project_handoff.md ONLY if new APIs/integrations added
5. Provide user with updated files

**Files to Reference During Session:**
- ✅ project_handoff.md (this file - master instructions)
- ✅ TECHNICAL_SPECS.md (technical reference)
- ✅ session_log_new.md (previous session memory)
- ✅ Instructions.txt (user constraints)
- ✅ Building Railyard Markets.docx (strategy document)
- ❌ session_log_template.md (ONLY at handoff, not during work)

**CRITICAL:** Edit or add ONLY new details. Never rewrite existing content.

**Don't Repeat These Mistakes:**
- ❌ Emulation Coding (discussing without implementing)
- ❌ Phantom References (referencing non-existent files)
- ❌ Incomplete Chains (building without testing integration)
- ❌ Assumption-Based Development (assuming "discussed" = "exists")
- ❌ Marking Complete Without Testing

**Verify Before Coding:**
- [ ] Check if file exists in repo (GitHub API)
- [ ] Verify integration still works
- [ ] Confirm assumptions with user
- [ ] Test full pipeline before marking complete

═══════════════════════════════════════════════════════════════
TWO TRADING STRATEGIES
═══════════════════════════════════════════════════════════════

## Universal Entry/Exit Rules (Both Strategies)

**Entry Signal:** Price climbs +0.5% from pattern low → BUY

**Targets:**
- Target 1 (T1): +0.75% from entry
- Target 2 (T2): +1.75% from entry

**Decision Points (not exits):**
- Cross Threshold: +1.00% from entry (intermediate floor if crossed)
- Momentum Confirmation: +1.25% from entry (confirms continuation to T2)

**Exit Logic:**
- If price reaches T2 (+1.75%) → Exit at T2
- If price reaches T1, crosses +1.00%, hits +1.25% → Stay in for T2
- If price reaches T1, crosses +1.00%, never hits +1.25% → Exit at +1.00%
- If price reaches T1 but never crosses +1.00% → Exit at T1 (+0.75%)
- Stop Loss: -0.5% from entry if immediate crash

**Tiered Dead Zone Timeouts:**
- Below T1: 3 minutes (no profit locked) → Exit at break-even or +0.25%
- At T1: 4 minutes (T1 locked at +0.75%) → Exit at T1
- At Cross: 4 minutes (Cross locked at +1.00%) → Exit at Cross
- After Momentum: 6 minutes (momentum confirmed) → Exit at Cross or higher
- Dead zone detection: Stuck in ±0.6% range

**Exit Reasons:** Target1, Target2, Cross, StopLoss, DeadZoneFailed, DeadZoneT1, DeadZoneCross, DeadZoneMomentum, TimeOut, Manual
═══════════════════════════════════════════════════════════════

## STRATEGY 1: 3-Step Geometric Reversal

**Pattern Detection:**
1. Price declines 1% from recent high
2. Price recovers 50% of that decline
3. Price retraces 50% of the recovery
4. Entry signal: Price climbs +0.5% from last low

**Key Characteristic:** 
- VWAP position IGNORED during detection
- Pure geometric W-bottom reversal pattern
- Works because selling exhaustion → buyers return

**Six Filter Presets:**

### 1. Default (Baseline)
- Filters: NONE
- Win rate: 68%, Trades/day: 15-25
- Use: Baseline performance measurement

### 2. Conservative
- Filters: All ON, tight thresholds
  - VWAP proximity: ±2%, Volume: 2x, Time: avoid first/last hour, S/R required, Trend align
- Win rate: 81%, Trades/day: 8-15
- Use: Risk-averse sessions, volatile conditions

### 3. Aggressive
- Filters: Minimal
  - VWAP proximity: ±10%, Volume: 1.5x, Time: all hours
- Win rate: 65-70%, Trades/day: 20-30
- Use: High-volume days, stable markets

### 4. Choppy Market
- Filters: S/R focused
  - VWAP: ±3%, Volume: 2.5x, S/R: MUST be near levels, Trend: neutral/range
- Win rate: 75%, Trades/day: 10-18
- Use: Range-bound, low-conviction days

### 5. Trending Market
- Filters: Momentum focused
  - Trend: MUST align, VWAP: ±5%, Volume: 1.5x, Time: favor mid-day
- Win rate: 72%, Trades/day: 12-20
- Use: Clear directional trend days

### 6. AB Test
- Filters: Experimental combinations
- Win rate: TBD, Trades/day: TBD
- Use: Strategy development, testing new filter ideas

═══════════════════════════════════════════════════════════════

## STRATEGY 2: VWAP Breakout

**Pattern Detection:**
1. Price drops BELOW VWAP
2. Price stabilizes near/under VWAP for confirmation
3. Price crosses BACK ABOVE VWAP (the breakout)
4. Entry signal: Price climbs +0.5% above VWAP with volume confirmation

**Key Characteristic:**
- VWAP crossover REQUIRED during detection
- Captures institutional rebalancing toward VWAP
- Theory: Algos push price back to VWAP equilibrium
- Different opportunities than 3-Step pattern

**Filter Presets (Future):**
- Can add Conservative, Aggressive, etc. presets once base pattern proves out
- Initial implementation: Default (just the VWAP breakout, no extra filters)

**Historical Performance (Projected):**
- Win rate: ~81-85% (higher selectivity)
- Trades/day: 8-12 (fewer, higher quality)
- Lower volatility than geometric pattern

═══════════════════════════════════════════════════════════════

## Morning Report Output

**Automated 5:45 AM ET scan generates forecasts for:**

**Strategy 1 (3-Step Geometric):**
1. Default forecast
2. Conservative forecast
3. Aggressive forecast
4. Choppy Market forecast
5. Trending Market forecast
6. AB Test forecast

**Strategy 2 (VWAP Breakout):**
7. VWAP Breakout forecast (initial: default preset only)

**User Workflow:**
1. Morning report auto-generates all 7 forecasts
2. User reviews and selects: (1) Strategy, (2) Preset
3. Trading starts with selected strategy + preset
4. Can switch mid-day (all forecasts pre-computed)
5. EOD compares actual vs selected forecast

**Critical:** Each strategy detects DIFFERENT patterns, finds DIFFERENT opportunities, may select DIFFERENT stocks.

═══════════════════════════════════════════════════════════════
MORNING REPORT ARCHITECTURE
═══════════════════════════════════════════════════════════════

## Automated Daily Research Pipeline

**Schedule:** 5:45 AM ET (automated, every trading day)

**Full Pipeline (Backend → Frontend):**
1. Pull TOP 500 stocks by volume from IBKR + 20-day historical data
2. **Detect BOTH patterns across all 500 stocks:**
   - 3-Step Geometric Reversal
   - VWAP Breakout
3. Score each stock across 16 dimensions for each pattern
4. Classify into risk categories (Conservative/Medium/Aggressive)
5. **Generate 7 forecasts:**
   - Strategy 1: 6 filter presets (Default, Conservative, Aggressive, Choppy, Trending, AB Test)
   - Strategy 2: 1 VWAP Breakout forecast
6. Rank stocks by composite score FOR EACH forecast
7. Present top 1-24 stocks per forecast to user
8. User selects: (1) Strategy, (2) Preset, (3) Portfolio size (8/12/16/20)
9. System generates execution lineup for Railyard.py

**Critical: Different patterns = different opportunities**
- 3-Step finds geometric reversals (VWAP ignored)
- VWAP Breakout finds crossovers (VWAP required)
- Each may identify DIFFERENT top stocks
- All 7 pre-computed - user toggles instantly

## Stock Selection Options

**User Chooses Portfolio Size:**
- 8 stocks (recommended for lower capital)
- 12 stocks (moderate diversification)
- 16 stocks (higher diversification)
- 20 stocks (maximum coverage)

**Automatic Backup Selection:**
- Next 4 highest-ranked stocks become backups
- Used if primary stock halted, gapped, or fails quality check
- Example: User selects 8 → System presents top 8 + next 4 backups

**Risk-Balanced Portfolio:**
- 2-3 Conservative (high win rate, low frequency)
- 4-6 Medium (balanced)
- 2-3 Aggressive (high frequency, lower win rate)

## 16 Scoring Dimensions (Quality Metrics)

**Pattern Performance (6 categories - 50% total weight):**
1. **Pattern Frequency** (20%) - Occurrences per day (2-4/day target)
2. **Confirmation Rate** (10%) - % patterns that trigger entry signal
3. **Win Rate** (8%) - % profitable trades after entry
4. **Expected Value** (6%) - Net profit per trade after costs
5. **Avg Win %** (3%) - Average gain on winning trades
6. **Risk/Reward Ratio** (3%) - Win size vs loss size

**Market Quality (5 categories - 30% total weight):**
7. **Liquidity Score** (10%) - Volume + spread + order book depth
8. **Volatility Score** (8%) - ATR sweet spot (1.5%-3.5% target)
9. **Spread Quality** (5%) - Bid-ask spread tightness
10. **VWAP Stability** (4%) - Clean VWAP curve (less noise)
11. **Trend Alignment** (3%) - Price vs moving averages

**Risk Factors (3 categories - 15% total weight):**
12. **Dead Zone Risk** (5%) - % trades stuck >8 min, avg duration, opportunity cost
13. **Halt Risk** (5%) - Days to earnings, news volatility, circuit breaker history
14. **Execution Efficiency** (5%) - Slippage, latency, fill quality

**Consistency (2 categories - 5% total weight):**
15. **Backtest Consistency** (3%) - Performance stability across 20 days
16. **Composite Rank** (2%) - Weighted average of all 15 above

**Output:** Each stock receives 16 scores (0-100 scale) + 1 composite rank

## 3 Risk Categories (Classification)

**Conservative:**
- High confirmation rate (>40%)
- Low activity (1-3 patterns/day)
- Mega-caps ($100B+ market cap)
- Tight spreads (<3 bps)
- Low dead zone risk (<10%)

**Medium:**
- Moderate confirmation rate (25-40%)
- Moderate activity (2-5 patterns/day)
- Large-caps ($10B-$100B)
- Acceptable spreads (3-5 bps)
- Moderate dead zone risk (10-20%)

**Aggressive:**
- Lower confirmation rate (15-25%)
- High activity (4-8 patterns/day)
- Mid-caps ($2B-$10B)
- Wider spreads (5-10 bps)
- Higher dead zone risk (20-30%)

**Portfolio Balancing:**
- 8-stock portfolio: 2 Conservative, 4 Medium, 2 Aggressive
- 12-stock portfolio: 3 Conservative, 6 Medium, 3 Aggressive
- 16-stock portfolio: 4 Conservative, 8 Medium, 4 Aggressive
- 20-stock portfolio: 5 Conservative, 10 Medium, 5 Aggressive

## Seven-Forecast Output (Two Strategies)

**Morning report generates 7 complete forecasts (5:45 AM ET):**

**Strategy 1 - 3-Step Geometric (6 presets):**
1. Default - No filters, baseline
2. Conservative - All filters ON, risk-averse
3. Aggressive - Minimal filters, high frequency
4. Choppy Market - S/R focused for range-bound
5. Trending Market - Momentum focused for directional
6. AB Test - Experimental filter combos

**Strategy 2 - VWAP Breakout:**
7. VWAP Breakout - Default preset (crossover required)

**Each Forecast Contains:**
- Stock list (top 8-20 stocks, DIFFERENT for each)
- Expected trades (low/high range)
- Expected P&L (low/high range)
- Win rate estimate
- Risk/reward ratio
- Dead zone probability
- Deployed/reserve capital split
- Filters applied (if any)

**Frontend Presentation:**
- Strategy selector: [3-Step Geometric ▼] [VWAP Breakout]
- Preset selector (if 3-Step): [Default] [Conservative] [Aggressive] [Choppy] [Trending] [AB Test]
- Selection shows: Stock list, forecast metrics, filter details
- Live monitoring compares actual vs selected forecast
- User can switch strategy/preset mid-day (instant, pre-computed)

**User Workflow Example:**
1. 5:45 AM: Auto-generates all 7 forecasts
2. 9:00 AM: User selects "3-Step Geometric - Conservative"
3. 9:31 AM: Trading starts with Conservative stocks + filters
4. 11:00 AM: Market trends, switches to "3-Step - Trending"
5. 2:00 PM: Sees VWAP breakouts, switches to "VWAP Breakout"
6. 4:00 PM: EOD compares actual vs all 3 presets used

═══════════════════════════════════════════════════════════════
DATA SOURCES & APIS
═══════════════════════════════════════════════════════════════

## Primary Data Source: IBKR via ib_insync (Native Binary Protocol)

**Connection:** IB Gateway localhost:4002 (paper) / 4001 (live)
**Mode:** Paper (DU5697343) until production clearance
**Library:** ib_insync 0.9.86+ (industry standard, professionally maintained)
**Implementation:** backend/data/ibkr_connector.py
**Configuration:** IBKRConfig in config/config.py

**Data Types:**
- Real-time: Tick-by-tick streaming via reqMktData() (1-10ms latency, native binary)
- Historical: 20-day lookbacks, customizable intervals (1 sec to 1 day bars)
- Account: Balance, positions, P&L, margin, fills, commissions
- Universe: **TOP 500 stocks by average daily volume** (via reqScannerData())

**Key Methods:**
- get_historical_data(ticker, period_days, bar_size) - Historical bars with VWAP
- get_market_snapshot(ticker) - Real-time price snapshot
- get_top_stocks_by_volume(limit, min_volume, min_price) - Scanner for top stocks
- get_account_balance() - Account summary
- subscribe_market_data(tickers) - Real-time tick streaming (needs integration with Railyard.py)

**Update Schedule:**
- 5:45 AM ET: Pull TOP 500 stocks by volume from IBKR + 20-day historical data for each
- 9:31-16:00 ET: Tick streaming via reqMktData() (1-10ms latency, native binary protocol)
- 16:05 ET: Provisional fills
- 19:30 ET: Final fills and reconciliation

**Data Schema:**
Returns pandas DataFrames: [timestamp, open, high, low, close, volume, vwap, bid, ask]

**Testing:** Run test_ib_insync_full.py to validate connection and data pipeline

---

## User Management Web API

**Purpose:** Multi-user fund with pooled IBKR account
**Implementation:** Flask routes (app.py) + backend/modules/auth.py
**Database:** Users table with ownership tracking

**Architecture:**
- 1 IBKR account (DU5697343)
- 2 users (both co-founders)
- IBKR credentials in .env (NOT per-user)
- ALL trading data shared
- P&L allocated by ownership %

**Endpoints:**
- POST /login - Authentication
- POST /logout - Session termination
- GET /api/user/profile - User data (username, role, ownership %)
- POST /api/user/update - Update settings
- GET /api/fund/ownership - Ownership breakdown

**User Data Model:**
- username (unique), password_hash (bcrypt), email (unique)
- role (admin/member)
- fund_contribution (USD), ownership_pct (calculated)
- created_at, last_login

---

## DEPRECATED (Do NOT Use)
- ❌ RapidAPI + yfinance
- ❌ EOD Historical Data API
- ❌ Any external market data APIs
- ❌ IBKR Client Portal Web API (replaced by ib_insync native binary protocol)
- ❌ ibkr_websocket.py (deleted - ib_insync has built-in streaming)

IBKR via ib_insync is single source of truth.

---

## Future: OANDA (Forex)
- Enable FX strategy prior to equities
- Details TBD during FX onboarding

═══════════════════════════════════════════════════════════════
SECURITY & SECRETS
═══════════════════════════════════════════════════════════════

**Rule:** ALL keys/tokens in GitHub Secrets + local .env (never committed)

**Required Secrets:**
- IBKR_ACCOUNT_ID
- GH_TOKEN
- (optional) REPO_URL

**Usage:** Read via environment variables (dotenv/os.getenv)
**Files:** .env.example (public with placeholders), .env (in .gitignore)

═══════════════════════════════════════════════════════════════
DEVELOPMENT PHASES
═══════════════════════════════════════════════════════════════

1. **Architecture & Alpha Review** - Inventory alpha app, confirm data pipeline, verify repo structure
2. **Engine Transition** - Replace Capitalise.ai with railyard.py execution engine
3. **Morning Report** - IBKR integration, 16-dimension scoring, dual-forecast generation, stock universe selection
4. **Live Monitoring** - Real-time WebSocket streaming, guardrails telemetry, position tracking
5. **End-of-Day** - Final fills/fees, KPIs, ledger, model drift analysis
6. **App Surfaces** - MD3 pages (Python/JS/CSS)
7. **Management System** - Roles, auth, backend data/file/page management
8. **Premarket Checklist** - Daily ET checklist flows
9. **Simulation/Practice** - Toggle simulation mode
10. **Conversations** - In-app notifications, DM system
11. **Strategy Assistant** - Read-only API chatbot
12. **Calendar** - System and user calendars
13. **Video** - Meeting integration
14. **Chart.js Overhaul** - Sophisticated visual data language
15. **Testing** - Full integration testing, security audit

═══════════════════════════════════════════════════════════════
OBJECTIVES
═══════════════════════════════════════════════════════════════

- Production-grade modules for Morning Report, Live Monitoring, EOD Analysis
- Material Design 3 front-end (vendored components only)
- Data governance, scoring logic, risk guardrails
- Full ET-scheduled automation
- Investor-grade transparency
- Best-in-class UI/UX for quant users and fund managers

═══════════════════════════════════════════════════════════════
NOTES
═══════════════════════════════════════════════════════════════

**Material Design 3:** All front-end work uses vendored MD3 components. No emulation or shortcuts.

**Permissions:** GitHub repo fromnineteen80/LRBF may be temporarily public. Read all code before generating/editing. Ignore outdated .md files, prioritize executable code.
