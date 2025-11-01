# Phase 0 Requirements - DRAFT

**Status:** DRAFT - Awaiting User Review  
**Created:** 2025-10-31  
**Last Updated:** 2025-10-31

## Overview

Phase 0 builds the core trading engine (Railyard) and end-of-day analysis system (EOD Reporter). These components must meet institutional-grade standards for reliability, performance, and risk management.

## Quality Standard

**Would a JPMorgan quant AND a Robinhood engineer trust this implementation?**

- JPMorgan quant perspective: Trading logic sound? Risk management robust? Algorithms proven?
- Robinhood engineer perspective: Code clean? Architecture scalable? Production-ready?

## 1. Railyard - Real-Time Trading Engine

### 1.1 Core Responsibilities

**Pattern Monitoring**
- Monitor real-time tick data for selected stocks (8/12/16/20)
- Detect 3-Step Geometric patterns OR VWAP Breakout patterns
- Track pattern completion with millisecond precision
- Apply entry confirmation rule (+0.5% climb from pattern low)

**Trade Execution**
- Execute market buy orders via IBKR API when patterns confirm
- Calculate position sizes based on account balance and deployment ratio
- Track order fills and latency
- Record all executions with timestamps and slippage metrics

**Exit Logic (Tiered System)**
- **T1 Floor (+0.75%)**: Lock in first milestone
- **CROSS Floor (+1.00%)**: Lock in second milestone  
- **Momentum Confirmation (+1.25%)**: Pursue T2 target
- **T2 Target (+1.75%)**: Maximum profit target
- **Tiered Timeouts (Dead Zone)**: 
  - Below T1: 3 min → exit if any positive
  - At T1: 4 min → exit at T1
  - At CROSS: 4 min → exit at CROSS
  - After momentum: 6 min → exit at best available
- **Stop Loss (-0.5%)**: Hard floor protection

**Risk Management**
- Daily loss limit: -1.5% of account balance → auto-pause all trading
- Position size limits per stock
- Maximum concurrent positions
- Kill switch functionality (manual emergency stop)
- Cooldown period: 1 minute after each trade per stock

### 1.2 Filter Support

Must support 7 different filter configurations:

1. **Default**: No filters (baseline)
2. **Conservative**: All filters tight (±2% VWAP, 2.5x volume, time restrictions, S/R required, uptrend only)
3. **Aggressive**: Minimal filters (±10% VWAP, 1.5x volume, all hours, any trend)
4. **Choppy Market**: S/R focused, neutral trend
5. **Trending Market**: Momentum focused, uptrend required
6. **AB Test**: User-defined experimental configurations
7. **VWAP Breakout**: Different pattern type entirely

Filters include:
- VWAP proximity (entry price within ±X% of VWAP)
- Volume threshold (current volume ≥ X multiplier of average)
- Time-of-day restrictions (exclude first/last hour for some presets)
- Support/Resistance proximity
- Trend alignment (20/50/200 MA)

### 1.3 Data Integration

**Inputs (from Morning Report)**
- Selected stocks (8/12/16/20)
- Active preset (which filter configuration)
- Time profiles (adaptive timeouts per stock)
- Expected performance forecast

**Real-Time Data (from IBKR)**
- Tick-level price data
- VWAP (calculated or from IBKR)
- Volume
- Bid-ask spread
- Order fills

**Outputs (to Database)**
- All executions to `fills` table
- Real-time positions and P&L
- Pattern detection events (for analysis)

### 1.4 Performance Requirements

- **Latency**: <100ms from pattern confirmation to order submission
- **Throughput**: Handle 20-30 concurrent stock monitors
- **Uptime**: Must not crash during market hours (9:31 AM - 4:00 PM)
- **Recovery**: If connection lost, reconnect and recover state within 10 seconds

### 1.5 Monitoring & Observability

**Live Dashboard Support** (via API endpoint `/api/railyard-data`):
- Current positions (ticker, entry price, current P&L, time in position)
- Recent fills (last 10 trades)
- Actual vs forecast comparison (trades count, P&L, win rate)
- Account balance and deployed capital
- Active patterns being monitored
- System health status

**Logging Requirements**:
- Pattern detection events (with timestamps)
- Entry confirmations
- Exit decisions (reason: T1, CROSS, T2, dead zone, stop loss)
- Order submissions and fills
- Error conditions (connection issues, API errors, risk limit violations)

### 1.6 Safety & Risk Controls

**Pre-Trade Controls**:
- Verify account balance before each trade
- Confirm position size within limits
- Check daily loss limit not exceeded
- Validate ticker in selected stocks list
- Confirm market hours

**Position Management**:
- Maximum position size: Do not exceed X% of account per stock
- Maximum concurrent positions: Based on portfolio size (8/12/16/20)
- No naked short positions
- Close all positions by 3:55 PM (5 min before market close)

