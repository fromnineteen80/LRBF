IBKR CLIENT PORTAL WEB API - IMPLEMENTATION VERIFICATION
==========================================================
Date: October 26, 2025
Status: NEEDS VERIFICATION AGAINST LIVE GATEWAY

OFFICIAL IBKR API DOCUMENTATION:
- https://www.interactivebrokers.com/campus/ibkr-api-page/webapi-ref/
- https://api.ibkr.com/gw/api/v3/api-docs

==========================================================
ENDPOINTS IMPLEMENTED (backend/data/ibkr_connector.py)
==========================================================

1. AUTHENTICATION
   ✅ GET /v1/api/iserver/auth/status
   Purpose: Check if authenticated to gateway
   Returns: {authenticated: bool, connected: bool}
   
   ✅ POST /v1/api/logout
   Purpose: End session

2. SYMBOL LOOKUP
   ✅ GET /v1/api/iserver/secdef/search
   Parameters: 
     - symbol: ticker (e.g., "AAPL")
     - name: false
     - secType: "STK" (for stocks)
   Returns: [{conid: int, symbol: str, ...}]
   
   ⚠️  ISSUE: Need to verify response format matches IBKR spec

3. HISTORICAL DATA
   ✅ GET /v1/api/iserver/marketdata/history
   Parameters:
     - conid: contract ID (from secdef/search)
     - period: "1d", "5d", "1w", "1m" etc.
     - bar: "1min", "5min", "15min", "30min", "1h", "1d"
     - outsideRth: "false" (regular hours only)
   Returns: {data: [{t: timestamp, o: open, h: high, l: low, c: close, v: volume}]}
   
   ⚠️  ISSUE: Need to verify:
     - Parameter format for period (is "1d" correct or "1 day"?)
     - Response parsing (are fields 'o','h','l','c','v' or full names?)
     - Does it support VWAP in response?

4. REAL-TIME DATA
   ✅ GET /v1/api/iserver/marketdata/snapshot
   Parameters:
     - conids: contract ID
     - fields: "31,84,86,87,7633" (last,bid,ask,volume,vwap)
   Returns: [{31: last_price, 84: bid, 86: ask, 87: volume, 7633: vwap}]
   
   ⚠️  ISSUE: Need to verify field codes:
     - 31 = Last price? ✅ (documented)
     - 84 = Bid? ✅ (documented)
     - 86 = Ask? ✅ (documented)
     - 87 = Volume? ✅ (documented)
     - 7633 = VWAP? ⚠️  (need to confirm this code)

5. MARKET SCANNER
   ✅ POST /v1/api/iserver/scanner/run
   Parameters:
     - instrument: "STK"
     - location: "STK.US.MAJOR"
     - type: "MOST_ACTIVE"
     - filter: []
   Returns: {contracts: [{symbol: str, conid: int, volume: int, ...}]}
   
   ⚠️  CRITICAL: This endpoint may NOT exist in IBKR API!
     - Scanner might require different endpoint
     - May need /iserver/scanner/params first
     - Scanner results may need subscription

6. ACCOUNT DATA
   ✅ GET /v1/api/portfolio/{accountId}/summary
   ✅ GET /v1/api/portfolio/{accountId}/positions/0
   ✅ GET /v1/api/iserver/account/trades
   
   ⚠️  ISSUE: Verify these endpoints exist in IBKR spec

7. ORDER MANAGEMENT
   ✅ POST /v1/api/iserver/account/{accountId}/orders
   ✅ DELETE /v1/api/iserver/account/orders
   
   ⚠️  ISSUE: Orders may require additional setup/confirmation

==========================================================
CRITICAL ISSUES TO VERIFY
==========================================================

ISSUE 1: MARKET SCANNER ENDPOINT
---------------------------------
Current implementation: POST /iserver/scanner/run

IBKR Documentation shows:
- GET /iserver/scanner/params (get available scanners)
- POST /hmds/scanner (different base path?)

ACTION REQUIRED: Test actual scanner endpoint on live gateway

ISSUE 2: HISTORICAL DATA VWAP
------------------------------
Current code expects VWAP in historical bars.

IBKR Documentation:
- Historical bars may NOT include VWAP
- VWAP might need to be calculated manually
- Or fetched via separate snapshot calls

