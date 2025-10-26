"""
Railyard.py - Proprietary Trading Execution Engine

Replaces Capitalise.ai with our own execution logic.
Monitors VWAP recovery patterns and executes trades via IBKR API.

Architecture:
- Real-time pattern monitoring (100ms updates)
- Direct IBKR integration (no third-party fees)
- Supports both default and enhanced strategies
- WebSocket streaming ready (future)

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import logging

from backend.data.ibkr_connector import IBKRConnector
from backend.core.pattern_detector import PatternDetector
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
        strategy: str = 'default'
    ):
        """
        Initialize Railyard engine.
        
        Args:
            ibkr_connector: IBKR connection (creates new if None)
            config: Trading configuration (uses default if None)
            strategy: 'default' or 'enhanced'
        """
        self.config = config or TradingConfig()
        self.strategy = strategy
        
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
        
        # Trading state
        self.active_positions = {}  # ticker -> position_info
        self.pending_orders = {}    # ticker -> order_info
        self.daily_pnl = 0.0
        self.trade_count = 0
        self.is_running = False
        
        # Selected tickers (loaded from morning report)
        self.selected_tickers = []
        
        logger.info(f"Railyard Engine initialized (strategy: {strategy})")
    
    def load_morning_forecast(self, date: str = None) -> bool:
        """
        Load selected tickers from morning forecast.
        
        Args:
            date: Date string (YYYY-MM-DD), uses today if None
            
        Returns:
            True if forecast loaded successfully
        """
        # TODO: Load from database
        # For now, use placeholder
        from backend.data.stock_universe import get_curated_universe
        universe = get_curated_universe()
        self.selected_tickers = universe[:self.config.NUM_STOCKS]
        
        logger.info(f"Loaded {len(self.selected_tickers)} tickers for trading")
        return True
    
    def start(self):
        """Start the trading engine."""
        logger.info("=" * 60)
        logger.info("STARTING RAILYARD EXECUTION ENGINE")
        logger.info("=" * 60)
        
        # Load morning forecast
        if not self.load_morning_forecast():
            logger.error("Failed to load morning forecast. Aborting.")
            return
        
        # Subscribe to market data
        logger.info(f"Subscribing to market data for {len(self.selected_tickers)} tickers...")
        self.ibkr.subscribe_market_data(self.selected_tickers)
        
        self.is_running = True
        logger.info("Engine started. Monitoring for patterns...")
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            logger.info("Received stop signal")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the trading engine and close all positions."""
        logger.info("Stopping Railyard Engine...")
        
        self.is_running = False
        
        # Close all open positions
        self._close_all_positions()
        
        # Disconnect from IBKR
        self.ibkr.disconnect()
        
        logger.info("Engine stopped")
    
    def _main_loop(self):
        """Main execution loop."""
        update_interval = IBKRConfig.REALTIME_UPDATE_INTERVAL_MS / 1000.0
        
        while self.is_running:
            loop_start = time.time()
            
            try:
                # Check market hours
                if not self._is_market_open():
                    time.sleep(60)  # Check every minute
                    continue
                
                # Check daily loss limit
                if self._check_daily_loss_limit():
                    logger.warning("Daily loss limit reached. Stopping engine.")
                    self.stop()
                    break
                
                # Get market snapshots
                snapshots = self.ibkr.get_multiple_snapshots(self.selected_tickers)
                
                # Process each ticker
                for ticker, snapshot in snapshots.items():
                    self._process_ticker(ticker, snapshot)
                
                # Sleep to maintain update interval
                elapsed = time.time() - loop_start
                sleep_time = max(0, update_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(1)
    
    def _process_ticker(self, ticker: str, snapshot: Dict):
        """
        Process a single ticker for pattern detection and execution.
        
        Args:
            ticker: Ticker symbol
            snapshot: Current market snapshot
        """
        # Skip if already have position
        if ticker in self.active_positions:
            self._manage_position(ticker, snapshot)
            return
        
        # Skip if pending order
        if ticker in self.pending_orders:
            return
        
        # Check for entry pattern
        if self._check_entry_pattern(ticker, snapshot):
            self._execute_entry(ticker, snapshot)
    
    def _check_entry_pattern(self, ticker: str, snapshot: Dict) -> bool:
        """
        Check if current snapshot matches VWAP recovery entry pattern.
        
        Args:
            ticker: Ticker symbol
            snapshot: Current market snapshot
            
        Returns:
            True if entry pattern detected
        """
        # TODO: Implement actual pattern detection logic
        # For now, placeholder
        return False
    
    def _execute_entry(self, ticker: str, snapshot: Dict):
        """
        Execute entry order for ticker.
        
        Args:
            ticker: Ticker symbol
            snapshot: Current market snapshot
        """
        # Calculate position size
        account_balance = self.ibkr.get_account_balance()['total_balance']
        deployed_capital = account_balance * self.config.DEPLOYMENT_RATIO
        position_size = deployed_capital / self.config.NUM_STOCKS
        
        # Calculate quantity
        quantity = int(position_size / snapshot['last_price'])
        
        if quantity == 0:
            logger.warning(f"{ticker}: Position size too small")
            return
        
        # Place order
        logger.info(f"{ticker}: ENTRY signal detected. Buying {quantity} shares @ ${snapshot['last_price']:.2f}")
        
        order = self.ibkr.place_order(
            ticker=ticker,
            action='BUY',
            quantity=quantity,
            order_type='MKT'
        )
        
        if order:
            self.pending_orders[ticker] = {
                'order_id': order['order_id'],
                'entry_price': snapshot['last_price'],
                'quantity': quantity,
                'timestamp': datetime.now()
            }
    
    def _manage_position(self, ticker: str, snapshot: Dict):
        """
        Manage existing position (check exit conditions).
        
        Args:
            ticker: Ticker symbol
            snapshot: Current market snapshot
        """
        position = self.active_positions[ticker]
        entry_price = position['entry_price']
        current_price = snapshot['last_price']
        
        # Calculate P&L
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Check stop loss
        if pnl_pct <= self.config.STOP_LOSS:
            logger.info(f"{ticker}: STOP LOSS triggered ({pnl_pct:.2f}%)")
            self._execute_exit(ticker, 'STOP_LOSS')
            return
        
        # Check profit targets
        if pnl_pct >= self.config.TARGET_2:
            logger.info(f"{ticker}: TARGET 2 hit ({pnl_pct:.2f}%)")
            self._execute_exit(ticker, 'TARGET_2')
            return
        
        if pnl_pct >= self.config.TARGET_1:
            # Reached Target 1, wait for Target 2 or return to Target 1
            if not position.get('target_1_reached'):
                logger.info(f"{ticker}: TARGET 1 reached ({pnl_pct:.2f}%), waiting for TARGET 2")
                position['target_1_reached'] = True
            elif pnl_pct < self.config.TARGET_1 * 0.9:  # Dropped below Target 1
                logger.info(f"{ticker}: Returned to TARGET 1, exiting ({pnl_pct:.2f}%)")
                self._execute_exit(ticker, 'TARGET_1_RETURN')
    
    def _execute_exit(self, ticker: str, reason: str):
        """
        Execute exit order for ticker.
        
        Args:
            ticker: Ticker symbol
            reason: Exit reason
        """
        position = self.active_positions[ticker]
        
        logger.info(f"{ticker}: EXITING position - {reason}")
        
        # Place sell order
        order = self.ibkr.place_order(
            ticker=ticker,
            action='SELL',
            quantity=position['quantity'],
            order_type='MKT'
        )
        
        if order:
            # Remove from active positions
            del self.active_positions[ticker]
            self.trade_count += 1
    
    def _close_all_positions(self):
        """Close all open positions."""
        logger.info(f"Closing {len(self.active_positions)} open positions...")
        
        for ticker in list(self.active_positions.keys()):
            self._execute_exit(ticker, 'EOD_CLOSE')
    
    def _is_market_open(self) -> bool:
        """Check if market is currently open."""
        now = datetime.now()
        
        # TODO: Use market calendar
        # For now, simple time check
        if now.weekday() >= 5:  # Weekend
            return False
        
        market_open = now.replace(hour=9, minute=31, second=0)
        market_close = now.replace(hour=16, minute=0, second=0)
        
        return market_open <= now <= market_close
    
    def _check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit has been reached."""
        account_balance = self.ibkr.get_account_balance()['total_balance']
        daily_loss_pct = (self.daily_pnl / account_balance) * 100
        
        return daily_loss_pct <= self.config.DAILY_LOSS_LIMIT
    
    def get_status(self) -> Dict:
        """Get current engine status."""
        return {
            'is_running': self.is_running,
            'strategy': self.strategy,
            'active_positions': len(self.active_positions),
            'trade_count': self.trade_count,
            'daily_pnl': self.daily_pnl,
            'selected_tickers': self.selected_tickers
        }


if __name__ == '__main__':
    # Test run
    print("=" * 60)
    print("RAILYARD ENGINE - TEST RUN")
    print("=" * 60)
    
    try:
        engine = RailyardEngine(strategy='default')
        print(f"Status: {engine.get_status()}")
        
        # Note: Don't start() in test mode - requires market hours
        print("\n✅ Engine initialized successfully")
        print("To run live: engine.start()")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
