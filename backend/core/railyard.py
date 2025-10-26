"""
Railyard.py - Proprietary Trading Execution Engine

Replaces Capitalise.ai with our own execution logic.
Monitors VWAP recovery patterns and executes trades via IBKR API.

Architecture:
- Real-time pattern monitoring (100ms updates)
- Direct IBKR integration (no third-party fees)
- Supports both default and enhanced strategies
- Position management with strict risk controls
- Daily loss limit enforcement

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import logging

from backend.data.ibkr_connector import IBKRConnector
from backend.core.pattern_detector import PatternDetector
from backend.core.filter_engine import FilterEngine
from backend.data.storage_manager import StorageManager
from config.config import TradingConfig, IBKRConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RailyardEngine:
    """
    Core trading execution engine.
    
    Features:
    - Real-time VWAP recovery pattern detection
    - Direct IBKR trade execution
    - Position management (1 position per ticker)
    - Risk management (stop loss, daily loss limit)
    - Dual-strategy support (default vs enhanced)
    """
    
    def __init__(
        self,
        ibkr_connector: Optional[IBKRConnector] = None,
        config: Optional[TradingConfig] = None,
        strategy: str = 'default',
        use_filters: bool = False
    ):
        """
        Initialize Railyard engine.
        
        Args:
            ibkr_connector: IBKR connection (creates new if None)
            config: Trading configuration (uses default if None)
            strategy: 'default' or 'enhanced'
            use_filters: Apply quality/timing/confluence filters
        """
        self.config = config or TradingConfig()
        self.strategy = strategy
        self.use_filters = use_filters
        
        # Initialize IBKR connection
        IBKRConfig.load_from_env()
        self.ibkr = ibkr_connector or IBKRConnector(
            gateway_url=IBKRConfig.GATEWAY_URL,
            account_id=IBKRConfig.ACCOUNT_ID,
            paper_trading=IBKRConfig.PAPER_TRADING
        )
        
        # Connect to IBKR
        if not self.ibkr.connect():
            raise ConnectionError("Failed to connect to IBKR Gateway")
        
        # Pattern detector
        self.pattern_detector = PatternDetector(self.config)
        
        # Filter engine (if using enhanced strategy)
        self.filter_engine = FilterEngine(self.config) if use_filters else None
        
        # Storage manager
        self.storage = StorageManager()
        
        # Trading state
        self.active_positions = {}  # ticker -> position_info
        self.pending_orders = {}    # ticker -> order_info
        self.daily_pnl = 0.0
        self.trade_count = 0
        self.is_running = False
        self.start_time = None
        
        # Selected tickers (loaded from morning report)
        self.selected_tickers = []
        
        # Account info
        self.account_balance = 0.0
        self.starting_balance = 0.0
        
        logger.info(f"Railyard Engine initialized (strategy: {strategy}, filters: {use_filters})")
    
    def load_morning_forecast(self, date: str = None) -> bool:
        """
        Load selected tickers from morning forecast.
        
        Args:
            date: Date string (YYYY-MM-DD), uses today if None
            
        Returns:
            True if forecast loaded successfully
        """
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Load forecast from database
            forecast = self.storage.get_morning_forecast(date)
            
            if not forecast:
                logger.error(f"No morning forecast found for {date}")
                return False
            
            # Extract selected tickers
            selected_stocks_json = forecast.get('selected_stocks_json', '[]')
            self.selected_tickers = json.loads(selected_stocks_json)
            
            logger.info(f"Loaded {len(self.selected_tickers)} tickers from morning forecast")
            logger.info(f"Tickers: {', '.join(self.selected_tickers)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading morning forecast: {e}")
            return False
    
    def start_trading(self, tickers: List[str] = None):
        """
        Start the trading loop.
        
        Args:
            tickers: List of tickers to trade (uses morning forecast if None)
        """
        # Load tickers
        if tickers:
            self.selected_tickers = tickers
        elif not self.selected_tickers:
            if not self.load_morning_forecast():
                logger.error("No tickers to trade. Exiting.")
                return
        
        # Get starting balance
        balance_info = self.ibkr.get_account_balance()
        if balance_info and 'net_liquidation' in balance_info:
            self.starting_balance = balance_info['net_liquidation']
            self.account_balance = self.starting_balance
            logger.info(f"Starting balance: ${self.account_balance:,.2f}")
        else:
            logger.error("Could not retrieve account balance")
            return
        
        # Subscribe to market data
        logger.info("Subscribing to market data...")
        self.ibkr.subscribe_market_data(self.selected_tickers)
        time.sleep(2)  # Wait for subscriptions to complete
        
        # Start trading loop
        self.is_running = True
        self.start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("TRADING STARTED")
        logger.info(f"Strategy: {self.strategy}")
        logger.info(f"Filters: {'ON' if self.use_filters else 'OFF'}")
        logger.info(f"Tickers: {len(self.selected_tickers)}")
        logger.info(f"Market open: {self.config.MARKET_OPEN}")
        logger.info(f"Market close: {self.config.MARKET_CLOSE}")
        logger.info(f"Entry cutoff: {self.config.ENTRY_CUTOFF}")
        logger.info("=" * 60)
        
        try:
            self._trading_loop()
        except KeyboardInterrupt:
            logger.info("Trading stopped by user")
        finally:
            self._shutdown()
    
    def _trading_loop(self):
        """
        Main trading loop.
        Runs every 100ms to monitor patterns and manage positions.
        """
        update_interval = IBKRConfig.REALTIME_UPDATE_INTERVAL_MS / 1000  # Convert to seconds
        
        while self.is_running:
            loop_start = time.time()
            
            # Check if we should stop trading
            if not self._is_trading_time():
                logger.info("Trading session ended")
                break
            
            # Check daily loss limit
            if self._check_daily_loss_limit():
                logger.warning("Daily loss limit hit. Stopping trading.")
                break
            
            # Update account balance
            self._update_account_balance()
            
            # Scan all tickers for patterns
            for ticker in self.selected_tickers:
                try:
                    # Skip if already have position
                    if ticker in self.active_positions:
                        self._manage_position(ticker)
                        continue
                    
                    # Skip if pending order
                    if ticker in self.pending_orders:
                        continue
                    
                    # Get market snapshot
                    snapshot = self.ibkr.get_market_snapshot(ticker)
                    if not snapshot:
                        continue
                    
                    # Check for entry pattern
                    self._check_entry_signal(ticker, snapshot)
                    
                except Exception as e:
                    logger.error(f"Error processing {ticker}: {e}")
            
            # Sleep to maintain update interval
            elapsed = time.time() - loop_start
            sleep_time = max(0, update_interval - elapsed)
            time.sleep(sleep_time)
    
    def _check_entry_signal(self, ticker: str, snapshot: Dict):
        """
        Check if ticker shows entry pattern.
        
        Args:
            ticker: Ticker symbol
            snapshot: Market snapshot with current price/volume/VWAP
        """
        # Get recent historical data (20 days, 1-minute bars)
        hist = self.ibkr.get_historical_data(
            ticker,
            period=self.config.ANALYSIS_PERIOD_DAYS,
            bar_size='1min'
        )
        
        if hist is None or hist.empty:
            return
        
        # Detect patterns
        patterns = self.pattern_detector.detect_patterns(hist, self.config)
        
        if not patterns:
            return
        
        # Get most recent pattern
        latest_pattern = patterns[-1]
        
        # Check if pattern confirms entry (price climbed ENTRY_THRESHOLD from last low)
        current_price = snapshot.get('last_price', 0)
        entry_low = latest_pattern.get('entry_low', 0)
        
        if entry_low == 0:
            return
        
        price_change_pct = ((current_price - entry_low) / entry_low) * 100
        
        if price_change_pct >= self.config.ENTRY_THRESHOLD:
            # Entry confirmed!
            
            # Apply filters if using enhanced strategy
            if self.use_filters and self.filter_engine:
                passed = self.filter_engine.apply_filters(
                    ticker=ticker,
                    pattern=latest_pattern,
                    market_data=hist,
                    current_price=current_price
                )
                
                if not passed:
                    logger.debug(f"{ticker}: Entry signal but failed filters")
                    return
            
            # Execute entry
            self._execute_entry(ticker, current_price, latest_pattern)
    
    def _execute_entry(self, ticker: str, entry_price: float, pattern: Dict):
        """
        Execute entry order.
        
        Args:
            ticker: Ticker symbol
            entry_price: Current price
            pattern: Pattern info
        """
        # Calculate position size
        position_size = self._calculate_position_size()
        shares = int(position_size / entry_price)
        
        if shares == 0:
            logger.warning(f"{ticker}: Position size too small")
            return
        
        logger.info(f"{ticker}: ENTRY SIGNAL - Price: ${entry_price:.2f}, Shares: {shares}")
        
        # Place market order
        order = self.ibkr.place_order(
            ticker=ticker,
            action='BUY',
            quantity=shares,
            order_type='MKT'
        )
        
        if not order:
            logger.error(f"{ticker}: Order failed")
            return
        
        # Track position
        self.active_positions[ticker] = {
            'ticker': ticker,
            'entry_price': entry_price,
            'shares': shares,
            'entry_time': datetime.now(),
            'pattern': pattern,
            'order_id': order.get('order_id'),
            'hit_target_1': False
        }
        
        self.trade_count += 1
        
        logger.info(f"{ticker}: Position opened - ${entry_price:.2f} x {shares} shares")
    
    def _manage_position(self, ticker: str):
        """
        Manage open position (check stop loss and profit targets).
        
        Args:
            ticker: Ticker symbol
        """
        position = self.active_positions[ticker]
        entry_price = position['entry_price']
        shares = position['shares']
        
        # Get current price
        snapshot = self.ibkr.get_market_snapshot(ticker)
        if not snapshot:
            return
        
        current_price = snapshot.get('last_price', 0)
        if current_price == 0:
            return
        
        # Calculate P&L percentage
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Check STOP LOSS
        if pnl_pct <= self.config.STOP_LOSS:
            logger.info(f"{ticker}: STOP LOSS HIT - P&L: {pnl_pct:.2f}%")
            self._execute_exit(ticker, current_price, 'STOP_LOSS')
            return
        
        # Check TARGET 1
        if not position['hit_target_1'] and pnl_pct >= self.config.TARGET_1:
            position['hit_target_1'] = True
            logger.info(f"{ticker}: TARGET 1 HIT - Waiting for TARGET 2 or reversion")
        
        # If hit TARGET 1, check for TARGET 2 or reversion
        if position['hit_target_1']:
            if pnl_pct >= self.config.TARGET_2:
                logger.info(f"{ticker}: TARGET 2 HIT - P&L: {pnl_pct:.2f}%")
                self._execute_exit(ticker, current_price, 'TARGET_2')
            elif pnl_pct < self.config.TARGET_1:
                logger.info(f"{ticker}: REVERTED TO TARGET 1 - P&L: {pnl_pct:.2f}%")
                self._execute_exit(ticker, current_price, 'TARGET_1')
    
    def _execute_exit(self, ticker: str, exit_price: float, reason: str):
        """
        Execute exit order.
        
        Args:
            ticker: Ticker symbol
            exit_price: Current price
            reason: Exit reason (STOP_LOSS, TARGET_1, TARGET_2)
        """
        position = self.active_positions[ticker]
        shares = position['shares']
        entry_price = position['entry_price']
        
        logger.info(f"{ticker}: EXITING - Reason: {reason}, Price: ${exit_price:.2f}")
        
        # Place market order to sell
        order = self.ibkr.place_order(
            ticker=ticker,
            action='SELL',
            quantity=shares,
            order_type='MKT'
        )
        
        if not order:
            logger.error(f"{ticker}: Exit order failed")
            return
        
        # Calculate P&L
        pnl = (exit_price - entry_price) * shares
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        
        self.daily_pnl += pnl
        
        logger.info(f"{ticker}: Position closed - P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")
        
        # Store fill in database
        self._store_fill(ticker, position, exit_price, pnl, reason)
        
        # Remove from active positions
        del self.active_positions[ticker]
        
        # Cooldown
        time.sleep(self.config.COOLDOWN_MINUTES * 60)
    
    def _store_fill(self, ticker: str, position: Dict, exit_price: float, pnl: float, exit_reason: str):
        """
        Store fill information in database.
        
        Args:
            ticker: Ticker symbol
            position: Position info
            exit_price: Exit price
            pnl: Realized P&L
            exit_reason: Exit reason
        """
        try:
            # Entry fill
            self.storage.store_fill({
                'date': position['entry_time'].strftime('%Y-%m-%d'),
                'timestamp': position['entry_time'],
                'ticker': ticker,
                'action': 'BUY',
                'quantity': position['shares'],
                'price': position['entry_price'],
                'realized_pnl': 0,
                'commission': 0,  # IBKR Lite has no commissions
                'ibkr_execution_id': f"{ticker}_{position['entry_time'].timestamp()}_BUY"
            })
            
            # Exit fill
            self.storage.store_fill({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now(),
                'ticker': ticker,
                'action': 'SELL',
                'quantity': position['shares'],
                'price': exit_price,
                'realized_pnl': pnl,
                'commission': 0,
                'ibkr_execution_id': f"{ticker}_{datetime.now().timestamp()}_SELL"
            })
            
            logger.debug(f"{ticker}: Fills stored in database")
            
        except Exception as e:
            logger.error(f"Error storing fills: {e}")
    
    def _calculate_position_size(self) -> float:
        """
        Calculate position size based on account balance and config.
        
        Returns:
            Dollar amount per position
        """
        deployed_capital = self.account_balance * self.config.DEPLOYMENT_RATIO
        position_size = deployed_capital / self.config.NUM_STOCKS
        return position_size
    
    def _update_account_balance(self):
        """Update account balance from IBKR."""
        balance_info = self.ibkr.get_account_balance()
        if balance_info and 'net_liquidation' in balance_info:
            self.account_balance = balance_info['net_liquidation']
    
    def _check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been hit.
        
        Returns:
            True if limit hit
        """
        if self.starting_balance == 0:
            return False
        
        loss_pct = ((self.account_balance - self.starting_balance) / self.starting_balance) * 100
        
        if loss_pct <= self.config.DAILY_LOSS_LIMIT:
            logger.warning(f"Daily loss limit hit: {loss_pct:.2f}%")
            return True
        
        return False
    
    def _is_trading_time(self) -> bool:
        """
        Check if current time is within trading hours.
        
        Returns:
            True if within trading hours
        """
        now = datetime.now().time()
        
        # Parse market times
        market_open = datetime.strptime(self.config.MARKET_OPEN, '%H:%M').time()
        entry_cutoff = datetime.strptime(self.config.ENTRY_CUTOFF, '%H:%M').time()
        market_close = datetime.strptime(self.config.MARKET_CLOSE, '%H:%M').time()
        
        # Before market open
        if now < market_open:
            return False
        
        # After entry cutoff (no new entries, but manage existing positions)
        if now > entry_cutoff:
            # Close all positions before market close
            if now >= market_close:
                return False
        
        return True
    
    def _shutdown(self):
        """Clean shutdown - close all positions."""
        logger.info("=" * 60)
        logger.info("SHUTTING DOWN")
        logger.info("=" * 60)
        
        # Close all open positions
        if self.active_positions:
            logger.info(f"Closing {len(self.active_positions)} open positions...")
            for ticker in list(self.active_positions.keys()):
                snapshot = self.ibkr.get_market_snapshot(ticker)
                if snapshot:
                    current_price = snapshot.get('last_price', 0)
                    if current_price > 0:
                        self._execute_exit(ticker, current_price, 'EOD_CLOSE')
        
        # Print summary
        logger.info("=" * 60)
        logger.info("TRADING SESSION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Starting Balance: ${self.starting_balance:,.2f}")
        logger.info(f"Ending Balance:   ${self.account_balance:,.2f}")
        logger.info(f"Daily P&L:        ${self.daily_pnl:,.2f}")
        
        if self.starting_balance > 0:
            daily_roi = (self.daily_pnl / self.starting_balance) * 100
            logger.info(f"Daily ROI:        {daily_roi:.2f}%")
        
        logger.info(f"Total Trades:     {self.trade_count}")
        logger.info("=" * 60)
        
        self.is_running = False


def main():
    """
    Example usage of Railyard engine.
    """
    # Initialize engine
    engine = RailyardEngine(
        strategy='default',
        use_filters=False
    )
    
    # Start trading
    engine.start_trading()


if __name__ == '__main__':
    main()
