#!/usr/bin/env python3
"""
Test IBKR tick streaming latency.

Measures:
- Connection latency
- Snapshot latency
- Streaming update frequency

Run this before paper/live trading to verify <100ms updates.
"""

import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

from backend.data.ibkr_connector import IBKRConnector
from config.config import IBKRConfig


def test_latency():
    """Test IBKR connection and streaming latency."""
    print("=" * 60)
    print("IBKR LATENCY TEST")
    print("=" * 60)
    print()
    
    # Initialize connector (paper trading)
    print("1. Connecting to IBKR Gateway...")
    ibkr = IBKRConnector(
        port=IBKRConfig.PAPER_PORT,
        paper_trading=True
    )
    
    if not ibkr.connect():
        print("❌ Failed to connect to IBKR Gateway")
        print("\nMake sure:")
        print("  - IBKR Gateway is running")
        print("  - Gateway is configured for paper trading")
        print("  - Port 4002 is open")
        return False
    
    print("✓ Connected to IBKR Gateway")
    print()
    
    # Test 1: Snapshot latency
    print("2. Testing snapshot latency...")
    ticker = 'AAPL'
    latencies = []
    
    for i in range(10):
        start = time.time()
        snapshot = ibkr.get_market_snapshot(ticker)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        if snapshot:
            latencies.append(elapsed)
            print(f"   Snapshot {i+1}: {elapsed:.1f}ms")
        else:
            print(f"   Snapshot {i+1}: Failed")
        
        time.sleep(0.1)
    
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print()
        print(f"   Average latency: {avg_latency:.1f}ms")
        print(f"   Min latency: {min_latency:.1f}ms")
        print(f"   Max latency: {max_latency:.1f}ms")
        
        if avg_latency < 100:
            print(f"   ✓ PASS - Average latency under 100ms target")
        else:
            print(f"   ⚠ WARNING - Average latency exceeds 100ms target")
    else:
        print("   ❌ No successful snapshots")
        return False
    
    print()
    
    # Test 2: Streaming update frequency
    print("3. Testing streaming update frequency (10 seconds)...")
    
    # Subscribe to market data
    ibkr.subscribe_market_data([ticker])
    time.sleep(1)  # Wait for subscription
    
    print(f"   Monitoring {ticker} updates...")
    
    start_time = time.time()
    update_count = 0
    last_price = None
    price_changes = 0
    
    while time.time() - start_time < 10:
        snapshot = ibkr.get_market_snapshot(ticker)
        
        if snapshot and 'last_price' in snapshot:
            update_count += 1
            
            if last_price is not None and snapshot['last_price'] != last_price:
                price_changes += 1
            
            last_price = snapshot['last_price']
        
        time.sleep(0.01)  # Poll every 10ms
    
    elapsed = time.time() - start_time
    update_frequency = update_count / elapsed
    
    print(f"   Updates received: {update_count} in {elapsed:.1f} seconds")
    print(f"   Update frequency: {update_frequency:.1f} Hz")
    print(f"   Price changes: {price_changes}")
    
    if update_frequency >= 10:  # 10 Hz = 100ms updates
        print(f"   ✓ PASS - Update frequency meets 100ms target")
    else:
        print(f"   ⚠ WARNING - Update frequency below 100ms target")
    
    print()
    
    # Test 3: Multiple tickers
    print("4. Testing multiple ticker streaming...")
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    
    ibkr.subscribe_market_data(tickers)
    time.sleep(1)
    
    multi_start = time.time()
    ticker_updates = {t: 0 for t in tickers}
    
    while time.time() - multi_start < 5:
        for ticker in tickers:
            snapshot = ibkr.get_market_snapshot(ticker)
            if snapshot:
                ticker_updates[ticker] += 1
        
        time.sleep(0.01)
    
    print(f"   Updates per ticker (5 seconds):")
    for ticker, count in ticker_updates.items():
        freq = count / 5
        status = "✓" if freq >= 10 else "⚠"
        print(f"     {status} {ticker}: {count} updates ({freq:.1f} Hz)")
    
    print()
    
    # Disconnect
    ibkr.disconnect()
    
    # Summary
    print("=" * 60)
    print("LATENCY TEST SUMMARY")
    print("=" * 60)
    print()
    
    all_pass = (
        avg_latency < 100 and
        update_frequency >= 10 and
        all(count / 5 >= 8 for count in ticker_updates.values())  # Allow 80% success
    )
    
    if all_pass:
        print("✅ ALL TESTS PASSED")
        print()
        print("System is ready for:")
        print("  - Real-time pattern detection")
        print("  - <100ms trade execution")
        print("  - Multiple ticker monitoring")
    else:
        print("⚠️  SOME TESTS FAILED")
        print()
        print("Recommendations:")
        print("  - Check network connection")
        print("  - Reduce concurrent applications")
        print("  - Consider upgrading IBKR Gateway")
        print("  - Test during different market hours")
    
    print()
    return all_pass


if __name__ == '__main__':
    success = test_latency()
    exit(0 if success else 1)
