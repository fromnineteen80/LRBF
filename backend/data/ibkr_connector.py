"""
IBKR API Connector - Phase 3, Checkpoint 3.1

Connects to Interactive Brokers API to retrieve:
- Account balance and margin availability
- Recent fills (trade executions)
- Current positions
- Order status

For development/testing, includes simulation mode that generates realistic data.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
sys.path.append('/home/claude/railyard')

from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
import random
import time
from config import TradingConfig as cfg


class IBKRConnector:
    """
    Interface to Interactive Brokers API.
    
    In production, this connects to IBKR's REST API or TWS API.
    In simulation mode, generates realistic test data for development.
    """
    
    def __init__(self, use_simulation: bool = True, account_id: str = None):
        """
        Initialize IBKR connector.
        
        Args:
            use_simulation: Use simulated data if True (for development)
            account_id: IBKR account ID (required for production)
        """
        self.use_simulation = use_simulation
        self.account_id = account_id
        self.connected = False
        
        # Simulation state
        self.sim_balance = cfg.SIMULATION_STARTING_BALANCE
        self.sim_fills = []
        self.sim_positions = {}
        self.sim_trades_today = 0
        
        if not use_simulation:
            # TODO: Initialize actual IBKR connection
            # This would use ib_insync or similar library
            # For now, we'll focus on simulation mode
            raise NotImplementedError("Production IBKR connection not yet implemented")
    
    def connect(self) -> bool:
        """
        Establish connection to IBKR.
        
        Returns:
            True if connection successful
        """
        if self.use_simulation:
            self.connected = True
            return True
        else:
            # TODO: Implement actual IBKR connection
            raise NotImplementedError("Production IBKR connection not yet implemented")
    
    def disconnect(self):
        """Close IBKR connection."""
        self.connected = False
    
    # ========================================================================
    # ACCOUNT DATA
    # ========================================================================
    
    def get_account_balance(self) -> Dict:
        """
        Get current account balance and margin information.
        
        Returns:
            Dictionary with account data:
            {
                'total_balance': float,      # Total account value
                'cash_balance': float,       # Available cash
                'margin_available': float,   # Available margin
                'buying_power': float,       # Total buying power
                'deployed_capital': float,   # Currently in positions
                'reserve_capital': float,    # Held in reserve
                'timestamp': datetime        # Data timestamp
            }
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")
        
        if self.use_simulation:
            return self._sim_get_account_balance()
        else:
            # TODO: Implement actual IBKR API call
            raise NotImplementedError("Production IBKR API not yet implemented")
    
    def _sim_get_account_balance(self) -> Dict:
        """Simulated account balance for testing."""
        
        # Calculate based on today's simulated performance
        total = self.sim_balance
        deployed = total * cfg.DEPLOYMENT_RATIO
        reserve = total * cfg.RESERVE_RATIO
        
        return {
            'total_balance': total,
            'cash_balance': reserve,
            'margin_available': reserve * 2,  # 2:1 margin
            'buying_power': total + (reserve * 2),
            'deployed_capital': deployed,
            'reserve_capital': reserve,
            'timestamp': datetime.now()
        }
    
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
                'realized_pnl': float,      # Realized P&L (for SELL orders)
                'commission': float,        # Commission paid
            }
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")
        
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today()
        
        if self.use_simulation:
            return self._sim_get_fills(start_date, end_date, ticker)
        else:
            # TODO: Implement actual IBKR API call
            raise NotImplementedError("Production IBKR API not yet implemented")
    
    def _sim_get_fills(
        self,
        start_date: date,
        end_date: date,
        ticker: str = None
    ) -> List[Dict]:
        """Simulated fills for testing."""
        
        # Generate realistic fills for today if none exist
        if date.today() == start_date and not self.sim_fills:
            self._sim_generate_fills()
        
        # Filter by date and ticker
        fills = []
        for fill in self.sim_fills:
            fill_date = fill['timestamp'].date()
            if start_date <= fill_date <= end_date:
                if ticker is None or fill['ticker'] == ticker:
                    fills.append(fill)
        
        return fills
    
    def _sim_generate_fills(self):
        """Generate realistic simulated fills for testing."""
        
        # Simulate 80-120 trades today based on forecast
        # These ranges come from expected performance in morning scanner
        num_trades = random.randint(80, 120)
        
        # Typical stocks - in production, these come from morning forecast
        # For simulation, use a representative sample
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD']
        
        now = datetime.now()
        market_open = now.replace(hour=9, minute=31, second=0)
        market_close = now.replace(hour=16, minute=0, second=0)
        
        # Generate pairs of BUY/SELL fills
        execution_id = 1
        total_pl = 0
        
        # Expected win rate from pattern analysis (~65-75%)
        expected_win_rate = 0.70
        
        for i in range(num_trades // 2):  # Pairs of trades
            ticker = random.choice(tickers)
            
            # BUY fill
            buy_time = market_open + timedelta(
                seconds=random.randint(0, int((market_close - market_open).total_seconds()))
            )
            buy_price = random.uniform(100, 300)
            
            # Position size from config: deployed capital / num_stocks
            # Simulating $3000 position size (from $30K * 80% / 8)
            deployed = self.sim_balance * cfg.DEPLOYMENT_RATIO
            position_size = deployed / cfg.NUM_STOCKS
            quantity = int(position_size / buy_price)
            
            buy_fill = {
                'ibkr_execution_id': f'SIM{execution_id:06d}',
                'timestamp': buy_time,
                'ticker': ticker,
                'action': 'BUY',
                'quantity': quantity,
                'price': buy_price,
                'realized_pnl': 0,
                'commission': 1.00
            }
            self.sim_fills.append(buy_fill)
            execution_id += 1
            
            # SELL fill - simulate win/loss based on expected win rate
            sell_time = buy_time + timedelta(minutes=random.randint(2, 30))
            
            if random.random() < expected_win_rate:  # Win
                # Use actual target percentages from config
                profit_pct = random.uniform(cfg.TARGET_1, cfg.TARGET_2)
                sell_price = buy_price * (1 + profit_pct / 100)
            else:  # Loss
                # Use actual stop loss from config
                sell_price = buy_price * (1 + cfg.STOP_LOSS / 100)
            
            realized_pl = (sell_price - buy_price) * quantity - 2.00  # Commissions
            total_pl += realized_pl
            
            sell_fill = {
                'ibkr_execution_id': f'SIM{execution_id:06d}',
                'timestamp': sell_time,
                'ticker': ticker,
                'action': 'SELL',
                'quantity': quantity,
                'price': sell_price,
                'realized_pnl': realized_pl,
                'commission': 1.00
            }
            self.sim_fills.append(sell_fill)
            execution_id += 1
        
        # Update simulated balance
        self.sim_balance += total_pl
        self.sim_trades_today = len(self.sim_fills) // 2
    
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
            raise ConnectionError("Not connected to IBKR")
        
        if self.use_simulation:
            return self._sim_get_positions()
        else:
            # TODO: Implement actual IBKR API call
            raise NotImplementedError("Production IBKR API not yet implemented")
    
    def _sim_get_positions(self) -> List[Dict]:
        """Simulated positions for testing."""
        
        # In simulation, we assume intraday-only trading
        # So positions list is typically empty (all closed by EOD)
        # But for testing, we might show 1-2 open positions
        
        if random.random() > 0.7:  # 30% chance of having open positions
            ticker = random.choice(['AAPL', 'MSFT', 'GOOGL'])
            quantity = random.randint(5, 15)
            avg_cost = random.uniform(100, 300)
            market_price = avg_cost * random.uniform(0.99, 1.02)
            
            return [{
                'ticker': ticker,
                'quantity': quantity,
                'avg_cost': avg_cost,
                'market_price': market_price,
                'market_value': market_price * quantity,
                'unrealized_pnl': (market_price - avg_cost) * quantity,
                'position_pct': (market_price * quantity) / self.sim_balance
            }]
        
        return []
    
    # ========================================================================
    # ORDERS
    # ========================================================================
    
    def get_order_status(self, order_id: str) -> Dict:
        """
        Get status of a specific order.
        
        Args:
            order_id: IBKR order ID
        
        Returns:
            Order status dictionary:
            {
                'order_id': str,
                'ticker': str,
                'action': str,           # 'BUY' or 'SELL'
                'quantity': int,
                'order_type': str,       # 'MARKET', 'LIMIT', etc.
                'status': str,           # 'SUBMITTED', 'FILLED', 'CANCELLED'
                'filled_quantity': int,
                'avg_fill_price': float,
                'timestamp': datetime
            }
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")
        
        if self.use_simulation:
            return self._sim_get_order_status(order_id)
        else:
            # TODO: Implement actual IBKR API call
            raise NotImplementedError("Production IBKR API not yet implemented")
    
    def _sim_get_order_status(self, order_id: str) -> Dict:
        """Simulated order status for testing."""
        
        # For simulation, assume all orders fill immediately
        return {
            'order_id': order_id,
            'ticker': 'AAPL',
            'action': 'BUY',
            'quantity': 10,
            'order_type': 'MARKET',
            'status': 'FILLED',
            'filled_quantity': 10,
            'avg_fill_price': 150.25,
            'timestamp': datetime.now()
        }
    
    # ========================================================================
    # CONNECTION HEALTH
    # ========================================================================
    # HISTORICAL DATA
    # ========================================================================
    
    def get_historical_data(
        self,
        ticker: str,
        period_days: int = 20,
        bar_size: str = "1 min",
        what_to_show: str = "TRADES"
    ):
        """
        Get historical 1-minute bar data from IBKR.
        
        Args:
            ticker: Stock ticker symbol
            period_days: Number of days of historical data (default: 20)
            bar_size: Bar interval (default: "1 min")
            what_to_show: Data type (default: "TRADES")
        
        Returns:
            DataFrame with columns: [timestamp, open, high, low, close, volume]
            Returns None if data fetch fails
        """
        if not self.connected:
            raise ConnectionError("Not connected to IBKR")
        
        if self.use_simulation:
            return self._sim_get_historical_data(ticker, period_days, bar_size)
        else:
            return self._prod_get_historical_data(ticker, period_days, bar_size, what_to_show)
    
    def _prod_get_historical_data(
        self,
        ticker: str,
        period_days: int,
        bar_size: str,
        what_to_show: str
    ):
        """
        Production: Fetch historical data from IBKR Client Portal Gateway API.
        
        IBKR Endpoint: /v1/api/iserver/marketdata/history
        """
        import pandas as pd
        
        base_url = "https://localhost:5000/v1/api"
        bar_size_param = bar_size.replace(" ", "")
        period_param = f"{period_days}d"
        
        search_url = f"{base_url}/iserver/secdef/search"
        search_params = {
            "symbol": ticker,
            "secType": "STK",
            "name": "false"
        }
        
        try:
            search_response = requests.get(search_url, params=search_params, verify=False)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            if not search_data:
                return None
            
            conid = search_data[0]['conid']
            
            history_url = f"{base_url}/iserver/marketdata/history"
            history_params = {
                "conid": conid,
                "period": period_param,
                "bar": bar_size_param,
                "outsideRth": "false"
            }
            
            history_response = requests.get(history_url, params=history_params, verify=False)
            history_response.raise_for_status()
            history_data = history_response.json()
            
            bars = history_data.get('data', [])
            if not bars:
                return None
            
            df = pd.DataFrame(bars)
            df.rename(columns={'t': 'timestamp', 'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'}, inplace=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            print(f"❌ IBKR API error for {ticker}: {e}")
            return None
    
    def _sim_get_historical_data(self, ticker: str, period_days: int, bar_size: str):
        """Simulation: Generate realistic historical data for testing."""
        try:
            from backend.core.batch_analyzer import generate_simulated_stock_data
            period_str = f"{period_days}d"
            interval = bar_size.replace(" ", "").replace("min", "m")
            return generate_simulated_stock_data(ticker, period_str, interval)
        except Exception as e:
            print(f"❌ Error generating simulated data: {e}")
            return None


    # ========================================================================
    
    def check_connection(self) -> Dict:
        """
        Check connection health and latency.
        
        Returns:
            Dictionary with connection metrics:
            {
                'connected': bool,
                'latency_ms': float,      # Round-trip latency
                'last_heartbeat': datetime,
                'api_version': str
            }
        """
        if not self.connected:
            return {
                'connected': False,
                'latency_ms': None,
                'last_heartbeat': None,
                'api_version': None
            }
        
        if self.use_simulation:
            return {
                'connected': True,
                'latency_ms': random.uniform(10, 50),  # Realistic latency
                'last_heartbeat': datetime.now(),
                'api_version': 'SIMULATION_1.0'
            }
        else:
            # TODO: Implement actual health check
            raise NotImplementedError("Production IBKR API not yet implemented")


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("Testing IBKR Connector (Simulation Mode)...")
    print("=" * 60)
    
    # Initialize connector
    ibkr = IBKRConnector(use_simulation=True)
    
    # Test 1: Connect
    print("\n1. Connecting to IBKR...")
    success = ibkr.connect()
    print(f"   {'✅' if success else '❌'} Connected: {success}")
    
    # Test 2: Get account balance
    print("\n2. Getting account balance...")
    balance = ibkr.get_account_balance()
    print(f"   Total Balance: ${balance['total_balance']:,.2f}")
    print(f"   Deployed: ${balance['deployed_capital']:,.2f}")
    print(f"   Reserve: ${balance['reserve_capital']:,.2f}")
    
    # Test 3: Get fills
    print("\n3. Getting today's fills...")
    fills = ibkr.get_fills()
    print(f"   Found {len(fills)} fills")
    
    if fills:
        buy_fills = [f for f in fills if f['action'] == 'BUY']
        sell_fills = [f for f in fills if f['action'] == 'SELL']
        total_pl = sum(f['realized_pnl'] for f in sell_fills)
        
        print(f"   BUY fills: {len(buy_fills)}")
        print(f"   SELL fills: {len(sell_fills)}")
        print(f"   Total P&L: ${total_pl:,.2f}")
        
        # Show a sample fill
        if len(fills) > 0:
            sample = fills[0]
            print(f"\n   Sample fill:")
            print(f"     ID: {sample['ibkr_execution_id']}")
            print(f"     {sample['action']} {sample['quantity']} {sample['ticker']} @ ${sample['price']:.2f}")
            print(f"     Time: {sample['timestamp'].strftime('%H:%M:%S')}")
    
    # Test 4: Get positions
    print("\n4. Getting current positions...")
    positions = ibkr.get_positions()
    print(f"   Open positions: {len(positions)}")
    
    for pos in positions:
        print(f"     {pos['ticker']}: {pos['quantity']} shares @ ${pos['avg_cost']:.2f}")
        print(f"       Unrealized P&L: ${pos['unrealized_pnl']:.2f}")
    
    # Test 5: Check connection health
    print("\n5. Checking connection health...")
    health = ibkr.check_connection()
    print(f"   Connected: {health['connected']}")
    print(f"   Latency: {health['latency_ms']:.1f}ms")
    print(f"   API Version: {health['api_version']}")
    
    # Test 6: Filter fills by ticker
    print("\n6. Testing ticker filtering...")
    if fills:
        test_ticker = fills[0]['ticker']
        ticker_fills = ibkr.get_fills(ticker=test_ticker)
        print(f"   {test_ticker} fills: {len(ticker_fills)}")
    
    # Disconnect
    ibkr.disconnect()
    print("\n" + "=" * 60)
    print("✅ All IBKR connector tests passed!")
