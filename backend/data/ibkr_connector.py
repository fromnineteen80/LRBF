"""
IBKR Client Portal Gateway API Connector - Production Implementation

Connects to Interactive Brokers via Client Portal Gateway REST API.
Supports both paper trading and live trading modes.
Always uses real market data for 20-day historical analysis.

Official API Docs:
- https://www.interactivebrokers.com/campus/ibkr-api-page/web-api/
- https://api.ibkr.com/gw/api/v3/api-docs

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import requests
import urllib3
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
import time
import json
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings for localhost gateway
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class IBKRConnector:
    """
    Production IBKR Client Portal Gateway API connector.
    
    Prerequisites:
    1. IBKR Client Portal Gateway running (https://localhost:5000)
    2. Authenticated session (login via web portal first)
    3. Valid account ID
    
    Modes:
    - paper=True: Uses paper trading account (DU + account_id)
    - paper=False: Uses live trading account
    
    Historical data ALWAYS uses real market data regardless of mode.
    """
    
    def __init__(
        self,
        gateway_url: str = "https://localhost:5000",
        account_id: str = None,
        paper_trading: bool = True,
        timeout: int = 30
    ):
        """
        Initialize IBKR connector.
        
        Args:
            gateway_url: Client Portal Gateway URL (default: https://localhost:5000)
            account_id: IBKR account ID (required)
            paper_trading: Use paper trading account if True
            timeout: Request timeout in seconds
        """
        if not account_id:
            raise ValueError("account_id is required")
        
        self.gateway_url = gateway_url.rstrip('/')
        self.base_url = f"{self.gateway_url}/v1/api"
        self.account_id = f"DU{account_id}" if paper_trading else account_id
        self.paper_trading = paper_trading
        self.timeout = timeout
        self.connected = False
        
        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.verify = False  # For localhost SSL
    
    # ========================================================================
    # CONNECTION & AUTHENTICATION
    # ========================================================================
    
    def connect(self) -> bool:
        """
        Verify connection to IBKR Client Portal Gateway.
        
        Returns:
            True if connected and authenticated
        """
        try:
            # Check authentication status
            response = self.session.get(
                f"{self.base_url}/iserver/auth/status",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            auth_data = response.json()
            authenticated = auth_data.get('authenticated', False)
            connected = auth_data.get('connected', False)
            
            if authenticated and connected:
                self.connected = True
                return True
            else:
                print(f"❌ Not authenticated. Please login via: {self.gateway_url}")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def check_connection(self) -> Dict:
        """
        Check connection health and latency.
        
        Returns:
            Dictionary with connection metrics
        """
        if not self.connected:
            return {
                'connected': False,
                'authenticated': False,
                'latency_ms': None,
                'server_info': None
            }
        
        try:
            start_time = time.time()
            
            response = self.session.get(
                f"{self.base_url}/iserver/auth/status",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            latency = (time.time() - start_time) * 1000  # Convert to ms
            
            auth_data = response.json()
            
            return {
                'connected': auth_data.get('connected', False),
                'authenticated': auth_data.get('authenticated', False),
                'latency_ms': round(latency, 2),
                'server_info': auth_data.get('serverInfo', {})
            }
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return {
                'connected': False,
                'authenticated': False,
                'latency_ms': None,
                'server_info': None
            }
    
    
    def run_market_scanner(
        self,
        scanner_type: str = "TOP_PERC_GAIN",
        location: str = "STK.US.MAJOR",
        instrument: str = "STK",
        limit: int = 500,
        filters: List[Dict] = None
    ) -> List[Dict]:
        """
        Run IBKR market scanner to find stocks matching criteria.
        
        Args:
            scanner_type: Scanner type (e.g., "TOP_PERC_GAIN", "MOST_ACTIVE")
            location: Market location (e.g., "STK.US.MAJOR", "STK.NASDAQ")
            instrument: Instrument type (default "STK" for stocks)
            limit: Maximum results to return (default 500)
            filters: Additional filters (optional)
        
        Returns:
            List of dictionaries with stock data
        """
        try:
            scanner_params = {
                "instrument": instrument,
                "location": location,
                "type": scanner_type,
                "filter": filters or []
            }
            
            response = self._make_request(
                "POST",
                "/iserver/scanner/run",
                json=scanner_params
            )
            
            if not response or "contracts" not in response:
                return []
            
            results = []
            for contract in response["contracts"][:limit]:
                results.append({
                    'symbol': contract.get('symbol', ''),
                    'conid': contract.get('conid'),
                    'volume': contract.get('volume', 0),
                    'market_cap': contract.get('market_cap', 0),
                    'price': contract.get('last_price', 0),
                    'company_name': contract.get('company_name', '')
                })
            
            return results
            
        except Exception as e:
            print(f"Error running market scanner: {e}")
            return []
    
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
            List of ticker symbols sorted by volume
        """
        try:
            scanner_results = self.run_market_scanner(
                scanner_type="MOST_ACTIVE",
                location="STK.US.MAJOR",
                limit=limit * 2
            )
            
            filtered = [
                r['symbol'] for r in scanner_results
                if r['volume'] >= min_volume and r['price'] >= min_price
            ]
            
            return filtered[:limit]
            
        except Exception as e:
            print(f"Error getting top stocks: {e}")
            return []

    def disconnect(self):
        """Close IBKR connection and logout."""
        try:
            if self.connected:
                # Logout
                response = self.session.post(
                    f"{self.base_url}/logout",
                    timeout=self.timeout
                )
                self.connected = False
                print("✅ Disconnected from IBKR")
        except Exception as e:
            print(f"⚠️  Logout error: {e}")
    
    # ========================================================================
    # ACCOUNT DATA
    # ========================================================================
    
    def get_account_balance(self) -> Dict:
        """
        Get current account balance and margin information.
        
        Returns:
            Dictionary with account data:
            {
                'total_balance': float,      # Net liquidation value
                'cash_balance': float,       # Available cash
                'margin_available': float,   # Excess liquidity
                'buying_power': float,       # Buying power
                'deployed_capital': float,   # Securities gross position value
                'reserve_capital': float,    # Cash - deployed
                'timestamp': datetime
            }
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        try:
            # Get account summary
            response = self.session.get(
                f"{self.base_url}/portfolio/{self.account_id}/summary",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            summary = response.json()
            
            # Extract key metrics
            net_liq = self._extract_value(summary, 'netliquidationvalue')
            cash = self._extract_value(summary, 'totalcashvalue')
            excess_liq = self._extract_value(summary, 'excessliquidity')
            buying_power = self._extract_value(summary, 'buyingpower')
            securities = self._extract_value(summary, 'securitiesgrosspositionvalue')
            
            return {
                'total_balance': net_liq,
                'cash_balance': cash,
                'margin_available': excess_liq,
                'buying_power': buying_power,
                'deployed_capital': securities,
                'reserve_capital': cash - securities if cash and securities else 0,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Failed to get account balance: {e}")
            raise
    
    def _extract_value(self, summary: Dict, key: str) -> float:
        """Extract numeric value from account summary."""
        for item in summary:
            if item.get('key', '').lower() == key.lower():
                return float(item.get('value', 0))
        return 0.0
    
    # ========================================================================
    # POSITIONS
    # ========================================================================
    
    def get_positions(self) -> List[Dict]:
        """
        Get current open positions.
        
        Returns:
            List of position dictionaries:
            {
                'ticker': str,              # Stock symbol
                'quantity': int,            # Number of shares
                'avg_cost': float,          # Average cost per share
                'market_price': float,      # Current market price
                'market_value': float,      # Current position value
                'unrealized_pnl': float,    # Unrealized profit/loss
                'position_pct': float       # % of total portfolio
            }
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        try:
            # Get all positions for account
            response = self.session.get(
                f"{self.base_url}/portfolio/{self.account_id}/positions/0",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            positions_data = response.json()
            
            # Get total portfolio value for percentage calc
            account = self.get_account_balance()
            total_value = account['total_balance']
            
            positions = []
            for pos in positions_data:
                ticker = pos.get('contractDesc', pos.get('ticker', 'UNKNOWN'))
                quantity = float(pos.get('position', 0))
                avg_cost = float(pos.get('avgCost', 0))
                market_price = float(pos.get('mktPrice', 0))
                market_value = float(pos.get('mktValue', 0))
                unrealized_pnl = float(pos.get('unrealizedPnl', 0))
                
                positions.append({
                    'ticker': ticker,
                    'quantity': int(quantity),
                    'avg_cost': avg_cost,
                    'market_price': market_price,
                    'market_value': market_value,
                    'unrealized_pnl': unrealized_pnl,
                    'position_pct': (market_value / total_value * 100) if total_value else 0
                })
            
            return positions
            
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
        Get recent trade fills (executions).
        
        Args:
            start_date: Start date for fills (default: today)
            end_date: End date for fills (default: today)
            ticker: Filter by specific ticker (optional)
        
        Returns:
            List of fill dictionaries:
            {
                'ibkr_execution_id': str,   # Unique execution ID
                'timestamp': datetime,       # Execution time
                'ticker': str,              # Stock symbol
                'action': str,              # 'BUY' or 'SELL'
                'quantity': int,            # Number of shares
                'price': float,             # Execution price
                'realized_pnl': float,      # Realized P&L
                'commission': float,        # Commission paid
            }
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today()
        
        try:
            # Get executions for the date range
            # Note: IBKR API doesn't support date filtering directly
            # We fetch recent executions and filter client-side
            
            response = self.session.get(
                f"{self.base_url}/iserver/account/trades",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            trades_data = response.json()
            
            fills = []
            for trade in trades_data:
                # Parse execution time
                exec_time_str = trade.get('execution_time', '')
                try:
                    exec_time = datetime.strptime(exec_time_str, '%Y%m%d-%H:%M:%S')
                except:
                    exec_time = datetime.now()
                
                # Filter by date range
                trade_date = exec_time.date()
                if not (start_date <= trade_date <= end_date):
                    continue
                
                # Extract fill data
                symbol = trade.get('symbol', 'UNKNOWN')
                
                # Filter by ticker if specified
                if ticker and symbol != ticker:
                    continue
                
                side = trade.get('side', '')
                action = 'BUY' if side == 'B' else 'SELL'
                
                fills.append({
                    'ibkr_execution_id': trade.get('execution_id', ''),
                    'timestamp': exec_time,
                    'ticker': symbol,
                    'action': action,
                    'quantity': int(float(trade.get('size', 0))),
                    'price': float(trade.get('price', 0)),
                    'realized_pnl': float(trade.get('realized_pnl', 0)),
                    'commission': float(trade.get('commission', 0))
                })
            
            return fills
            
        except Exception as e:
            print(f"❌ Failed to get fills: {e}")
            return []
    
    # ========================================================================
    # HISTORICAL DATA (ALWAYS REAL DATA)
    # ========================================================================
    
    def get_historical_data(
        self,
        ticker: str,
        period_days: int = 20,
        bar_size: str = "1min"
    ) -> Optional[pd.DataFrame]:
        """
        Get historical intraday data from IBKR.
        
        CRITICAL: Always returns REAL market data regardless of paper/live mode.
        Used for morning report 20-day pattern analysis.
        
        Args:
            ticker: Stock ticker symbol
            period_days: Number of days of historical data (default: 20)
            bar_size: Bar interval (1min, 5min, 15min, 30min, 1h, 1d)
        
        Returns:
            DataFrame with columns: [timestamp, open, high, low, close, volume]
            Returns None if data fetch fails
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        try:
            # Step 1: Get contract ID (conid) for ticker
            conid = self._get_conid(ticker)
            if not conid:
                print(f"❌ Could not find contract ID for {ticker}")
                return None
            
            # Step 2: Determine period parameter
            # IBKR uses format like "1d", "5d", "1w", "1m"
            if period_days <= 1:
                period = "1d"
            elif period_days <= 7:
                period = f"{period_days}d"
            elif period_days <= 30:
                period = f"{(period_days + 6) // 7}w"  # Convert to weeks
            else:
                period = f"{(period_days + 29) // 30}m"  # Convert to months
            
            # Step 3: Request historical data
            response = self.session.get(
                f"{self.base_url}/iserver/marketdata/history",
                params={
                    'conid': conid,
                    'period': period,
                    'bar': bar_size,
                    'outsideRth': 'false'  # Regular trading hours only
                },
                timeout=self.timeout * 2  # Longer timeout for historical data
            )
            response.raise_for_status()
            
            history_data = response.json()
            
            # Step 4: Parse bars
            bars = history_data.get('data', [])
            if not bars:
                print(f"⚠️  No historical data returned for {ticker}")
                return None
            
            # Step 5: Convert to DataFrame
            df = pd.DataFrame(bars)
            
            # Rename columns to standard format
            column_map = {
                't': 'timestamp',
                'o': 'open',
                'h': 'high',
                'l': 'low',
                'c': 'close',
                'v': 'volume'
            }
            df.rename(columns=column_map, inplace=True)
            
            # Convert timestamp from milliseconds to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Convert numeric columns
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sort by timestamp
            df.sort_values('timestamp', inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            return df
            
        except Exception as e:
            print(f"❌ Failed to get historical data for {ticker}: {e}")
            return None
    
    def _get_conid(self, ticker: str) -> Optional[int]:
        """
        Get contract ID (conid) for a stock ticker.
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Contract ID or None if not found
        """
        try:
            # Search for security
            response = self.session.get(
                f"{self.base_url}/iserver/secdef/search",
                params={
                    'symbol': ticker,
                    'name': 'false',
                    'secType': 'STK'  # Stock
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            results = response.json()
            
            if results and len(results) > 0:
                # Return first match (usually most relevant)
                return results[0].get('conid')
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to get conid for {ticker}: {e}")
            return None
    
    # ========================================================================
    # ORDER EXECUTION (Paper or Live based on mode)
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
            ticker: Stock ticker symbol
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: 'MKT' (market) or 'LMT' (limit)
            limit_price: Required for limit orders
        
        Returns:
            Order confirmation dictionary
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        try:
            # Get contract ID
            conid = self._get_conid(ticker)
            if not conid:
                raise ValueError(f"Could not find contract for {ticker}")
            
            # Build order payload
            side = "BUY" if action.upper() == "BUY" else "SELL"
            
            order_payload = {
                'acctId': self.account_id,
                'conid': conid,
                'secType': f'{conid}:STK',
                'orderType': order_type,
                'side': side,
                'quantity': quantity,
                'tif': 'DAY'  # Time in force: day order
            }
            
            if order_type == 'LMT':
                if not limit_price:
                    raise ValueError("limit_price required for limit orders")
                order_payload['price'] = limit_price
            
            # Submit order
            response = self.session.post(
                f"{self.base_url}/iserver/account/{self.account_id}/orders",
                json={'orders': [order_payload]},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # IBKR may require order confirmation
            if result and len(result) > 0:
                order_result = result[0]
                
                # Check if confirmation needed
                if 'id' in order_result:
                    # Order placed successfully
                    return {
                        'order_id': order_result['id'],
                        'status': 'SUBMITTED',
                        'message': order_result.get('message', 'Order submitted')
                    }
                elif 'message' in order_result:
                    # Confirmation or error message
                    return {
                        'order_id': None,
                        'status': 'PENDING_CONFIRMATION',
                        'message': order_result['message']
                    }
            
            return {
                'order_id': None,
                'status': 'ERROR',
                'message': 'Unexpected response from IBKR'
            }
            
        except Exception as e:
            print(f"❌ Failed to place order: {e}")
            return {
                'order_id': None,
                'status': 'ERROR',
                'message': str(e)
            }
    
    def get_order_status(self, order_id: str) -> Dict:
        """
        Get status of a specific order.
        
        Args:
            order_id: IBKR order ID
        
        Returns:
            Order status dictionary
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR. Call connect() first.")
        
        try:
            # Get live orders
            response = self.session.get(
                f"{self.base_url}/iserver/account/orders",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            orders = response.json()
            
            # Find matching order
            for order in orders.get('orders', []):
                if str(order.get('orderId')) == str(order_id):
                    return {
                        'order_id': order.get('orderId'),
                        'ticker': order.get('ticker'),
                        'action': 'BUY' if order.get('side') == 'BUY' else 'SELL',
                        'quantity': int(order.get('totalSize', 0)),
                        'order_type': order.get('orderType'),
                        'status': order.get('status'),
                        'filled_quantity': int(order.get('filledQuantity', 0)),
                        'avg_fill_price': float(order.get('avgPrice', 0)),
                        'timestamp': datetime.now()
                    }
            
            return {
                'order_id': order_id,
                'status': 'NOT_FOUND',
                'message': f'Order {order_id} not found'
            }
            
        except Exception as e:
            print(f"❌ Failed to get order status: {e}")
            return {
                'order_id': order_id,
                'status': 'ERROR',
                'message': str(e)
            }


# ============================================================================
# TESTING
# ============================================================================


    # ========================================================================
    # REAL-TIME MARKET DATA
    # ========================================================================
    
    def subscribe_market_data(self, tickers: List[str]) -> Dict:
        """
        Subscribe to real-time market data for given tickers.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary with subscription results per ticker
        """
        results = {}
        
        for ticker in tickers:
            try:
                # Get contract ID (conid) for ticker
                conid = self._get_conid(ticker)
                if not conid:
                    results[ticker] = {'success': False, 'error': f'Contract not found for {ticker}'}
                    continue
                
                # Subscribe to market data
                response = self.session.post(
                    f"{self.base_url}/iserver/marketdata/snapshot",
                    json={
                        "conids": [conid],
                        "fields": ["31", "84", "86", "7295"]  # Last, Bid, Ask, VWAP
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                results[ticker] = {
                    'success': True,
                    'conid': conid,
                    'data': response.json()
                }
                
            except Exception as e:
                results[ticker] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def get_market_snapshot(self, ticker: str) -> Optional[Dict]:
        """
        Get current market snapshot for a single ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Dictionary with current market data:
            {
                'ticker': str,
                'last_price': float,
                'bid': float,
                'ask': float,
                'vwap': float,
                'volume': int,
                'timestamp': datetime
            }
        """
        try:
            conid = self._get_conid(ticker)
            if not conid:
                return None
            
            response = self.session.get(
                f"{self.base_url}/iserver/marketdata/snapshot",
                params={
                    "conids": conid,
                    "fields": "31,84,86,87,7295"  # Last, Bid, Ask, Volume, VWAP
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if not data or len(data) == 0:
                return None
            
            snapshot = data[0]
            
            return {
                'ticker': ticker,
                'last_price': snapshot.get('31'),  # Last price
                'bid': snapshot.get('84'),  # Bid
                'ask': snapshot.get('86'),  # Ask
                'volume': snapshot.get('87'),  # Volume
                'vwap': snapshot.get('7295'),  # VWAP
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Error getting snapshot for {ticker}: {e}")
            return None
    
    def get_multiple_snapshots(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Get current market snapshots for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary mapping ticker to snapshot data
        """
        snapshots = {}
        
        for ticker in tickers:
            snapshot = self.get_market_snapshot(ticker)
            if snapshot:
                snapshots[ticker] = snapshot
            
            # Rate limiting
            time.sleep(0.1)  # 100ms between requests
        
        return snapshots
    
    def stream_market_data(self, tickers: List[str], callback, interval_ms: int = 100):
        """
        Stream real-time market data with callback.
        
        Args:
            tickers: List of ticker symbols
            callback: Function to call with each update
            interval_ms: Update interval in milliseconds
            
        Note: This is a polling implementation. For true streaming,
        use WebSocket connection (future enhancement).
        """
        interval_sec = interval_ms / 1000.0
        
        try:
            while True:
                snapshots = self.get_multiple_snapshots(tickers)
                callback(snapshots)
                time.sleep(interval_sec)
                
        except KeyboardInterrupt:
            print("Streaming stopped by user")

if __name__ == "__main__":
    print("IBKR Client Portal Gateway Connector - Test Suite")
    print("=" * 60)
    print("⚠️  Ensure Client Portal Gateway is running at https://localhost:5000")
    print("=" * 60)
    
    # Initialize connector (paper trading mode)
    account_id = input("\nEnter your IBKR account ID: ").strip()
    
    ibkr = IBKRConnector(
        account_id=account_id,
        paper_trading=True  # Use paper trading for testing
    )
    
    # Test 1: Connect
    print("\n1. Connecting to IBKR...")
    if ibkr.connect():
        print("   ✅ Connected successfully")
    else:
        print("   ❌ Connection failed")
        exit(1)
    
    # Test 2: Check connection health
    print("\n2. Checking connection health...")
    health = ibkr.check_connection()
    print(f"   Connected: {health['connected']}")
    print(f"   Authenticated: {health['authenticated']}")
    print(f"   Latency: {health['latency_ms']}ms")
    
    # Test 3: Get account balance
    print("\n3. Getting account balance...")
    try:
        balance = ibkr.get_account_balance()
        print(f"   Total Balance: ${balance['total_balance']:,.2f}")
        print(f"   Cash: ${balance['cash_balance']:,.2f}")
        print(f"   Deployed: ${balance['deployed_capital']:,.2f}")
        print(f"   Buying Power: ${balance['buying_power']:,.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Get positions
    print("\n4. Getting current positions...")
    try:
        positions = ibkr.get_positions()
        print(f"   Found {len(positions)} open positions")
        for pos in positions:
            print(f"     {pos['ticker']}: {pos['quantity']} shares @ ${pos['market_price']:.2f}")
            print(f"       Unrealized P&L: ${pos['unrealized_pnl']:.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Get fills
    print("\n5. Getting today's fills...")
    try:
        fills = ibkr.get_fills()
        print(f"   Found {len(fills)} fills today")
        if fills:
            sample = fills[0]
            print(f"   Sample: {sample['action']} {sample['quantity']} {sample['ticker']} @ ${sample['price']:.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Get historical data
    print("\n6. Getting historical data for AAPL...")
    try:
        df = ibkr.get_historical_data('AAPL', period_days=5, bar_size='1min')
        if df is not None:
            print(f"   ✅ Retrieved {len(df)} bars")
            print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"\n   Sample data:")
            print(df.head())
        else:
            print("   ⚠️  No data returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Disconnect
    print("\n7. Disconnecting...")
    ibkr.disconnect()
    
    print("\n" + "=" * 60)
    print("✅ Test suite complete!")
