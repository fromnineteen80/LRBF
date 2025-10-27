"""
IBKR Connector - ib_insync Implementation

Uses ib_insync library for native IB Gateway connection.
Much simpler and more reliable than Client Portal Web API.

Prerequisites:
1. IB Gateway or TWS running
2. Gateway configured for port 4002 (paper) or 4001 (live)
3. Socket client enabled in Gateway settings

Author: The Luggage Room Boys Fund
Date: October 2025
"""

from ib_insync import IB, Stock, MarketOrder, LimitOrder, util
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
import pandas as pd
import time


class IBKRConnector:
    """
    Production IBKR connector using ib_insync.
    
    Advantages over Client Portal API:
    - Native binary protocol (faster, more reliable)
    - Built-in tick streaming (no WebSocket needed)
    - Simpler contract specification
    - Better error handling
    - ~200 lines vs 400+ lines
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4002,
        client_id: int = 1,
        account_id: str = None,
        paper_trading: bool = True
    ):
        """
        Initialize IBKR connector.
        
        Args:
            host: IB Gateway host (default: 127.0.0.1)
            port: Gateway port (4002=paper, 4001=live, 7497=TWS paper, 7496=TWS live)
            client_id: Unique client identifier (1-32)
            account_id: IBKR account ID (optional, will auto-detect)
            paper_trading: Use paper trading account if True
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.account_id = account_id
        self.paper_trading = paper_trading
        self.connected = False
        
        # Initialize ib_insync client
        self.ib = IB()
        
        # Contract cache (symbol -> Contract)
        self._contract_cache = {}
    
    # ========================================================================
    # CONNECTION
    # ========================================================================
    
    def connect(self) -> bool:
        """
        Connect to IB Gateway.
        
        Returns:
            True if connected successfully
        """
        try:
            self.ib.connect(
                host=self.host,
                port=self.port,
                clientId=self.client_id,
                timeout=20
            )
            
            self.connected = True
            
            # Auto-detect account ID if not provided
            if not self.account_id:
                accounts = self.ib.managedAccounts()
                if accounts:
                    self.account_id = accounts[0]
                    if self.paper_trading and not self.account_id.startswith('DU'):
                        print(f"⚠️  Warning: Using account {self.account_id} but paper_trading=True")
            
            print(f"✅ Connected to IB Gateway (Account: {self.account_id})")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print(f"   Ensure IB Gateway is running on {self.host}:{self.port}")
            return False
    
    def disconnect(self):
        """Disconnect from IB Gateway."""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            print("✅ Disconnected from IBKR")
    
    def check_connection(self) -> Dict:
        """
        Check connection health.
        
        Returns:
            Dictionary with connection status
        """
        return {
            'connected': self.ib.isConnected(),
            'account_id': self.account_id,
            'paper_trading': self.paper_trading
        }
    
    # ========================================================================
    # CONTRACT MANAGEMENT
    # ========================================================================
    
    def _get_contract(self, ticker: str) -> Optional[Stock]:
        """
        Get Stock contract for ticker (with caching).
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Stock contract or None
        """
        # Check cache first
        if ticker in self._contract_cache:
            return self._contract_cache[ticker]
        
        try:
            # Create stock contract
            contract = Stock(ticker, 'SMART', 'USD')
            
            # Qualify contract (get full details from IBKR)
            self.ib.qualifyContracts(contract)
            
            # Cache it
            self._contract_cache[ticker] = contract
            
            return contract
            
        except Exception as e:
            print(f"❌ Failed to get contract for {ticker}: {e}")
            return None
    
    # ========================================================================
    # ACCOUNT DATA
    # ========================================================================
    
    def get_account_balance(self) -> Dict:
        """
        Get current account balance.
        
        Returns:
            Dictionary with account data
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        try:
            # Request account summary
            account_values = self.ib.accountValues(account=self.account_id)
            
            # Extract key metrics
            metrics = {
                'NetLiquidation': 0.0,
                'TotalCashValue': 0.0,
                'GrossPositionValue': 0.0,
                'BuyingPower': 0.0,
                'ExcessLiquidity': 0.0
            }
            
            for item in account_values:
                if item.tag in metrics:
                    metrics[item.tag] = float(item.value)
            
            return {
                'total_balance': metrics['NetLiquidation'],
                'cash_balance': metrics['TotalCashValue'],
                'deployed_capital': metrics['GrossPositionValue'],
                'reserve_capital': metrics['TotalCashValue'] - metrics['GrossPositionValue'],
                'buying_power': metrics['BuyingPower'],
                'margin_available': metrics['ExcessLiquidity'],
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Failed to get account balance: {e}")
            raise
    
    # ========================================================================
    # POSITIONS
    # ========================================================================
    
    def get_positions(self) -> List[Dict]:
        """
        Get current open positions.
        
        Returns:
            List of position dictionaries
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        try:
            positions = self.ib.positions(account=self.account_id)
            
            # Get total portfolio value for percentages
            account = self.get_account_balance()
            total_value = account['total_balance']
            
            result = []
            for pos in positions:
                ticker = pos.contract.symbol
                quantity = pos.position
                avg_cost = pos.avgCost
                market_price = pos.marketPrice
                market_value = pos.marketValue
                unrealized_pnl = pos.unrealizedPNL
                
                result.append({
                    'ticker': ticker,
                    'quantity': int(quantity),
                    'avg_cost': float(avg_cost),
                    'market_price': float(market_price),
                    'market_value': float(market_value),
                    'unrealized_pnl': float(unrealized_pnl),
                    'position_pct': (market_value / total_value * 100) if total_value else 0
                })
            
            return result
            
        except Exception as e:
            print(f"❌ Failed to get positions: {e}")
            return []
    
    # ========================================================================
    # FILLS / EXECUTIONS
    # ========================================================================
    
    def get_fills(
        self,
        start_date: date = None,
        end_date: date = None,
        ticker: str = None
    ) -> List[Dict]:
        """
        Get recent trade fills.
        
        Args:
            start_date: Start date (default: today)
            end_date: End date (default: today)
            ticker: Filter by ticker (optional)
            
        Returns:
            List of fill dictionaries
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today()
        
        try:
            # Get all fills
            fills = self.ib.fills()
            
            result = []
            for fill in fills:
                # Parse execution time
                exec_time = fill.execution.time
                
                # Filter by date range
                if not (start_date <= exec_time.date() <= end_date):
                    continue
                
                # Get symbol
                symbol = fill.contract.symbol
                
                # Filter by ticker if specified
                if ticker and symbol != ticker:
                    continue
                
                # Determine action
                action = 'BUY' if fill.execution.side == 'BOT' else 'SELL'
                
                result.append({
                    'ibkr_execution_id': fill.execution.execId,
                    'timestamp': exec_time,
                    'ticker': symbol,
                    'action': action,
                    'quantity': int(fill.execution.shares),
                    'price': float(fill.execution.price),
                    'realized_pnl': float(fill.commissionReport.realizedPNL) if fill.commissionReport else 0.0,
                    'commission': float(fill.commissionReport.commission) if fill.commissionReport else 0.0
                })
            
            return result
            
        except Exception as e:
            print(f"❌ Failed to get fills: {e}")
            return []
    
    # ========================================================================
    # HISTORICAL DATA
    # ========================================================================
    
    def get_historical_data(
        self,
        ticker: str,
        period_days: int = 20,
        bar_size: str = "1 min"
    ) -> Optional[pd.DataFrame]:
        """
        Get historical intraday data.
        
        Args:
            ticker: Stock symbol
            period_days: Number of days (default: 20)
            bar_size: Bar size (default: "1 min")
                Options: "1 secs", "5 secs", "10 secs", "15 secs", "30 secs",
                        "1 min", "2 mins", "3 mins", "5 mins", "10 mins", 
                        "15 mins", "30 mins", "1 hour", "2 hours", "4 hours",
                        "1 day", "1 week", "1 month"
        
        Returns:
            DataFrame with OHLCV data + VWAP
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        try:
            # Get contract
            contract = self._get_contract(ticker)
            if not contract:
                return None
            
            # Calculate duration string
            # IBKR format: "X D" (days), "X W" (weeks), "X M" (months)
            if period_days <= 1:
                duration = "1 D"
            elif period_days <= 30:
                duration = f"{period_days} D"
            elif period_days <= 365:
                weeks = (period_days + 6) // 7
                duration = f"{weeks} W"
            else:
                months = (period_days + 29) // 30
                duration = f"{months} M"
            
            # Request historical data
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',  # Empty = current time
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,  # Regular trading hours only
                formatDate=1  # 1 = string format
            )
            
            if not bars:
                print(f"⚠️  No historical data for {ticker}")
                return None
            
            # Convert to DataFrame
            df = util.df(bars)
            
            # Rename columns
            df.rename(columns={
                'date': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }, inplace=True)
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Calculate VWAP if not present
            if 'vwap' not in df.columns and 'average' in df.columns:
                df['vwap'] = df['average']
            elif 'vwap' not in df.columns:
                # Calculate VWAP: sum(price * volume) / sum(volume)
                df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
            
            # Keep only necessary columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'vwap']]
            
            return df
            
        except Exception as e:
            print(f"❌ Failed to get historical data for {ticker}: {e}")
            return None
    
    # ========================================================================
    # MARKET SCANNER
    # ========================================================================
    
    def get_top_stocks_by_volume(
        self,
        limit: int = 500,
        min_volume: int = 5_000_000,
        min_price: float = 5.0
    ) -> List[str]:
        """
        Get top stocks by volume using IBKR scanner.
        
        Args:
            limit: Maximum number of stocks
            min_volume: Minimum average daily volume
            min_price: Minimum stock price
            
        Returns:
            List of ticker symbols
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        try:
            from ib_insync import ScannerSubscription
            
            # Create scanner subscription
            sub = ScannerSubscription(
                instrument='STK',
                locationCode='STK.US.MAJOR',
                scanCode='MOST_ACTIVE'
            )
            
            # Add filters
            sub.aboveVolume = min_volume
            sub.abovePrice = min_price
            
            # Request scan
            scan_data = self.ib.reqScannerData(sub)
            
            # Extract symbols
            symbols = [
                item.contract.symbol 
                for item in scan_data[:limit]
            ]
            
            return symbols
            
        except Exception as e:
            print(f"❌ Failed to scan stocks: {e}")
            return []
    
    # ========================================================================
    # REAL-TIME MARKET DATA
    # ========================================================================
    
    def get_market_snapshot(self, ticker: str) -> Optional[Dict]:
        """
        Get current market snapshot.
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Dictionary with current market data
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        try:
            contract = self._get_contract(ticker)
            if not contract:
                return None
            
            # Request market data snapshot
            self.ib.reqMktData(contract, '', snapshot=True)
            
            # Wait for data (max 5 seconds)
            self.ib.sleep(2)
            
            # Get ticker data
            ticker_data = self.ib.ticker(contract)
            
            return {
                'ticker': ticker,
                'last_price': float(ticker_data.last) if ticker_data.last else None,
                'bid': float(ticker_data.bid) if ticker_data.bid else None,
                'ask': float(ticker_data.ask) if ticker_data.ask else None,
                'volume': int(ticker_data.volume) if ticker_data.volume else 0,
                'vwap': float(ticker_data.vwap) if hasattr(ticker_data, 'vwap') and ticker_data.vwap else None,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Failed to get snapshot for {ticker}: {e}")
            return None
    
    def subscribe_market_data(self, tickers: List[str]) -> Dict:
        """
        Subscribe to real-time market data (streaming).
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary with subscription results
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        results = {}
        
        for ticker in tickers:
            try:
                contract = self._get_contract(ticker)
                if not contract:
                    results[ticker] = {'success': False, 'error': 'Contract not found'}
                    continue
                
                # Subscribe to streaming data
                self.ib.reqMktData(contract, '', False, False)
                
                results[ticker] = {'success': True, 'contract': contract}
                
            except Exception as e:
                results[ticker] = {'success': False, 'error': str(e)}
        
        return results
    
    # ========================================================================
    # ORDER EXECUTION
    # ========================================================================
    
    def place_order(
        self,
        ticker: str,
        action: str,
        quantity: int,
        order_type: str = "MKT",
        limit_price: float = None
    ) -> Dict:
        """
        Place an order.
        
        Args:
            ticker: Stock symbol
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: 'MKT' or 'LMT'
            limit_price: Required for limit orders
            
        Returns:
            Order confirmation dictionary
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        try:
            # Get contract
            contract = self._get_contract(ticker)
            if not contract:
                return {
                    'order_id': None,
                    'status': 'ERROR',
                    'message': f'Contract not found for {ticker}'
                }
            
            # Create order
            if order_type == 'MKT':
                order = MarketOrder(action, quantity)
            elif order_type == 'LMT':
                if not limit_price:
                    raise ValueError("limit_price required for limit orders")
                order = LimitOrder(action, quantity, limit_price)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            # Place order
            trade = self.ib.placeOrder(contract, order)
            
            # Wait for order ID
            self.ib.sleep(1)
            
            return {
                'order_id': trade.order.orderId,
                'status': trade.orderStatus.status,
                'message': f'Order placed: {action} {quantity} {ticker}'
            }
            
        except Exception as e:
            print(f"❌ Failed to place order: {e}")
            return {
                'order_id': None,
                'status': 'ERROR',
                'message': str(e)
            }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("IBKR ib_insync Connector - Test Suite")
    print("=" * 60)
    print("⚠️  Ensure IB Gateway is running on port 4002 (paper trading)")
    print("=" * 60)
    
    # Initialize connector
    ibkr = IBKRConnector(
        port=4002,  # Paper trading
        paper_trading=True
    )
    
    # Test 1: Connect
    print("\n1. Connecting to IB Gateway...")
    if ibkr.connect():
        print("   ✅ Connected successfully")
    else:
        print("   ❌ Connection failed")
        exit(1)
    
    # Test 2: Check connection
    print("\n2. Checking connection...")
    health = ibkr.check_connection()
    print(f"   Connected: {health['connected']}")
    print(f"   Account: {health['account_id']}")
    
    # Test 3: Get account balance
    print("\n3. Getting account balance...")
    try:
        balance = ibkr.get_account_balance()
        print(f"   Total Balance: ${balance['total_balance']:,.2f}")
        print(f"   Cash: ${balance['cash_balance']:,.2f}")
        print(f"   Deployed: ${balance['deployed_capital']:,.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Get positions
    print("\n4. Getting positions...")
    positions = ibkr.get_positions()
    print(f"   Found {len(positions)} positions")
    for pos in positions[:3]:  # Show first 3
        print(f"     {pos['ticker']}: {pos['quantity']} shares @ ${pos['market_price']:.2f}")
    
    # Test 5: Get historical data
    print("\n5. Getting historical data for AAPL...")
    df = ibkr.get_historical_data('AAPL', period_days=1, bar_size='1 min')
    if df is not None:
        print(f"   ✅ Retrieved {len(df)} bars")
        print(f"   Columns: {list(df.columns)}")
        print("\n   Sample data:")
        print(df.head())
    
    # Test 6: Market scanner
    print("\n6. Scanning top 10 stocks by volume...")
    top_stocks = ibkr.get_top_stocks_by_volume(limit=10)
    print(f"   Found {len(top_stocks)} stocks:")
    print(f"   {', '.join(top_stocks)}")
    
    # Test 7: Market snapshot
    print("\n7. Getting market snapshot for AAPL...")
    snapshot = ibkr.get_market_snapshot('AAPL')
    if snapshot:
        print(f"   Last: ${snapshot['last_price']:.2f}")
        print(f"   Bid: ${snapshot['bid']:.2f}")
        print(f"   Ask: ${snapshot['ask']:.2f}")
        if snapshot['vwap']:
            print(f"   VWAP: ${snapshot['vwap']:.2f}")
    
    # Disconnect
    print("\n8. Disconnecting...")
    ibkr.disconnect()
    
    print("\n" + "=" * 60)
    print("✅ Test suite complete!")