ACTION REQUIRED: Check if historical response includes VWAP field

ISSUE 3: GATEWAY URL
--------------------
Code uses: https://localhost:5000
TECHNICAL_SPECS.md says: https://localhost:8000

⚠️  FIXED in commit 4c9d259 (changed to 8000)

But default in __init__ may still be wrong:
gateway_url: str = "https://localhost:5000"  ← Should be 8000?

ISSUE 4: WEBSOCKET STREAMING
-----------------------------
Current implementation: backend/data/ibkr_websocket.py

WebSocket endpoint: wss://localhost:8000/v1/api/ws

IBKR Documentation:
- May use different WebSocket path
- May require session token
- Field codes need verification

ACTION REQUIRED: Test WebSocket connection on live gateway

ISSUE 5: TICK DATA vs BARS
---------------------------
Morning report needs 20-day TICK data for pattern detection.

Current implementation requests:
- bar_size = "1min" (1-minute bars)

This is NOT tick data! Tick data is trade-by-trade.

IBKR may not support 20 days of tick-level data via history endpoint.
Typical limits:
- Tick data: Last 24-48 hours only
- Minute bars: Up to 1 year

ACTION REQUIRED: Clarify if 1-min bars are acceptable or true ticks needed

==========================================================
MORNING REPORT DATA REQUIREMENTS
==========================================================

For morning report to work correctly, it needs:

1. ✅ Get top 500 stocks by volume (scanner)
2. ✅ For each stock, fetch 20 days of 1-minute bars
3. ⚠️  Parse OHLCV + VWAP from bars (VWAP may not be in response)
4. ✅ Run pattern detection on 20-day data
5. ✅ Calculate 16-category quality scores
6. ✅ Generate 7 forecast scenarios
7. ✅ Store in database

BLOCKING ISSUES:
- Scanner endpoint may not work as implemented
- VWAP may not be in historical data response
- 20 days of 1-min bars = 7,800 bars per stock × 500 stocks = 3.9M bars
  → This is massive data volume, may hit rate limits

==========================================================
RECOMMENDED TESTING STEPS
==========================================================

STEP 1: Test Basic Connection
------------------------------
python3 << EOF
from backend.data.ibkr_connector import IBKRConnector
ibkr = IBKRConnector(account_id="5697343", paper_trading=True, gateway_url="https://localhost:8000")
print("Connected:", ibkr.connect())
EOF

STEP 2: Test Symbol Lookup
---------------------------
conid = ibkr._get_conid("AAPL")
print("AAPL conid:", conid)

STEP 3: Test Historical Data
-----------------------------
df = ibkr.get_historical_data("AAPL", period_days=1, bar_size="1min")
print("Columns:", df.columns.tolist())
print("Has VWAP:", 'vwap' in df.columns)

STEP 4: Test Market Scanner
----------------------------
stocks = ibkr.run_market_scanner(limit=10)
print("Scanned stocks:", stocks)

STEP 5: Test Real-Time Snapshot
--------------------------------
ibkr.subscribe_market_data(["AAPL"])
snapshot = ibkr.get_market_snapshot("AAPL")
print("Snapshot:", snapshot)

==========================================================
ALTERNATIVE APPROACH (IF SCANNER FAILS)
==========================================================

If IBKR scanner doesn't work, use this strategy:

1. Maintain curated list of ~500 liquid stocks
2. Use IBKR only for historical data + real-time quotes
3. Update curated list quarterly based on volume

This is MORE RELIABLE than depending on scanner endpoint.

==========================================================
VERDICT
==========================================================

STATUS: ⚠️  NEEDS LIVE TESTING

The IBKR connector implementation looks reasonable but has NOT been
tested against a live IBKR Client Portal Gateway instance.

CRITICAL GAPS:
1. Scanner endpoint implementation may be incorrect
2. VWAP may not be in historical data
3. Response parsing needs verification
4. Rate limits not handled
5. WebSocket not tested

RECOMMENDATION:
1. Start IBKR Client Portal Gateway on localhost:8000
2. Run all 5 testing steps above
3. Fix any endpoint/response format issues
4. Add rate limit handling
5. Consider fallback to static list if scanner fails

==========================================================
