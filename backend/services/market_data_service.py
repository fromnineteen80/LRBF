"""
Market Data Service - Fetch Real Intraminute Data

Uses yfinance for testing, with hooks for IBKR API integration later.

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Optional, List
import time


class MarketDataService:
    """
    Fetch market data from yfinance (testing) or IBKR (production).
    """
    
    def __init__(self, data_source: str = 'yfinance'):
        """
        Initialize market data service.
        
        Args:
            data_source: 'yfinance' or 'ibkr'
        """
        self.data_source = data_source
        print(f"📊 Market data source: {data_source}")
    
    def get_intraday_data(
        self,
        ticker: str,
        days: int = 20,
        interval: str = '1m'
    ) -> pd.DataFrame:
        """
        Fetch intraminute data for a stock.
        
        Args:
            ticker: Stock symbol
            days: Number of days of history
            interval: Data interval ('1m', '5m', etc.)
        
        Returns:
            DataFrame with OHLCV data
        """
        if self.data_source == 'yfinance':
            return self._fetch_yfinance(ticker, days, interval)
        elif self.data_source == 'ibkr':
            return self._fetch_ibkr(ticker, days, interval)
        else:
            raise ValueError(f"Unknown data source: {self.data_source}")
    
    def _fetch_yfinance(
        self,
        ticker: str,
        days: int,
        interval: str
    ) -> pd.DataFrame:
        """
        Fetch data from yfinance.
        
        Note: yfinance only provides last 7 days of 1m data.
        For 20-day history, we'll use 5m data and resample.
        
        Args:
            ticker: Stock symbol
            days: Days of history
            interval: Interval
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # yfinance limitation: 1m data only for last 7 days
            # For 20-day testing, use 5m data
            if days > 7 and interval == '1m':
                print(f"   ⚠️  yfinance limits 1m data to 7 days - using 5m for {ticker}")
                interval = '5m'
                period = f"{days}d"
            else:
                period = f"{min(days, 7)}d"
            
            # Fetch data
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                print(f"   ❌ No data for {ticker}")
                return pd.DataFrame()
            
            # Clean and standardize
            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]
            
            # Rename datetime column to timestamp
            if 'datetime' in df.columns:
                df.rename(columns={'datetime': 'timestamp'}, inplace=True)
            
            # Ensure required columns
            required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required):
                print(f"   ❌ Missing columns for {ticker}: {df.columns.tolist()}")
                return pd.DataFrame()
            
            df = df[required]
            
            print(f"   ✅ {ticker}: {len(df)} bars ({df['timestamp'].min()} to {df['timestamp'].max()})")
            
            return df
            
        except Exception as e:
            print(f"   ❌ Error fetching {ticker}: {str(e)}")
            return pd.DataFrame()
    
    def _fetch_ibkr(
        self,
        ticker: str,
        days: int,
        interval: str
    ) -> pd.DataFrame:
        """
        Fetch data from IBKR API (placeholder for future implementation).
        
        Args:
            ticker: Stock symbol
            days: Days of history
            interval: Interval
        
        Returns:
            DataFrame with OHLCV data
        """
        # TODO: Implement IBKR API integration
        raise NotImplementedError("IBKR integration not yet implemented")
    
    def get_batch_data(
        self,
        tickers: List[str],
        days: int = 20,
        interval: str = '1m',
        delay_ms: int = 200
    ) -> dict:
        """
        Fetch data for multiple tickers (rate-limited).
        
        Args:
            tickers: List of stock symbols
            days: Days of history
            interval: Interval
            delay_ms: Delay between requests (rate limiting)
        
        Returns:
            Dictionary mapping ticker -> DataFrame
        """
        results = {}
        
        print(f"\n📥 Fetching data for {len(tickers)} tickers...")
        
        for i, ticker in enumerate(tickers, 1):
            print(f"[{i}/{len(tickers)}] {ticker}", end=" ")
            
            df = self.get_intraday_data(ticker, days, interval)
            
            if not df.empty:
                results[ticker] = df
            
            # Rate limiting
            if i < len(tickers):
                time.sleep(delay_ms / 1000)
        
        print(f"\n✅ Fetched data for {len(results)}/{len(tickers)} tickers")
        
        return results


# Convenience functions
def fetch_stock_data(ticker: str, days: int = 20) -> pd.DataFrame:
    """Fetch data for single stock."""
    service = MarketDataService()
    return service.get_intraday_data(ticker, days)


def fetch_batch_data(tickers: List[str], days: int = 20) -> dict:
    """Fetch data for multiple stocks."""
    service = MarketDataService()
    return service.get_batch_data(tickers, days)
