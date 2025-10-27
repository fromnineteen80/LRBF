# NEXT SESSION EXECUTION PLAN
**Objective:** Complete ib_insync migration + validate morning report
**Estimated Tokens:** 30k (90% code, 10% validation)

---

## PHASE 1: ib_insync Migration (5 commits, ~15k tokens)

### Commit 1: Add ib_insync dependency
**File:** `requirements.txt`
**Action:** Add `ib-insync>=0.9.86`

### Commit 2: Rewrite IBKR connector with ib_insync
**File:** `backend/data/ibkr_connector.py`
**Replace entire file with:**
- IB() connection to localhost:4002 (IB Gateway)
- Methods: connect(), get_historical_data(), get_account_balance(), get_positions(), get_fills()
- Use Stock() contract for symbols
- reqHistoricalData() for 20-day bars
- reqTickers() for real-time snapshots
- scannerData() for top 500 stocks by volume
- Keep SAME method signatures (drop-in replacement)

**Key differences from Client Portal:**
- No HTTP/REST calls (native binary protocol)
- No contract ID lookup needed (use Stock('AAPL', 'SMART', 'USD'))
- Built-in tick streaming (no WebSocket needed)
- Simpler code (~200 lines vs 400)

### Commit 3: Update data provider wrapper
**File:** `backend/data/ibkr_data_provider.py`
**Changes:**
- Import from new ibkr_connector
- scan_top_stocks() → use ib.reqScannerData()
- get_historical_data() → parse ib_insync BarDataList to DataFrame
- get_current_price() → use ib.reqTickers()
- Add VWAP calculation if not in bars

### Commit 4: Delete WebSocket (not needed)
**File:** `backend/data/ibkr_websocket.py`
**Action:** DELETE (ib_insync has streaming built-in via reqMktData())

### Commit 5: Update configuration
**File:** `config/config.py`
**Action:** Add IB Gateway settings (host, port, clientId)

---

## PHASE 2: Validation (3 steps, ~10k tokens)

### Step 1: Create test script
**File:** `test_ib_insync_connector.py`
**Test:**
1. Connect to IB Gateway (localhost:4002)
2. Get AAPL contract
3. Fetch 1 day historical data
4. Check VWAP calculation
5. Run scanner for 10 stocks
6. Get real-time snapshot

### Step 2: Fix any issues
Based on test output, fix:
- Connection parameters
- Contract specification
- Historical data parsing
- Scanner parameters
- VWAP calculation

### Step 3: Integration test
**Run:** `python backend/reports/morning_report.py`
**Verify:**
- Scans 500 stocks from IB Gateway
- Fetches 20-day data per stock
- Generates 7 forecasts
- Stores in database
- No errors

---

## PHASE 3: Documentation (2 commits, ~5k tokens)

### Commit 1: Update TECHNICAL_SPECS.md
**Changes:**
- Replace Client Portal sections with IB Gateway
- Update data source to ib_insync
- Update latency specs (1-10ms)
- Update prerequisites (IB Gateway setup)

### Commit 2: Create IB Gateway setup guide
**File:** `docs/IB_GATEWAY_SETUP.md`
**Content:**
- Download IB Gateway
- Configuration (port 4002)
- Paper trading setup
- Auto-restart settings
- Troubleshooting

---

## SUCCESS CRITERIA

✅ All 5 migration commits pushed
✅ Test script passes all checks
✅ Morning report generates 7 forecasts
✅ Database contains forecast data
✅ No Client Portal references remain

---

## FILE CHANGES SUMMARY

**Modified (3 files):**
- backend/data/ibkr_connector.py (complete rewrite)
- backend/data/ibkr_data_provider.py (update imports/calls)
- requirements.txt (add ib_insync)

**Deleted (1 file):**
- backend/data/ibkr_websocket.py

**Unchanged (everything else):**
- All core logic (pattern detection, forecasting, scoring)
- All reports (morning, EOD)
- All frontend (HTML, JS, CSS)
- All database schemas
- All other backend modules

**Total LOC changed:** ~500 lines (out of 15,000+ total)

---

## CRITICAL NOTES

1. **IB Gateway must be running** before any tests
2. **Paper account** (DU5697343) should be configured
3. **Port 4002** is standard for IB Gateway (not 8000)
4. **VWAP calculation:** If not in historical bars, calculate as sum(price × volume) / sum(volume)
5. **Scanner:** Use ScannerSubscription with TOP_PERC_GAIN or MOST_ACTIVE filter

---

## EXECUTION ORDER

1. Read this plan
2. Execute Phase 1 (migration) - commit after each step
3. Execute Phase 2 (validation) - fix issues immediately
4. Execute Phase 3 (documentation) - update specs
5. Report token usage after completion

---

## ESTIMATED TIMELINE

- Phase 1: 15k tokens (5 commits)
- Phase 2: 10k tokens (testing)
- Phase 3: 5k tokens (docs)
- **Total: 30k tokens**
- **Remaining: 60k tokens for morning report work**

---

## AFTER COMPLETION

Next priorities (if tokens remain):
1. Run full morning report scan (500 stocks)
2. Verify 7 forecasts stored correctly
3. Test database queries
4. Fix any performance issues

---

**END OF PLAN**