**Circuit Breakers**:
- Daily loss limit: -1.5% → Stop all trading
- Connection loss: Pause trading, attempt reconnection
- IBKR API errors (3 consecutive): Pause trading, alert user
- Kill switch: Manual stop button stops all trading immediately

## 2. EOD Reporter - End-of-Day Analysis

### 2.1 Core Responsibilities

**Data Collection**
- Load morning forecast from database
- Fetch all fills from IBKR and database
- Filter fills to selected stocks only (CRITICAL)
- Calculate realized P&L for closed positions

**Metrics Calculation**
- Win rate, loss rate
- Average win %, average loss %
- Sharpe ratio (risk-adjusted return)
- Sortino ratio (downside risk-adjusted return)
- Calmar ratio (return vs max drawdown)
- Max drawdown %
- Average latency (order submission to fill)
- Average slippage %

**Forecast Accuracy**
- Compare actual trade count vs expected range
- Compare actual P&L vs expected range
- Compare actual win rate vs expected
- Calculate forecast accuracy percentages

**Per-Stock Breakdown**
- Trades per stock
- P&L per stock
- Win rate per stock
- Average win/loss per stock
- Best performing stocks
- Worst performing stocks

**Storage**
- Store summary in `daily_summaries` table
- Include per-stock breakdown as JSON
- Link to morning forecast

### 2.2 Report Output

**Summary Statistics** (stored in database, displayed in UI):
```
Opening Balance: $XX,XXX.XX
Closing Balance: $XX,XXX.XX
Realized P&L: $XXX.XX (+X.XX%)
Unrealized P&L: $XX.XX (if any positions held overnight)

Trades: XX (expected: XX-XX)
Wins: XX (XX%)
Losses: XX (XX%)

Average Win: +X.XX%
Average Loss: -X.XX%
Risk/Reward: X.XX

Sharpe Ratio: X.XX
Sortino Ratio: X.XX
Max Drawdown: -X.XX%

Avg Latency: XXXms
Avg Slippage: X.XX%
```

**Forecast Comparison**:
```
Metric          Expected      Actual      Accuracy
------------------------------------------------
Trade Count     15-25         22          ✓ Within range
P&L %           +2.8-4.5%     +3.2%       ✓ Within range
Win Rate        68%           71%         +3% better
```

**Per-Stock Performance** (top 3 and bottom 3):
```
Best Performers:
1. AAPL: 3 trades, +1.2%, 100% win rate
2. MSFT: 2 trades, +0.9%, 100% win rate
3. GOOGL: 4 trades, +0.8%, 75% win rate

Worst Performers:
1. TSLA: 3 trades, -0.3%, 33% win rate
2. AMD: 2 trades, -0.2%, 50% win rate
3. NVDA: 1 trade, -0.5%, 0% win rate
```

### 2.3 Data Quality Checks

**Validation Before Analysis**:
- Confirm fills match IBKR records
- Verify all buy orders have corresponding sell orders (or still open)
- Check for orphaned records
- Validate P&L calculations against IBKR account balance
- Flag any discrepancies for manual review

**Reconciliation**:
- Opening balance + realized P&L = closing balance (within rounding)
- Sum of per-stock P&L = total realized P&L
- Number of sell orders = number of completed trades

## 3. Database Schema Requirements

### 3.1 New Tables

None - Phase 0 uses existing tables.

### 3.2 Existing Tables to Use

**morning_forecasts** (already exists):
- Primary source for selected stocks
- Contains all 7 forecasts
- Contains time profiles for adaptive timeouts

**fills** (already exists):
- Store every IBKR execution (buy and sell)
- Columns: ibkr_execution_id, date, timestamp, ticker, action, quantity, price, realized_pnl, commission, latency_ms, slippage_pct

**daily_summaries** (already exists):
- Store EOD analysis results
- Columns: date, opening_balance, closing_balance, realized_pl, roi_pct, trade_count, win_count, loss_count, win_rate, sharpe_ratio, sortino_ratio, max_drawdown_pct, avg_latency_ms, avg_slippage_pct, stock_performance_json

### 3.3 Critical Data Integrity Rules

1. **Fills must be filtered to selected stocks only**
   - When EOD loads fills, filter by `ticker IN selected_stocks`
   - Do NOT include all fills from IBKR if user traded other stocks manually

2. **Timestamps must be millisecond precision**
   - Pattern detection: ms precision
   - Order submission: ms precision
   - Fill received: ms precision

3. **Realized P&L calculation**
   - Only for closed positions (matching buy + sell)
   - Include commission in calculation
   - Store gross and net P&L separately

## 4. Integration Requirements

### 4.1 Morning Report → Railyard

**Data Flow**:
```
morning_forecasts table
    → Railyard reads: selected_stocks_json, time_profiles_json, active_preset
    → Railyard configures: stock monitors, filter rules, timeout settings
```

### 4.2 Railyard → Database

**Data Flow**:
```
IBKR order fills
    → Railyard writes to fills table
    → Includes: execution_id, timestamp, ticker, action, price, quantity, latency, slippage
```

