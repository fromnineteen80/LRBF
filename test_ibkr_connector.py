"""
IBKR Connector Validation Test

Tests all endpoints used by morning report against live IBKR Gateway.
Run this with IBKR Client Portal Gateway running on localhost:8000.

Usage:
    python test_ibkr_connector.py

Prerequisites:
    1. IBKR Client Portal Gateway running (https://localhost:8000)
    2. Authenticated via web portal
    3. Paper account DU5697343 configured
"""

import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, '/home/claude')

print("=" * 80)
print("IBKR CONNECTOR VALIDATION TEST")
print("=" * 80)
print()

# Test 1: Import and Initialize
print("TEST 1: Import and Initialize")
print("-" * 80)
try:
    from backend.data.ibkr_connector import IBKRConnector
    ibkr = IBKRConnector(
        account_id="5697343",
        paper_trading=True,
        gateway_url="https://localhost:8000"
    )
    print("✅ PASS: Connector initialized")
    print(f"   Account ID: {ibkr.account_id}")
    print(f"   Gateway: {ibkr.gateway_url}")
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

print()

# Test 2: Connection
print("TEST 2: Connection to Gateway")
print("-" * 80)
try:
    connected = ibkr.connect()
    if connected:
        print("✅ PASS: Connected and authenticated")
    else:
        print("❌ FAIL: Not connected")
        print("   Action: Login at https://localhost:8000")
        sys.exit(1)
except Exception as e:
    print(f"❌ FAIL: {e}")
    sys.exit(1)

print()

# Test 3: Symbol Lookup (Contract ID)
print("TEST 3: Symbol Lookup (Get Contract ID)")
print("-" * 80)
try:
    conid = ibkr._get_conid("AAPL")
    if conid:
        print(f"✅ PASS: AAPL contract ID = {conid}")
        print(f"   Endpoint: GET /iserver/secdef/search")
    else:
        print("❌ FAIL: Could not get contract ID")
        print("   Check if endpoint exists and returns data")
except Exception as e:
    print(f"❌ FAIL: {e}")
    print(f"   Error suggests endpoint may be incorrect")

print()

# Test 4: Historical Data
print("TEST 4: Historical Data (1 day, 1-minute bars)")
print("-" * 80)
try:
    df = ibkr.get_historical_data("AAPL", period_days=1, bar_size="1min")
    if df is not None and not df.empty:
        print(f"✅ PASS: Fetched {len(df)} bars")
        print(f"   Endpoint: GET /iserver/marketdata/history")
        print(f"   Columns: {df.columns.tolist()}")
        
        # Check for VWAP
        if 'vwap' in df.columns:
            print(f"   ✅ VWAP present in response")
        else:
            print(f"   ⚠️  VWAP NOT in response (needs manual calculation)")
        
        # Show sample bar
        print(f"\n   Sample bar:")
        print(f"   {df.iloc[0].to_dict()}")
    else:
        print("❌ FAIL: No data returned")
        print("   Check endpoint parameters and response format")
except Exception as e:
    print(f"❌ FAIL: {e}")
    print(f"   Error suggests endpoint or parsing issue")

print()

# Test 5: Market Scanner
print("TEST 5: Market Scanner (Top 10 stocks)")
print("-" * 80)
try:
    stocks = ibkr.run_market_scanner(limit=10)
    if stocks and len(stocks) > 0:
        print(f"✅ PASS: Scanned {len(stocks)} stocks")
        print(f"   Endpoint: POST /iserver/scanner/run")
        print(f"   Stocks: {stocks[:5]}...")
    else:
        print("❌ FAIL: Scanner returned no results")
        print("   CRITICAL: This endpoint may not exist!")
        print("   Action: Check IBKR docs for correct scanner endpoint")
except Exception as e:
    print(f"❌ FAIL: {e}")
    print(f"   Scanner endpoint likely incorrect")
    print(f"   Fallback: Use static curated stock list")

print()

# Test 6: Real-Time Snapshot
print("TEST 6: Real-Time Market Snapshot")
print("-" * 80)
try:
    # Subscribe first
    ibkr.subscribe_market_data(["AAPL"])
    
    # Get snapshot
    snapshot = ibkr.get_market_snapshot("AAPL")
    if snapshot:
        print(f"✅ PASS: Got snapshot for AAPL")
        print(f"   Endpoint: GET /iserver/marketdata/snapshot")
        print(f"   Data: {json.dumps(snapshot, indent=2)}")
        
        # Check field codes
        if 'last_price' in snapshot or '31' in snapshot:
            print(f"   ✅ Price data present")
        if 'vwap' in snapshot or '7633' in snapshot:
            print(f"   ✅ VWAP present")
        else:
            print(f"   ⚠️  VWAP field code may be wrong")
    else:
        print("❌ FAIL: No snapshot data")
except Exception as e:
    print(f"❌ FAIL: {e}")

print()

# Test 7: Account Summary
print("TEST 7: Account Summary")
print("-" * 80)
try:
    balance = ibkr.get_account_balance()
    if balance:
        print(f"✅ PASS: Account balance = ${balance:,.2f}")
        print(f"   Endpoint: GET /portfolio/{account_id}/summary")
    else:
        print("❌ FAIL: Could not get balance")
except Exception as e:
    print(f"❌ FAIL: {e}")

print()

# Summary
print("=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)
print()
print("Next Steps:")
print("1. Fix any failed tests by adjusting endpoint URLs/parameters")
print("2. If scanner fails, use static stock list as fallback")
print("3. If VWAP not in historical data, add manual calculation")
print("4. Re-run this test until all pass")
print()
print("After all tests pass:")
print("- Morning report will work with live IBKR data")
print("- Run: python backend/reports/morning_report.py")
print()
