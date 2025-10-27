"""
IBKR Data Provider - Production Implementation

Replaces RapidAPI/yfinance with direct IBKR Client Portal Gateway API.
Provides historical data, real-time quotes, and market scanning capabilities.

Key Features:
- 20-day historical tick/minute data from IBKR
- Real-time price snapshots via WebSocket
- Top 500 stock scanner by volume
- Production-grade error handling and retries

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from backend.data.ibkr_connector import IBKRConnector


class IBKRDataProvider:
    """
    Production IBKR data provider for morning report and live trading.
    
    Wraps IBKRConnector with convenience methods matching the old RapidAPI interface
    to enable drop-in replacement throughout the codebase.
    """
    
    def __init__(
        self,
        account_id: str = None,
        paper_trading: bool = True,
        gateway_url: str = "https://localhost:8000"
    ):
        """
        Initialize IBKR data provider.
        
        Args:
            account_id: IBKR account ID (reads from env if not provided)
            paper_trading: Use paper account (DU prefix)
            gateway_url: Client Portal Gateway URL
        """
        # Get account ID from environment if not provided
        if not account_id:
            account_id = os.getenv('IBKR_ACCOUNT_ID')
            if not account_id:
                raise ValueError("IBKR_ACCOUNT_ID must be set in environment or passed as argument")
        
        # Initialize IBKR connector
        self.connector = IBKRConnector(
            gateway_url=gateway_url,
            account_id=account_id,
            paper_trading=paper_trading
        )
        
        # Connect to gateway
        self.connected = self.connector.connect()
        if not self.connected:
            raise ConnectionError("Failed to connect to IBKR Client Portal Gateway")
    
    # ========================================================================
    # HISTORICAL DATA (20-day lookback for morning report)
    # ========================================================================
    
    def get_historical_data(
        self,
        ticker: str,
        interval: str = '1m',
        range_str: str = '20d',
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        Get historical intraday data from IBKR.
        
        Drop-in replacement for RapidAPIDataProvider.get_historical_data()
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            interval: Bar size ('1m', '5m', '15m', '1h', '1d')
            range_str: Time period ('5d', '20d', '1mo', etc.)
            **kwargs: Ignored for IBKR compatibility
        
        Returns:
            DataFrame with columns: [timestamp, open, high, low, close, volume]
            Indexed by timestamp
        """
        try:
            # Parse period string to days
            period_days = self._parse_period(range_str)
            
            # Convert interval format (yfinance style -> IBKR style)
            bar_size = self._convert_interval(interval)
            
            # Fetch from IBKR
            df = self.connector.get_historical_data(
                ticker=ticker,
                period_days=period_days,
                bar_size=bar_size
            )
            
            if df is None or df.empty:
                return None
            
            # Set timestamp as index (match RapidAPI interface)
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching historical data for {ticker}: {e}")
            return None
    
    def _parse_period(self, range_str: str) -> int:
        """Convert period string to days (e.g., '20d' -> 20, '1mo' -> 30)."""
        range_str = range_str.lower().strip()
        
        if range_str.endswith('d'):
            return int(range_str[:-1])
        elif range_str.endswith('mo'):
            return int(range_str[:-2]) * 30
        elif range_str.endswith('y'):
            return int(range_str[:-1]) * 365
        else:
            # Default to 20 days
            return 20
    
    def _convert_interval(self, interval: str) -> str:
        """Convert yfinance-style interval to IBKR bar size."""
        conversion_map = {
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '1h': '1h',
            '1d': '1d'
        }
        return conversion_map.get(interval, '1min')
    
    # ========================================================================
    # REAL-TIME DATA (live monitoring)
    # ========================================================================
    
    def get_current_price(self, ticker: str, **kwargs) -> Optional[float]:
        """
        Get current/latest price from IBKR.
        
        Drop-in replacement for RapidAPIDataProvider.get_current_price()
        
        Args:
            ticker: Stock symbol
            **kwargs: Ignored for IBKR compatibility
        
        Returns:
            Current price as float, or None if unavailable
        """
        try:
            snapshot = self.connector.get_market_snapshot(ticker)
            if not snapshot:
                return None
            
            # Try last price, then bid, then ask
            return (
                snapshot.get('31') or  # Last price
                snapshot.get('84') or  # Bid price
                snapshot.get('86')     # Ask price
            )
            
        except Exception as e:
            print(f"❌ Error fetching current price for {ticker}: {e}")
            return None
    
    def get_quote_data(self, ticker: str, **kwargs) -> Optional[Dict]:
        """
        Get full quote data from IBKR.
        
        Drop-in replacement for RapidAPIDataProvider.get_quote_data()
        
        Args:
            ticker: Stock symbol
            **kwargs: Ignored for IBKR compatibility
        
        Returns:
            Dictionary with quote data, or None if unavailable
        """
        try:
            snapshot = self.connector.get_market_snapshot(ticker)
            if not snapshot:
                return None
            
            # Map IBKR field codes to readable names
            return {
                'symbol': ticker,
                'current_price': snapshot.get('31'),      # Last price
                'bid': snapshot.get('84'),                # Bid price
                'ask': snapshot.get('86'),                # Ask price
                'bid_size': snapshot.get('88'),           # Bid size
                'ask_size': snapshot.get('85'),           # Ask size
                'volume': snapshot.get('87'),             # Volume
                'vwap': snapshot.get('7633'),             # VWAP
                'open': snapshot.get('7295'),             # Open price
                'high': snapshot.get('70'),               # High price
                'low': snapshot.get('71'),                # Low price
                'previous_close': snapshot.get('7295'),   # Previous close
                'change': snapshot.get('82'),             # Price change
                'change_pct': snapshot.get('83')          # % change
            }
            
        except Exception as e:
            print(f"❌ Error fetching quote data for {ticker}: {e}")
            return None
    
    # ========================================================================
    # MARKET SCANNING (top 500 stocks for morning report)
    # ========================================================================
    
    def scan_top_stocks(
        self,
        limit: int = 500,
        min_volume: int = 5_000_000,
        min_price: float = 5.0,
        exchanges: List[str] = None
    ) -> List[str]:
        """
        Scan IBKR for top stocks by volume.
        
        NEW METHOD - Returns dynamic list of top 500 liquid stocks.
        
        Args:
            limit: Maximum number of stocks to return (default 500)
            min_volume: Minimum average daily volume (default 5M)
            min_price: Minimum stock price (default $5)
            exchanges: List of exchanges (default: ['NYSE', 'NASDAQ'])
        
        Returns:
            List of ticker symbols sorted by volume (descending)
        
        Note: In Phase 1, this may use a curated fallback list if IBKR
              market scanner is not yet implemented. Phase 2 will use
              IBKR's native scanner API.
        """
        if exchanges is None:
            exchanges = ['NYSE', 'NASDAQ']
        
        try:
            # Use IBKR market scanner
            tickers = self.connector.get_top_stocks_by_volume(
                limit=limit,
                min_volume=min_volume,
                min_price=min_price
            )
            
            if tickers and len(tickers) > 0:
                print(f"✅ Scanned {len(tickers)} stocks from IBKR (target: {limit})")
                return tickers
            else:
                print("⚠️  IBKR scanner returned no results. Using fallback.")
                return self._get_fallback_universe(limit)
            
        except Exception as e:
            print(f"❌ Error scanning top stocks: {e}. Using fallback.")
            return self._get_fallback_universe(limit)
    
    def _get_fallback_universe(self, limit: int = 500) -> List[str]:
        """
        Fallback stock universe from stock_universe.py.
        
        This is temporary - will be replaced with dynamic IBKR scanner.
        """
        try:
            from backend.data.stock_universe import get_all_stocks
            all_stocks = get_all_stocks()
            return all_stocks[:limit]
        except ImportError:
            # Hard fallback if import fails
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B',
                'JPM', 'JNJ', 'V', 'PG', 'XOM', 'UNH', 'HD', 'MA', 'BAC', 'ABBV',
                'COST', 'PFE', 'DIS', 'AVGO', 'KO', 'PEP', 'TMO', 'WMT', 'MRK',
                'CSCO', 'ABT', 'ACN', 'CVX', 'NKE', 'DHR', 'CMCSA', 'LIN', 'VZ',
                'ADBE', 'WFC', 'NEE', 'TXN', 'PM', 'UPS', 'BMY', 'ORCL', 'COP',
                'MS', 'RTX', 'HON', 'QCOM', 'INTC', 'AMGN', 'IBM', 'SBUX', 'LOW'
            ][:limit]
    
    # ========================================================================
    # BULK DATA FETCHING (parallel data loading for morning report)
    # ========================================================================
    
    def get_multiple_historical(
        self,
        tickers: List[str],
        interval: str = '1m',
        range_str: str = '20d'
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical data for multiple tickers efficiently.
        
        NEW METHOD - Optimized for morning report batch loading.
        
        Args:
            tickers: List of ticker symbols
            interval: Bar size
            range_str: Time period
        
        Returns:
            Dictionary mapping ticker -> DataFrame
        """
        results = {}
        
        for ticker in tickers:
            df = self.get_historical_data(ticker, interval, range_str)
            if df is not None and not df.empty:
                results[ticker] = df
        
        return results
    
    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================
    
    def disconnect(self):
        """Disconnect from IBKR gateway."""
        if self.connector:
            self.connector.disconnect()
            self.connected = False


# ============================================================================
# GLOBAL SINGLETON INSTANCE
# ============================================================================

_data_provider = None

def get_data_provider(force_new: bool = False) -> IBKRDataProvider:
    """
    Get or create the global IBKR data provider instance.
    
    Args:
        force_new: Force creation of new instance (useful for reconnecting)
    
    Returns:
        IBKRDataProvider singleton
    """
    global _data_provider
    
    if _data_provider is None or force_new:
        _data_provider = IBKRDataProvider()
    
    return _data_provider


# ============================================================================
# STANDALONE FUNCTION (drop-in replacement for morning report)
# ============================================================================

def fetch_market_data(
    ticker: str,
    period: str = "20d",
    interval: str = "1m",
    use_simulation: bool = False
) -> Optional[pd.DataFrame]:
    """
    Standalone function to fetch market data for a single ticker.
    
    Drop-in replacement for data_provider.fetch_market_data()
    
    Args:
        ticker: Stock symbol
        period: Time period (e.g., "20d", "1mo")
        interval: Data interval (e.g., "1m", "5m")
        use_simulation: Use mock data for testing
    
    Returns:
        DataFrame with OHLCV data or None if unavailable
    """
    if use_simulation:
        # Return mock data for testing
        dates = pd.date_range(end=datetime.now(), periods=20*390, freq='1min')
        np.random.seed(hash(ticker) % 10000)
        
        base_price = 100 + np.random.rand() * 100
        returns = np.random.randn(len(dates)) * 0.001
        prices = base_price * (1 + returns).cumprod()
        
        return pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * 1.002,
            'low': prices * 0.998,
            'close': prices,
            'volume': np.random.randint(100000, 1000000, len(dates))
        }).set_index('timestamp')
    
    # Production: Use IBKR data provider
    try:
        provider = get_data_provider()
        return provider.get_historical_data(ticker, interval=interval, range_str=period)
    except Exception as e:
        print(f"❌ Failed to fetch data for {ticker}: {e}")
        return None
