"""
IBKR Connector - PROFESSIONAL IMPLEMENTATION

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
"""

from ib_insync import IB, Stock, util
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio


class IBKRConnector:
    """
    Professional IBKR connector using ib_insync library.
    
    Connects to TWS (Trader Workstation) or IB Gateway (more stable than Client Portal).
    """
    
    def __init__(
        self,
        host: str = '127.0.0.1',
        port: int = 7497,  # 7497 = TWS paper, 7496 = TWS live, 4002 = Gateway paper
        client_id: int = 1,
        account: str = None
    ):
        """
        Initialize IBKR connector.
        
        Args:
            host: IB Gateway/TWS host (default: localhost)
            port: 7497 (TWS paper), 7496 (TWS live), 4002 (Gateway paper), 4001 (Gateway live)
            client_id: Unique client ID (1-999)
            account: Paper account starts with 'DU', live is regular account ID
        """
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.account = account
        self.connected = False
    
    def connect(self) -> bool:
        """
        Connect to IB Gateway or TWS.
        
        Returns:
            True if connected successfully
        """
        try:
            self.ib.connect(
                self.host,
                self.port,
                clientId=self.client_id,
                timeout=20
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
            return False
    
    def disconnect(self):
        """Disconnect from IBKR."""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
    
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
        if not self.connected:
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
        if not self.connected:
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            # Request scanner parameters
            params = self.ib.reqScannerParameters()
            
            # Create scanner subscription
            scanner_sub = self.ib.reqScannerSubscription(
                instrument=instrument,
                locationCode=location,
                scanCode=scan_code,
                numberOfRows=limit
            )
            
            # Get results
            self.ib.sleep(2)  # Wait for scanner results
            
            # Extract tickers
            tickers = [data.contract.symbol for data in scanner_sub]
            
            return tickers[:limit]
            
        except Exception as e:
            print(f"❌ Scanner error: {e}")
            return []
    
    # ========================================================================
    # REAL-TIME DATA
    # ========================================================================
    
    def get_market_snapshot(self, ticker: str) -> Optional[Dict]:
        """
        Get real-time market data snapshot.
        
        Returns:
            Dict with: last, bid, ask, volume, vwap
        """
        if not self.connected:
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            contract = Stock(ticker, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Request market data
            ticker_obj = self.ib.reqMktData(contract, '', False, False)
            
            # Wait for data
            self.ib.sleep(1)
            
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
    # ACCOUNT DATA
    # ========================================================================
    
    def get_account_balance(self) -> float:
        """Get current account balance."""
        if not self.connected:
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
        if not self.connected:
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
    # ORDER EXECUTION
    # ========================================================================
    
    def place_market_order(
        self,
        ticker: str,
        quantity: int,
        action: str = 'BUY'
    ) -> Optional[Dict]:
        """
        Place market order.
        
        Args:
            ticker: Stock symbol
            quantity: Number of shares
            action: 'BUY' or 'SELL'
        
        Returns:
            Order status dict
        """
        if not self.connected:
            raise ConnectionError("Not connected. Call connect() first.")
        
        try:
            from ib_insync import MarketOrder
            
            contract = Stock(ticker, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            order = MarketOrder(action, quantity)
            
            trade = self.ib.placeOrder(contract, order)
            
            # Wait for fill
            self.ib.sleep(1)
            
            return {
                'order_id': trade.order.orderId,
                'status': trade.orderStatus.status,
                'filled': trade.orderStatus.filled,
                'avg_fill_price': trade.orderStatus.avgFillPrice
            }
            
        except Exception as e:
            print(f"❌ Order failed: {e}")
            return None


# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

def get_connector(paper: bool = True) -> IBKRConnector:
    """
    Get connected IBKR connector.
    
    Args:
        paper: Use paper trading account (True) or live (False)
    
    Returns:
        Connected IBKRConnector instance
    """
    port = 4002 if paper else 4001  # IB Gateway ports
    
    connector = IBKRConnector(port=port)
    
    if connector.connect():
        return connector
    else:
        raise ConnectionError("Could not connect to IBKR")


# ========================================================================
# EXAMPLE USAGE
# ========================================================================

if __name__ == "__main__":
    print("Testing IBKR Connector (ib_insync)...")
    print()
    
    # Connect
    ibkr = get_connector(paper=True)
    
    # Get historical data
    print("Fetching AAPL historical data...")
    df = ibkr.get_historical_data("AAPL", duration="5 D", bar_size="1 min")
    print(f"   Got {len(df)} bars")
    print(f"   Columns: {df.columns.tolist()}")
    print(f"   VWAP included: {'vwap' in df.columns}")
    print()
    
    # Get snapshot
    print("Getting AAPL snapshot...")
    snapshot = ibkr.get_market_snapshot("AAPL")
    print(f"   Price: ${snapshot['last_price']}")
    print(f"   VWAP: ${snapshot['vwap']}")
    print()
    
    # Get account info
    print("Getting account info...")
    balance = ibkr.get_account_balance()
    print(f"   Balance: ${balance:,.2f}")
    print()
    
    # Disconnect
    ibkr.disconnect()
    print("✅ Test complete")
