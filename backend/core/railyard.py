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
from backend.core.time_profile_analyzer import calculate_adaptive_timeout
from backend.core.news_monitor import NewsMonitor
from backend.models.database import get_db_connection

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
        

        # Time profiles for adaptive dead zones (loaded from morning report)
        self.stock_time_profiles = {}
        
        # News monitoring
        self.news_monitor = NewsMonitor()
        self.last_news_check = 0
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

            # Load time profiles for adaptive dead zones
            time_profiles_json = forecast.get('time_profiles_json', '{}')
            self.stock_time_profiles = json.loads(time_profiles_json) if time_profiles_json else {}
            logger.info(f"Loaded time profiles for {len(self.stock_time_profiles)} stocks")
            
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
            

            # Check news every 60 seconds
            if time.time() - self.last_news_check > 60:
                self._check_news()
                self.last_news_check = time.time()
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
        Manage open position with sophisticated tiered exit logic.
        
        Exit Logic:
        - If price reaches T2 (+1.75%) → Exit at T2
        - If price reaches T1, crosses +1.00%, hits +1.25% → Stay in for T2
        - If price reaches T1, crosses +1.00%, never hits +1.25% → Exit at +1.00%
        - If price reaches T1 but never crosses +1.00% → Exit at T1 (+0.75%)
        - Stop Loss: -0.5% from entry if immediate crash
        - Tiered dead zones based on profit level
        
        Args:
            ticker: Ticker symbol
        """
        position = self.active_positions[ticker]
        entry_price = position['entry_price']
        entry_time = position['entry_time']
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
        time_in_trade = time.time() - entry_time

        # Calculate adaptive timeout based on time-of-day performance
        adaptive_timeouts = {}
        if ticker in self.stock_time_profiles:
            # Determine current milestone
            milestone = None
            if position.get('hit_momentum', False):
                milestone = 'momentum'
            elif position.get('hit_cross', False):
                milestone = 'cross'
            elif position.get('hit_target_1', False):
                milestone = 'target1'
            else:
                milestone = 'base'
            
            # Calculate adaptive timeout
            pattern_strength = position.get('pattern_strength', 1.0)
            adaptive_timeout = calculate_adaptive_timeout(
                stock_profile=self.stock_time_profiles[ticker],
                milestone=milestone,
                current_time=datetime.now(),
                pattern_strength=pattern_strength
            )
            
            # Store for use in dead zone checks
            adaptive_timeouts['momentum'] = adaptive_timeout
            adaptive_timeouts['cross'] = adaptive_timeout
            adaptive_timeouts['base'] = adaptive_timeout
        else:
            # Fallback to config defaults
            adaptive_timeouts['momentum'] = self.config.DEAD_ZONE_TIMEOUT_MOMENTUM
            adaptive_timeouts['cross'] = adaptive_timeouts['cross']
            adaptive_timeouts['base'] = adaptive_timeouts['base']
        
        # Update max P&L reached
        if 'max_pnl_pct' not in position:
            position['max_pnl_pct'] = pnl_pct
        else:
            position['max_pnl_pct'] = max(position['max_pnl_pct'], pnl_pct)
        
        # Track price history for dead zone detection
        if 'price_history' not in position:
            position['price_history'] = []
        position['price_history'].append(pnl_pct)
        if len(position['price_history']) > 60:  # Keep last 60 ticks
            position['price_history'] = position['price_history'][-60:]
        
        # Initialize milestone flags
        if 'hit_target_1' not in position:
            position['hit_target_1'] = False
        if 'hit_cross' not in position:
            position['hit_cross'] = False
        if 'hit_momentum' not in position:
            position['hit_momentum'] = False
        
        # === CASE 1: Hit T2 → Exit immediately ===
        if pnl_pct >= self.config.TARGET_2:
            logger.info(f"{ticker}: TARGET 2 HIT - P&L: {pnl_pct:.2f}%")
            self._execute_exit(ticker, current_price, 'TARGET_2')
            return
        
        # === CASE 2: Stop Loss (immediate crash) ===
        if pnl_pct <= self.config.STOP_LOSS:
            logger.info(f"{ticker}: STOP LOSS HIT - P&L: {pnl_pct:.2f}%")
            self._execute_exit(ticker, current_price, 'STOP_LOSS')
            return
        
        # === Update milestone flags ===
        if pnl_pct >= self.config.TARGET_1:
            position['hit_target_1'] = True
        if pnl_pct >= self.config.CROSS_THRESHOLD:
            position['hit_cross'] = True
        if pnl_pct >= self.config.MOMENTUM_CONFIRMATION:
            position['hit_momentum'] = True
        
        # === CASE 3: Momentum confirmed, going for T2 ===
        if position['hit_momentum']:
            # Check dead zone (6 minutes after momentum)
            if self._check_dead_zone(position, time_in_trade, adaptive_timeouts['momentum']):
                # Exit at Cross floor or higher
                exit_pct = max(pnl_pct, self.config.CROSS_THRESHOLD)
                logger.info(f"{ticker}: DEAD ZONE MOMENTUM - Exiting at {exit_pct:.2f}%")
                self._execute_exit(ticker, current_price, 'DEAD_ZONE_MOMENTUM')
                return
            # Otherwise, hold for T2
            return
        
        # === CASE 4: Hit T1, crossed 1.00%, waiting for momentum ===
        if position['hit_cross']:
            # Check if we should exit at Cross (never hit 1.25%)
            if pnl_pct < self.config.CROSS_THRESHOLD:
                logger.info(f"{ticker}: REVERTED TO CROSS - Exiting at {self.config.CROSS_THRESHOLD:.2f}%")
                self._execute_exit(ticker, current_price, 'CROSS_THRESHOLD')
                return
            
            # Check dead zone (4 minutes)
            if self._check_dead_zone(position, time_in_trade, adaptive_timeouts['cross']):
                logger.info(f"{ticker}: DEAD ZONE AT CROSS - Exiting at {self.config.CROSS_THRESHOLD:.2f}%")
                self._execute_exit(ticker, current_price, 'DEAD_ZONE_CROSS')
                return
            return
        
        # === CASE 5: Hit T1, waiting for Cross ===
        if position['hit_target_1']:
            # Check if we should exit at T1 (never crossed 1.00%)
            if pnl_pct < self.config.TARGET_1:
                logger.info(f"{ticker}: REVERTED TO T1 - Exiting at {self.config.TARGET_1:.2f}%")
                self._execute_exit(ticker, current_price, 'TARGET_1')
                return
            
            # Check dead zone (4 minutes)
            if self._check_dead_zone(position, time_in_trade, self.config.DEAD_ZONE_TIMEOUT_AT_T1):
                logger.info(f"{ticker}: DEAD ZONE AT T1 - Exiting at {self.config.TARGET_1:.2f}%")
                self._execute_exit(ticker, current_price, 'DEAD_ZONE_T1')
                return
            return
        
        # === CASE 6: Below T1, check for weak pattern ===
        if time_in_trade > self.config.DEAD_ZONE_TIMEOUT_BELOW_T1:
            if self._check_dead_zone(position, time_in_trade, self.config.DEAD_ZONE_TIMEOUT_BELOW_T1):
                # Exit at break-even or small profit
                exit_pct = max(pnl_pct, 0.0)
                logger.info(f"{ticker}: DEAD ZONE BELOW T1 - Exiting at {exit_pct:.2f}%")
                self._execute_exit(ticker, current_price, 'DEAD_ZONE_FAILED')
                return
    
    def _check_dead_zone(self, position: Dict, time_in_trade: float, timeout: float) -> bool:
        """
        Check if position is stuck in dead zone (±0.6% range).
        
        Args:
            position: Position dict with price_history
            time_in_trade: Time since entry (seconds)
            timeout: Timeout threshold (seconds)
        
        Returns:
            True if dead zone detected
        """
        if time_in_trade < timeout:
            return False
        
        # Check if stuck in narrow range
        price_history = position.get('price_history', [])
        if len(price_history) < 30:
            return False
        
        recent_prices = price_history[-30:]
        price_range = max(recent_prices) - min(recent_prices)
        
        # Dead zone = stuck in ±0.6% range
        return price_range < self.config.DEAD_ZONE_RANGE

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
    
    
    def _check_news(self):
        """
        Check for news events on active positions every 60 seconds.
        Take action based on risk level.
        """
        if not self.active_positions:
            return
        
        # Get list of tickers with open positions
        active_tickers = list(self.active_positions.keys())
        
        # Monitor for news
        news_actions = self.news_monitor.monitor_tickers(active_tickers)
        
        # Handle recommended actions
        for ticker, action in news_actions.items():
            if action == 'EXIT_IMMEDIATELY':
                logger.warning(f"{ticker}: BREAKING NEWS - Emergency exit triggered")
                snapshot = self.ibkr.get_market_snapshot(ticker)
                if snapshot:
                    current_price = snapshot.get('last_price', 0)
                    if current_price > 0:
                        self._execute_exit(ticker, current_price, 'NEWS_BREAK')
            
            elif action == 'TIGHTEN_STOPS':
                logger.warning(f"{ticker}: ELEVATED NEWS RISK - Tightening stops")
                position = self.active_positions.get(ticker)
                if position:
                    # Reduce stop loss to -0.25% (tighter than normal -0.5%)
                    position['tightened_stop'] = True
                    position['stop_loss_pct'] = -0.25
            
            elif action == 'HALT_TRADING':
                logger.warning(f"{ticker}: EXTREME NEWS RISK - Halting new entries")
                # Remove from selected tickers to prevent new entries
                if ticker in self.selected_tickers:
                    self.selected_tickers.remove(ticker)
    
    def _emergency_exit(self, ticker: str, reason: str):
        """Emergency exit for news events."""
        if ticker not in self.active_positions:
            return
        
        snapshot = self.ibkr.get_market_snapshot(ticker)
        if snapshot:
            current_price = snapshot.get('last_price', 0)
            if current_price > 0:
                self._execute_exit(ticker, current_price, reason)
                logger.info(f"{ticker}: Emergency exit completed - {reason}")
    
    def _tighten_stops(self, ticker: str, multiplier: float = 0.5):
        """Tighten stop loss for elevated risk."""
        if ticker not in self.active_positions:
            return
        
        position = self.active_positions[ticker]
        original_stop = self.config.STOP_LOSS
        new_stop = original_stop * multiplier
        position['stop_loss_pct'] = new_stop
        logger.info(f"{ticker}: Stop loss tightened from {original_stop}% to {new_stop}%")
    
    def _halt_position(self, ticker: str):
        """Halt trading for a specific ticker."""
        # Remove from selected tickers
        if ticker in self.selected_tickers:
            self.selected_tickers.remove(ticker)
            logger.info(f"{ticker}: Removed from trading list due to news risk")
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