### 4.3 Database → EOD Reporter

**Data Flow**:
```
morning_forecasts + fills tables
    → EOD reads: forecast + filtered fills (selected stocks only)
    → EOD calculates: metrics, accuracy, per-stock breakdown
    → EOD writes to: daily_summaries table
```

### 4.4 EOD Reporter → Frontend

**Data Flow**:
```
daily_summaries table
    → API endpoint /api/eod-data
    → Frontend displays: charts, tables, metrics
```

## 5. Technology Stack

**Backend (Confirmed)**:
- Python 3.10+
- Flask 3.0+ (API framework)
- ib_insync (IBKR connectivity)
- SQLite (dev) / PostgreSQL (prod)
- pandas (data manipulation)
- numpy (calculations)

**IBKR Connection**:
- IB Gateway on localhost:4002 (paper trading)
- IB Gateway on localhost:4001 (live trading - future)

**Frontend (Deferred to Later Phases)**:
- Material Design 3 components
- Chart.js for visualizations

## 6. Testing Requirements

### 6.1 Unit Tests (Per Component)

**Pattern Detector**:
- Test 3-Step Geometric detection
- Test VWAP Breakout detection
- Test entry confirmation logic
- Test filter application

**Exit Logic**:
- Test T1/CROSS/momentum/T2 tiers
- Test dead zone timeouts
- Test stop loss trigger
- Test tiered timeout escalation

**Risk Controls**:
- Test daily loss limit
- Test position size limits
- Test kill switch
- Test cooldown period

**EOD Metrics**:
- Test Sharpe ratio calculation
- Test Sortino ratio calculation
- Test win rate calculation
- Test forecast accuracy calculation

### 6.2 Integration Tests

**Database → API → Frontend Chain**:
- Test morning forecast loaded correctly
- Test fills filtered to selected stocks
- Test EOD summary calculated correctly
- Test API returns correct JSON

**IBKR Connection**:
- Test connection to IB Gateway
- Test order submission
- Test fill reception
- Test reconnection after disconnect

### 6.3 End-to-End Test

**Simulated Trading Day**:
1. Load morning forecast with 8 test stocks
2. Run Railyard with paper trading account
3. Monitor for patterns on real market data
4. Execute at least 3 test trades
5. Let exit logic close positions
6. Run EOD reporter
7. Verify all data chain works: Forecast → Fills → EOD → Display

**Success Criteria**:
- No crashes during market hours
- All trades recorded in database
- EOD report generated correctly
- Forecast vs actual comparison accurate
- No orphaned records

## 7. Known Limitations & Future Work

**Phase 0 Limitations**:
- Frontend will be basic (existing templates, not MD3 yet)
- No backtesting integration (future phase)
- No multi-strategy support (future phase)
- No position rollover overnight (close all by 3:55 PM)
- No options or futures (equities only)

**Future Phases**:
- Phase 1-6: User/fund management
- Phase 7-17: Backend enhancements
- Phase 18-31: Frontend rebuild with MD3

## 8. Success Criteria

**Phase 0 is complete when:**

✅ Railyard can monitor 20 stocks simultaneously  
✅ Railyard detects patterns correctly (validated against test data)  
✅ Railyard executes trades via IBKR  
✅ Exit logic works: T1 → CROSS → momentum → T2  
✅ Dead zone timeouts work correctly  
✅ Stop loss triggers at -0.5%  
✅ Daily loss limit auto-pauses at -1.5%  
✅ EOD reporter generates accurate summary  
✅ Forecast accuracy calculated correctly  
✅ Integration tested: Database → API → Frontend chain works  
✅ No critical bugs in 3 consecutive test days  
✅ User has successfully paper-traded for 1 week without issues  

## 9. Open Questions for User

1. **Position Sizing**: Should position size be equal-weighted across stocks, or weighted by composite score?
2. **Risk Limits**: Confirm 1.5% daily loss limit is appropriate. Industry standard is 1-2%.
3. **Dead Zone Timeouts**: Should timeouts be stock-specific (from morning report) or universal?
4. **Cooldown Period**: Confirm 1 minute cooldown after each trade per stock. Could be 30s-5min.
5. **Market Close**: Confirm all positions closed by 3:55 PM (5 min buffer before close).
6. **VWAP Calculation**: Use IBKR's VWAP or calculate our own? Calculate = more control, IBKR = less latency.
7. **Pattern Detection**: Should we record ALL patterns detected (even if not traded) for analysis?

## 10. References

- docs/explainers/trading_strategy_explainer.md
- docs/explainers/morning_report_explainer.md
- docs/explainers/data_pipeline_explainer.md
- Industry research: FIA Best Practices for Automated Trading Risk Controls
- Industry research: Institutional trading architecture patterns (event sourcing, CEP, order management)

---

**Next Step**: User reviews this DRAFT requirements.md. Once approved, we create plan.md and begin implementation.
