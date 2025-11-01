"""
IBKR Connector - PROFESSIONAL IMPLEMENTATION (Enhanced for Phase 0)

Uses ib_insync library (industry standard for IBKR Python integration).
Battle-tested, maintained, used by real quant firms.

Why ib_insync instead of custom REST wrapper:
1. Maintained by professionals (10+ years)
2. Handles all IBKR API quirks automatically
3. Async/sync support built-in
4. Error handling for real-world edge cases
5. Active community (thousands of users)
6. Works with TWS and IB Gateway (more reliable than Client Portal)

Installation:
    pip install ib_insync --break-system-packages

Documentation:
    https://ib-insync.readthedocs.io/

Author: The Luggage Room Boys Fund
Date: October 2025
Phase 0 Enhancements: Real-time tick streaming, reconnection, fill tracking
"""

from ib_insync import IB, Stock, util, Ticker
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Generator, Callable
import asyncio
import time


class IBKRConnectorInsync:
    """
    Professional IBKR connector using ib_insync library.
    Enhanced for Phase 0 Railyard real-time trading.
    
    Connects to TWS (Trader Workstation) or IB Gateway (more stable).
    """
    
    def __init__(
        self,
        host: str = '127.0.0.1',
        port: int = 4002,  # 4002 = Gateway paper, 4001 = Gateway live
        client_id: int = 1,
        account: str = None
    ):
        """
        Initialize IBKR connector.
        
        Args:
            host: IB Gateway/TWS host (default: localhost)
            port: 4002 (Gateway paper), 4001 (Gateway live), 7497 (TWS paper), 7496 (TWS live)
            client_id: Unique client ID (1-999)
            account: Paper account starts with 'DU', live is regular account ID
        """
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.account = account
        self.connected = False
        self._ticker_streams = {}  # Active ticker subscriptions
        self._order_callbacks = {}  # Order callbacks for fill tracking
    
    def connect(self, timeout: int = 10) -> bool:
        """
        Connect to IB Gateway or TWS.
        
        Args:
            timeout: Connection timeout in seconds
        
        Returns:
            True if connected successfully
        """
        try:
            self.ib.connect(
                self.host,
                self.port,
                clientId=self.client_id,
                timeout=timeout,
                readonly=False
            )
            self.connected = True
            
            # Get account if not specified
            if not self.account:
                accounts = self.ib.managedAccounts()
                if accounts:
                    self.account = accounts[0]
            
            print(f"✅ Connected to IBKR")
            print(f"   Host: {self.host}:{self.port}")
            print(f"   Account: {self.account}")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print(f"   Make sure IB Gateway or TWS is running on port {self.port}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IBKR and cleanup subscriptions."""
        if self.connected:
            # Cancel all ticker streams
            for ticker_obj in self._ticker_streams.values():
                self.ib.cancelMktData(ticker_obj.contract)
            self._ticker_streams.clear()
            
            # Clear order callbacks
            self._order_callbacks.clear()
            
            self.ib.disconnect()
            self.connected = False
            print("✅ Disconnected from IBKR")
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to IBKR.
        
        Returns:
            True if connected
        """
        return self.connected and self.ib.isConnected()
    
    def reconnect(self, max_attempts: int = 3) -> bool:
        """
        Attempt to reconnect to IBKR after connection loss.
        
        Args:
            max_attempts: Maximum reconnection attempts
        
        Returns:
            True if reconnected successfully
        """
        print(f"🔄 Attempting to reconnect to IBKR (max {max_attempts} attempts)...")
        
        for attempt in range(1, max_attempts + 1):
            print(f"   Attempt {attempt}/{max_attempts}...")
            
            # Disconnect if partially connected
            try:
                if self.ib.isConnected():
                    self.ib.disconnect()
            except:
                pass
            
            # Wait before retry
            time.sleep(2 * attempt)  # Exponential backoff
            
            # Try to connect
            if self.connect():
                print(f"✅ Reconnected successfully on attempt {attempt}")
                return True
        
        print(f"❌ Failed to reconnect after {max_attempts} attempts")
        return False
    
    # ========================================================================
    # REAL-TIME TICK STREAMING (Phase 0 Requirement)
    # ========================================================================
    
    def stream_ticks(self, ticker: str, snapshot: bool = False) -> Optional[Ticker]:
        """
        Subscribe to real-time tick data for a ticker.
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            snapshot: If True, get snapshot only (not streaming)
        
        Returns:
            Ticker object that updates automatically with new ticks
        
        Usage:
            ticker_obj = connector.stream_ticks('AAPL')
            while True:
                print(f"Price: {ticker_obj.last}, Time: {ticker_obj.time}")
                connector.ib.sleep(0.1)  # Check every 100ms
        """
        if not self.is_connected():
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            contract = Stock(ticker, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Request market data
            ticker_obj = self.ib.reqMktData(
                contract,
                genericTickList='',
                snapshot=snapshot,
                regulatorySnapshot=False
            )
            
            # Store for cleanup
            self._ticker_streams[ticker] = ticker_obj
            
            # Wait for initial data
            self.ib.sleep(1)
            
            return ticker_obj
            
        except Exception as e:
            print(f"❌ Error streaming {ticker}: {e}")
            return None
    
    def stop_stream(self, ticker: str):
        """Stop streaming tick data for a ticker."""
        if ticker in self._ticker_streams:
            self.ib.cancelMktData(self._ticker_streams[ticker].contract)
            del self._ticker_streams[ticker]
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get current price for a ticker (uses existing stream or creates snapshot).
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Current last price
        """
        if not self.is_connected():
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            # If already streaming, use that
            if ticker in self._ticker_streams:
                return self._ticker_streams[ticker].last
            
            # Otherwise get snapshot
            ticker_obj = self.stream_ticks(ticker, snapshot=True)
            if ticker_obj:
                return ticker_obj.last
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting price for {ticker}: {e}")
            return None
    
    # ========================================================================
    # ORDER EXECUTION WITH FILL TRACKING (Phase 0 Requirement)
    # ========================================================================
    
    def place_market_order(
        self,
        ticker: str,
        quantity: int,
        action: str = 'BUY',
        callback: Optional[Callable] = None
    ) -> Optional[Dict]:
        """
        Place market order with fill tracking.
        
        Args:
            ticker: Stock symbol
            quantity: Number of shares
            action: 'BUY' or 'SELL'
            callback: Optional callback function(fill_data) called when filled
        
        Returns:
            Order status dict with submission time and order ID
        """
        if not self.is_connected():
            raise ConnectionError("Not connected. Call connect() first.")
        
        submission_time = datetime.now()
        
        try:
            from ib_insync import MarketOrder
            
            contract = Stock(ticker, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            order = MarketOrder(action, quantity)
            
            # Place order
            trade = self.ib.placeOrder(contract, order)
            
            # Store callback for fill tracking
            if callback:
                self._order_callbacks[trade.order.orderId] = callback
            
            # Wait briefly for order to be submitted
            self.ib.sleep(0.5)
            
            order_data = {
                'order_id': trade.order.orderId,
                'ticker': ticker,
                'action': action,
                'quantity': quantity,
                'status': trade.orderStatus.status,
                'submission_time': submission_time,
                'filled': trade.orderStatus.filled,
                'avg_fill_price': trade.orderStatus.avgFillPrice,
                'trade_obj': trade  # For tracking
            }
            
            return order_data
            
        except Exception as e:
            print(f"❌ Order failed: {e}")
            return None
    
    def wait_for_fill(
        self,
        order_data: Dict,
        timeout: int = 5
    ) -> Optional[Dict]:
        """
        Wait for an order to fill.
        
        Args:
            order_data: Order data dict from place_market_order()
            timeout: Max seconds to wait
        
        Returns:
            Fill data dict or None if timeout
        """
        if not self.is_connected():
            return None
        
        trade = order_data.get('trade_obj')
        if not trade:
            return None
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            self.ib.sleep(0.1)  # Check every 100ms
            
            if trade.orderStatus.status == 'Filled':
                fill_time = datetime.now()
                
                # Calculate latency
                submission_time = order_data['submission_time']
                latency_ms = (fill_time - submission_time).total_seconds() * 1000
                
                fill_data = {
                    'order_id': trade.order.orderId,
                    'ticker': order_data['ticker'],
                    'action': order_data['action'],
                    'quantity': trade.orderStatus.filled,
                    'price': trade.orderStatus.avgFillPrice,
                    'fill_time': fill_time,
                    'latency_ms': latency_ms,
                    'commission': trade.orderStatus.commission if hasattr(trade.orderStatus, 'commission') else 0,
                    'status': 'Filled'
                }
                
                # Call callback if exists
                if trade.order.orderId in self._order_callbacks:
                    callback = self._order_callbacks.pop(trade.order.orderId)
                    callback(fill_data)
                
                return fill_data
        
        # Timeout
        return None
    
    def get_order_status(self, order_id: int) -> Optional[str]:
        """
        Get current status of an order.
        
        Returns:
            Status string: 'Submitted', 'Filled', 'Cancelled', etc.
        """
        if not self.is_connected():
            return None
        
        trades = self.ib.trades()
        for trade in trades:
            if trade.order.orderId == order_id:
                return trade.orderStatus.status
        
        return None
    
    # ========================================================================
    # HISTORICAL DATA (For Morning Report)
    # ========================================================================
    
    def get_historical_data(
        self,
        ticker: str,
        duration: str = '20 D',  # 20 days
        bar_size: str = '1 min',
        what_to_show: str = 'TRADES'
    ) -> Optional[pd.DataFrame]:
        """
        Get historical intraday data.
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            duration: Time period ('20 D', '1 W', '1 Y')
            bar_size: '1 min', '5 mins', '15 mins', '30 mins', '1 hour', '1 day'
            what_to_show: 'TRADES', 'MIDPOINT', 'BID', 'ASK'
        
        Returns:
            DataFrame with columns: [date, open, high, low, close, volume, average, barCount]
            'average' is VWAP!
        """
        if not self.is_connected():
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            # Create stock contract
            contract = Stock(ticker, 'SMART', 'USD')
            
            # Qualify contract (get full details)
            self.ib.qualifyContracts(contract)
            
            # Request historical data
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',  # Now
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=True,  # Regular trading hours only
                formatDate=1
            )
            
            if not bars:
                print(f"⚠️  No data for {ticker}")
                return None
            
            # Convert to DataFrame
            df = util.df(bars)
            
            # Rename 'average' to 'vwap' for clarity
            if 'average' in df.columns:
                df['vwap'] = df['average']
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching {ticker}: {e}")
            return None
    
    # ========================================================================
    # MARKET SCANNER (Get Top Stocks)
    # ========================================================================
    
    def scan_top_stocks(
        self,
        limit: int = 500,
        instrument: str = 'STK',
        location: str = 'STK.US.MAJOR',
        scan_code: str = 'TOP_PERC_GAIN'
    ) -> List[str]:
        """
        Scan for top stocks using IBKR market scanner.
        
        Args:
            limit: Maximum results
            instrument: 'STK' for stocks
            location: 'STK.US.MAJOR', 'STK.NASDAQ', etc.
            scan_code: 'TOP_PERC_GAIN', 'MOST_ACTIVE', 'HOT_BY_VOLUME'
        
        Returns:
            List of ticker symbols
        """
        if not self.is_connected():
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            # Create scanner subscription
            scanner_sub = self.ib.reqScannerSubscription(
                instrument=instrument,
                locationCode=location,
                scanCode=scan_code,
                numberOfRows=limit
            )
            
            # Wait for results
            self.ib.sleep(2)
            
            # Extract tickers
            tickers = [data.contract.symbol for data in scanner_sub]
            
            return tickers[:limit]
            
        except Exception as e:
            print(f"❌ Scanner error: {e}")
            return []
    
    # ========================================================================
    # ACCOUNT DATA
    # ========================================================================
    
    def get_account_balance(self) -> float:
        """Get current account balance (Net Liquidation Value)."""
        if not self.is_connected():
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            account_values = self.ib.accountValues(self.account)
            
            for value in account_values:
                if value.tag == 'NetLiquidation' and value.currency == 'USD':
                    return float(value.value)
            
            return 0.0
            
        except Exception as e:
            print(f"❌ Error getting balance: {e}")
            return 0.0
    
    def get_positions(self) -> List[Dict]:
        """Get current positions."""
        if not self.is_connected():
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            positions = self.ib.positions(self.account)
            
            return [
                {
                    'symbol': pos.contract.symbol,
                    'quantity': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_value': pos.marketValue,
                    'unrealized_pnl': pos.unrealizedPNL
                }
                for pos in positions
            ]
            
        except Exception as e:
            print(f"❌ Error getting positions: {e}")
            return []
    
    # ========================================================================
    # MARKET DATA SNAPSHOT
    # ========================================================================
    
    def get_market_snapshot(self, ticker: str) -> Optional[Dict]:
        """
        Get real-time market data snapshot.
        
        Returns:
            Dict with: last, bid, ask, volume, vwap
        """
        if not self.is_connected():
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            ticker_obj = self.stream_ticks(ticker, snapshot=True)
            
            if not ticker_obj:
                return None
            
            return {
                'symbol': ticker,
                'last_price': ticker_obj.last,
                'bid': ticker_obj.bid,
                'ask': ticker_obj.ask,
                'volume': ticker_obj.volume,
                'vwap': ticker_obj.vwap,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Error getting snapshot for {ticker}: {e}")
            return None


# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

def get_connector(paper: bool = True) -> IBKRConnectorInsync:
    """
    Get connected IBKR connector.
    
    Args:
        paper: Use paper trading account (True) or live (False)
    
    Returns:
        Connected IBKRConnectorInsync instance
    """
    port = 4002 if paper else 4001  # IB Gateway ports
    
    connector = IBKRConnectorInsync(port=port)
    
    if connector.connect():
        return connector
    else:
        raise ConnectionError("Could not connect to IBKR")


# ========================================================================
# EXAMPLE USAGE
# ========================================================================

if __name__ == "__main__":
    print("Testing Enhanced IBKR Connector (Phase 0)...")
    print()
    
    # Connect
    ibkr = get_connector(paper=True)
    
    # Test connection status
    print(f"Connected: {ibkr.is_connected()}")
    print()
    
    # Test tick streaming
    print("Testing tick streaming (5 seconds)...")
    ticker_obj = ibkr.stream_ticks('AAPL')
    if ticker_obj:
        for i in range(50):  # 5 seconds at 100ms intervals
            price = ticker_obj.last
            print(f"   AAPL: ${price:.2f}", end='\r')
            ibkr.ib.sleep(0.1)
        print()  # New line
        ibkr.stop_stream('AAPL')
    print()
    
    # Test current price
    print("Getting current price...")
    price = ibkr.get_current_price('AAPL')
    print(f"   AAPL: ${price:.2f}")
    print()
    
    # Test account balance
    print("Getting account info...")
    balance = ibkr.get_account_balance()
    print(f"   Balance: ${balance:,.2f}")
    print()
    
    # Test historical data
    print("Fetching historical data...")
    df = ibkr.get_historical_data("AAPL", duration="5 D", bar_size="1 min")
    if df is not None:
        print(f"   Got {len(df)} bars")
        print(f"   VWAP included: {'vwap' in df.columns}")
    print()
    
    # Disconnect
    ibkr.disconnect()
    print("✅ Phase 0 tests complete")
