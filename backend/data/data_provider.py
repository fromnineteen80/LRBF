"""
RapidAPI Yahoo Finance Data Provider

This module replaces the free yfinance library with the paid RapidAPI Yahoo Finance API.
Provides historical intraday data for pattern detection and live price data.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import sys
sys.path.append('/home/claude/railyard')

import requests
import pandas as pd
import numpy as np
from typing import Optional, Dict
from datetime import datetime, timedelta
from config import TradingConfig as cfg


class RapidAPIDataProvider:
    """Handles all market data requests via RapidAPI Yahoo Finance."""
    
    def __init__(self, api_key: str = None, api_host: str = None):
        """
        Initialize the data provider.
        
        Args:
            api_key: RapidAPI key (defaults to config)
            api_host: RapidAPI host (defaults to config)
        """
        self.api_key = api_key or cfg.RAPIDAPI_KEY
        self.api_host = api_host or cfg.RAPIDAPI_HOST
        self.base_url = f'https://{self.api_host}/api/stock'
        
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """
        Make a request to the RapidAPI Yahoo Finance API.
        
        Args:
            endpoint: API endpoint (e.g., 'get-chart', 'get-price')
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        url = f'{self.base_url}/{endpoint}'
        headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.api_host
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_historical_data(
        self,
        ticker: str,
        interval: str = '1m',
        range_str: str = '5d',
        region: str = 'US'
    ) -> Optional[pd.DataFrame]:
        """
        Get historical intraday data for a ticker.
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            interval: Data interval ('1m', '5m', '15m', '1h', '1d')
            range_str: Time range ('1d', '5d', '1mo', '3mo', '1y')
            region: Market region ('US', 'AU', etc.)
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
            Returns None if request fails
        """
        try:
            params = {
                'symbol': ticker,
                'interval': interval,
                'range': range_str,
                'region': region
            }
            
            data = self._make_request('get-chart', params)
            
            # Parse the response
            if not data.get('chart') or not data['chart'].get('result'):
                return None
                
            result = data['chart']['result'][0]
            timestamps = result.get('timestamp', [])
            quotes = result.get('indicators', {}).get('quote', [{}])[0]
            
            if not timestamps or not quotes:
                return None
            
            # Build DataFrame
            df = pd.DataFrame({
                'timestamp': [datetime.fromtimestamp(ts) for ts in timestamps],
                'open': quotes.get('open', []),
                'high': quotes.get('high', []),
                'low': quotes.get('low', []),
                'close': quotes.get('close', []),
                'volume': quotes.get('volume', [])
            })
            
            # Clean data - remove rows with None values
            df = df.dropna()
            
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
    
    def get_current_price(self, ticker: str, region: str = 'US') -> Optional[float]:
        """
        Get current/latest price for a ticker.
        
        Args:
            ticker: Stock symbol
            region: Market region
            
        Returns:
            Current price as float, or None if request fails
        """
        try:
            params = {
                'symbol': ticker,
                'region': region
            }
            
            data = self._make_request('get-price', params)
            
            # Navigate to price data
            result = data.get('quoteSummary', {}).get('result', [{}])[0]
            price_data = result.get('price', {})
            
            # Try regular market price first, then post-market
            price = price_data.get('regularMarketPrice', {}).get('raw')
            if price is None:
                price = price_data.get('postMarketPrice', {}).get('raw')
                
            return price
            
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            return None
    
    def get_quote_data(self, ticker: str, region: str = 'US') -> Optional[Dict]:
        """
        Get full quote data including volume, market cap, etc.
        
        Args:
            ticker: Stock symbol
            region: Market region
            
        Returns:
            Dictionary with quote data, or None if request fails
        """
        try:
            params = {
                'symbol': ticker,
                'region': region
            }
            
            data = self._make_request('get-price', params)
            
            result = data.get('quoteSummary', {}).get('result', [{}])[0]
            price_data = result.get('price', {})
            
            return {
                'symbol': price_data.get('symbol'),
                'current_price': price_data.get('regularMarketPrice', {}).get('raw'),
                'previous_close': price_data.get('regularMarketPreviousClose', {}).get('raw'),
                'open': price_data.get('regularMarketOpen', {}).get('raw'),
                'day_high': price_data.get('regularMarketDayHigh', {}).get('raw'),
                'day_low': price_data.get('regularMarketDayLow', {}).get('raw'),
                'volume': price_data.get('regularMarketVolume', {}).get('raw'),
                'market_cap': price_data.get('marketCap', {}).get('raw'),
                'exchange': price_data.get('exchange'),
                'currency': price_data.get('currency')
            }
            
        except Exception as e:
            print(f"Error fetching quote for {ticker}: {e}")
            return None


# Global singleton instance
_data_provider = None

def get_data_provider() -> RapidAPIDataProvider:
    """Get or create the global data provider instance."""
    global _data_provider
    if _data_provider is None:
        _data_provider = RapidAPIDataProvider()
    return _data_provider
