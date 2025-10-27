"""
Test Suite for ib_insync Migration
Validates IBKR connection, data retrieval, and real-time streaming
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ib_insync import IB, Stock
from backend.data.ibkr_connector import IBKRConnector
import time

def test_connection():
    """Test basic IB Gateway connection"""
    print("\n=== Testing IB Gateway Connection ===")
    try:
        ib = IB()
        ib.connect('127.0.0.1', 4002, clientId=1)
        print(f"✅ Connected to IB Gateway")
        print(f"   Server Version: {ib.client.serverVersion()}")
        ib.disconnect()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_account_data():
    """Test account balance retrieval"""
    print("\n=== Testing Account Data ===")
    try:
        connector = IBKRConnector()
        if not connector.connect():
            print("❌ Could not connect to IBKR")
            return False
        
        balance = connector.get_account_balance()
        print(f"✅ Account Balance: ${balance:,.2f}")
        return True
    except Exception as e:
        print(f"❌ Account data failed: {e}")
        return False

def test_historical_data():
    """Test 20-day historical data retrieval"""
    print("\n=== Testing Historical Data ===")
    try:
        connector = IBKRConnector()
        if not connector.connect():
            print("❌ Could not connect to IBKR")
            return False
        
        df = connector.get_historical_data('AAPL', period_days=5, bar_size='1 min')
        if df is not None and not df.empty:
            print(f"✅ Historical data retrieved: {len(df)} bars")
            print(f"   Columns: {list(df.columns)}")
            print(f"   Date range: {df.index[0]} to {df.index[-1]}")
            return True
        else:
            print("❌ No historical data returned")
            return False
    except Exception as e:
        print(f"❌ Historical data failed: {e}")
        return False

def test_market_snapshot():
    """Test real-time market snapshot"""
    print("\n=== Testing Market Snapshot ===")
    try:
        connector = IBKRConnector()
        if not connector.connect():
            print("❌ Could not connect to IBKR")
            return False
        
        # Subscribe first
        connector.subscribe_market_data(['AAPL'])
        time.sleep(2)  # Wait for subscription
        
        snapshot = connector.get_market_snapshot('AAPL')
        if snapshot:
            print(f"✅ Market snapshot retrieved:")
            print(f"   Last: ${snapshot.get('last', 'N/A')}")
            print(f"   Bid: ${snapshot.get('bid', 'N/A')}")
            print(f"   Ask: ${snapshot.get('ask', 'N/A')}")
            print(f"   Volume: {snapshot.get('volume', 'N/A'):,}")
            return True
        else:
            print("❌ No snapshot data returned")
            return False
    except Exception as e:
        print(f"❌ Market snapshot failed: {e}")
        return False

def test_top_stocks():
    """Test top 500 scanner"""
    print("\n=== Testing Top Stocks Scanner ===")
    try:
        connector = IBKRConnector()
        if not connector.connect():
            print("❌ Could not connect to IBKR")
            return False
        
        stocks = connector.get_top_stocks_by_volume(limit=10)
        if stocks:
            print(f"✅ Scanner retrieved {len(stocks)} stocks:")
            for stock in stocks[:5]:
                print(f"   {stock.get('symbol', 'N/A')}: {stock.get('volume', 0):,} shares")
            return True
        else:
            print("❌ Scanner returned no stocks")
            return False
    except Exception as e:
        print(f"❌ Scanner failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("LRBF - ib_insync Migration Test Suite")
    print("=" * 60)
    
    results = []
    results.append(("Connection", test_connection()))
    results.append(("Account Data", test_account_data()))
    results.append(("Historical Data", test_historical_data()))
    results.append(("Market Snapshot", test_market_snapshot()))
    results.append(("Top Stocks Scanner", test_top_stocks()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! ib_insync migration successful.")
        sys.exit(0)
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check IBKR Gateway connection.")
        sys.exit(1)
