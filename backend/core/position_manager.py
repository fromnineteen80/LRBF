"""
Position Manager - Component 6

Manages trading positions for LRBF:
- Submits orders to IBKR
- Tracks open positions
- Enforces 1-position-per-ticker limit
- Logs fills to database

Author: The Luggage Room Boys Fund
Date: October 2025
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open position."""
    ticker: str
    entry_time: datetime
    entry_price: float
    quantity: int
    pattern_type: str  # '3step' or 'vwap_breakout'
    preset: str  # Filter preset used
    ibkr_order_id: str
    ibkr_execution_id: Optional[str] = None
    current_price: Optional[float] = None
    unrealized_pnl: float = 0.0
    
    def update_current_price(self, price: float):
        """Update current price and recalculate unrealized P&L."""
        self.current_price = price
        self.unrealized_pnl = (price - self.entry_price) * self.quantity
    
    def get_pnl_pct(self) -> float:
        """Get P&L as percentage of entry price."""
        if self.current_price is None:
            return 0.0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100


class PositionManager:
    """
    Manages trading positions with institutional-grade controls.
    
    Key Features:
    - 1-position-per-ticker enforcement
    - Real-time position tracking
    - Integration with IBKR for order submission
    - Database logging of all fills
    - Position lifecycle management
    """
    
    def __init__(
        self,
        ibkr_connector,
        database,
        max_position_size: int = 100,
        default_quantity: int = 10
    ):
        """
        Initialize Position Manager.
        
        Args:
            ibkr_connector: IBKRConnector instance for order submission
            database: TradingDatabase instance for logging fills
            max_position_size: Maximum shares per position
            default_quantity: Default number of shares to trade
        """
        self.ibkr = ibkr_connector
        self.db = database
        self.max_position_size = max_position_size
        self.default_quantity = default_quantity
        
        # Active positions: {ticker: Position}
        self.positions: Dict[str, Position] = {}
        
        logger.info("PositionManager initialized")
    
    # ========================================================================
    # POSITION ENTRY
    # ========================================================================
    
    def can_enter_position(self, ticker: str) -> Tuple[bool, str]:
        """
        Check if we can enter a new position for this ticker.
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Tuple of (can_enter, reason)
        """
        # Check 1: Do we already have a position?
        if ticker in self.positions:
            return False, f"Position already exists for {ticker}"
        
        # Check 2: Is IBKR connected?
        if not self.ibkr.check_connection()['connected']:
            return False, "IBKR not connected"
        
        # All checks passed
        return True, "OK"
    
    def enter_position(
        self,
        ticker: str,
        entry_price: float,
        pattern_type: str,
        preset: str = 'default',
        quantity: Optional[int] = None
    ) -> Tuple[bool, str, Optional[Position]]:
        """
        Enter a new position by submitting a BUY order to IBKR.
        
        Args:
            ticker: Stock symbol
            entry_price: Current price (for reference)
            pattern_type: '3step' or 'vwap_breakout'
            preset: Filter preset name
            quantity: Number of shares (uses default if None)
        
        Returns:
            Tuple of (success, message, position)
        """
        # Validate we can enter
        can_enter, reason = self.can_enter_position(ticker)
        if not can_enter:
            logger.warning(f"Cannot enter {ticker}: {reason}")
            return False, reason, None
        
        # Determine quantity
        if quantity is None:
            quantity = self.default_quantity
        
        # Validate quantity
        if quantity <= 0 or quantity > self.max_position_size:
            return False, f"Invalid quantity: {quantity}", None
        
        # Submit BUY order to IBKR
        try:
            order_result = self.ibkr.place_order(
                ticker=ticker,
                action='BUY',
                quantity=quantity,
                order_type='MKT'
            )
            
            # Check if order was accepted
            if not order_result or 'orderId' not in order_result:
                return False, "Order submission failed", None
            
            # Create position record
            position = Position(
                ticker=ticker,
                entry_time=datetime.now(),
                entry_price=entry_price,
                quantity=quantity,
                pattern_type=pattern_type,
                preset=preset,
                ibkr_order_id=str(order_result['orderId']),
                current_price=entry_price
            )
            
            # Store in active positions
            self.positions[ticker] = position
            
            logger.info(
                f"✅ Entered position: {ticker} x{quantity} @ ${entry_price:.2f} "
                f"({pattern_type}, {preset})"
            )
            
            # Log to database (will be updated when fill arrives)
            self.db.log_event(
                event_type="INFO",
                severity="LOW",
                message=f"Position opened: {ticker} x{quantity} @ ${entry_price:.2f}",
                ticker=ticker
            )
            
            return True, "Position opened", position
            
        except Exception as e:
            logger.error(f"Error entering position {ticker}: {e}")
            return False, str(e), None
    
    # ========================================================================
    # POSITION EXIT
    # ========================================================================
    
    def exit_position(
        self,
        ticker: str,
        exit_price: float,
        reason: str = "Exit signal"
    ) -> Tuple[bool, str]:
        """
        Exit an existing position by submitting a SELL order to IBKR.
        
        Args:
            ticker: Stock symbol
            exit_price: Current price (for reference)
            reason: Reason for exit (e.g., "T2 target", "Stop loss")
        
        Returns:
            Tuple of (success, message)
        """
        # Check if position exists
        if ticker not in self.positions:
            return False, f"No position exists for {ticker}"
        
        position = self.positions[ticker]
        
        # Submit SELL order to IBKR
        try:
            order_result = self.ibkr.place_order(
                ticker=ticker,
                action='SELL',
                quantity=position.quantity,
                order_type='MKT'
            )
            
            # Check if order was accepted
            if not order_result or 'orderId' not in order_result:
                return False, "Order submission failed"
            
            # Calculate realized P&L
            realized_pnl = (exit_price - position.entry_price) * position.quantity
            pnl_pct = ((exit_price - position.entry_price) / position.entry_price) * 100
            
            logger.info(
                f"✅ Exited position: {ticker} x{position.quantity} @ ${exit_price:.2f} "
                f"| P&L: ${realized_pnl:.2f} ({pnl_pct:+.2f}%) | Reason: {reason}"
            )
            
            # Log to database
            self.db.log_event(
                event_type="INFO",
                severity="LOW",
                message=f"Position closed: {ticker} | P&L: ${realized_pnl:.2f} ({pnl_pct:+.2f}%) | {reason}",
                ticker=ticker
            )
            
            # Remove from active positions
            del self.positions[ticker]
            
            return True, f"Position closed: ${realized_pnl:.2f} ({pnl_pct:+.2f}%)"
            
        except Exception as e:
            logger.error(f"Error exiting position {ticker}: {e}")
            return False, str(e)
    
    # ========================================================================
    # FILL HANDLING
    # ========================================================================
    
    def process_fill(self, fill_data: Dict):
        """
        Process a fill notification from IBKR.
        
        This is called when IBKR confirms an order execution.
        Updates position records and logs to database.
        
        Args:
            fill_data: Fill information from IBKR
                Required keys: execution_id, ticker, action, quantity, 
                              price, timestamp, commission
        """
        ticker = fill_data['ticker']
        action = fill_data['action']
        
        # Update position if it exists
        if ticker in self.positions:
            position = self.positions[ticker]
            
            if action == 'BUY':
                # Update entry details with actual fill price
                position.ibkr_execution_id = fill_data['execution_id']
                position.entry_price = fill_data['price']
                position.current_price = fill_data['price']
                
                logger.info(f"Fill confirmed: BUY {ticker} x{fill_data['quantity']} @ ${fill_data['price']:.2f}")
            
            elif action == 'SELL':
                # Position should be removed after sell
                # This is just for logging the final fill
                realized_pnl = (fill_data['price'] - position.entry_price) * fill_data['quantity']
                logger.info(f"Fill confirmed: SELL {ticker} x{fill_data['quantity']} @ ${fill_data['price']:.2f} | P&L: ${realized_pnl:.2f}")
        
        # Log fill to database
        try:
            db_fill_data = {
                'ibkr_execution_id': fill_data['execution_id'],
                'timestamp': fill_data.get('timestamp', datetime.now().isoformat()),
                'ticker': ticker,
                'action': action,
                'quantity': fill_data['quantity'],
                'price': fill_data['price'],
                'commission': fill_data.get('commission', 0),
                'realized_pnl': fill_data.get('realized_pnl', 0)
            }
            
            self.db.insert_fill(db_fill_data)
            logger.debug(f"Fill logged to database: {fill_data['execution_id']}")
            
        except Exception as e:
            logger.error(f"Error logging fill to database: {e}")
    
    # ========================================================================
    # POSITION TRACKING
    # ========================================================================
    
    def get_position(self, ticker: str) -> Optional[Position]:
        """Get position for a ticker."""
        return self.positions.get(ticker)
    
    def get_all_positions(self) -> List[Position]:
        """Get all active positions."""
        return list(self.positions.values())
    
    def has_position(self, ticker: str) -> bool:
        """Check if we have an open position for ticker."""
        return ticker in self.positions
    
    def get_position_count(self) -> int:
        """Get number of active positions."""
        return len(self.positions)
    
    def update_position_price(self, ticker: str, current_price: float):
        """
        Update current price for a position.
        
        This should be called regularly with live price data.
        
        Args:
            ticker: Stock symbol
            current_price: Latest price
        """
        if ticker in self.positions:
            self.positions[ticker].update_current_price(current_price)
    
    def get_total_unrealized_pnl(self) -> float:
        """Get total unrealized P&L across all positions."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    def get_position_summary(self) -> Dict:
        """
        Get summary of all positions.
        
        Returns:
            Dictionary with position metrics
        """
        if not self.positions:
            return {
                'position_count': 0,
                'total_unrealized_pnl': 0.0,
                'positions': []
            }
        
        positions_list = []
        for pos in self.positions.values():
            positions_list.append({
                'ticker': pos.ticker,
                'quantity': pos.quantity,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'unrealized_pnl': pos.unrealized_pnl,
                'pnl_pct': pos.get_pnl_pct(),
                'pattern_type': pos.pattern_type,
                'preset': pos.preset,
                'entry_time': pos.entry_time.isoformat()
            })
        
        return {
            'position_count': len(self.positions),
            'total_unrealized_pnl': self.get_total_unrealized_pnl(),
            'positions': positions_list
        }
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def close_all_positions(self, reason: str = "End of day") -> Dict[str, Tuple[bool, str]]:
        """
        Close all open positions.
        
        Useful for end-of-day cleanup or emergency shutdowns.
        
        Args:
            reason: Reason for closing all positions
        
        Returns:
            Dictionary mapping ticker to (success, message)
        """
        results = {}
        tickers_to_close = list(self.positions.keys())
        
        logger.info(f"Closing {len(tickers_to_close)} positions: {reason}")
        
        for ticker in tickers_to_close:
            position = self.positions[ticker]
            # Use last known price, or get fresh quote if needed
            exit_price = position.current_price or position.entry_price
            
            success, message = self.exit_position(
                ticker=ticker,
                exit_price=exit_price,
                reason=reason
            )
            
            results[ticker] = (success, message)
        
        return results
    
    def get_positions_by_pattern(self, pattern_type: str) -> List[Position]:
        """Get all positions for a specific pattern type."""
        return [
            pos for pos in self.positions.values()
            if pos.pattern_type == pattern_type
        ]
    
    def get_positions_by_preset(self, preset: str) -> List[Position]:
        """Get all positions for a specific filter preset."""
        return [
            pos for pos in self.positions.values()
            if pos.preset == preset
        ]


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.path.append('/home/claude/LRBF')
    
    from backend.data.ibkr_connector import IBKRConnector
    from backend.models.database import TradingDatabase
    
    print("Testing PositionManager...")
    print("=" * 60)
    
    # Initialize dependencies (mock mode)
    try:
        ibkr = IBKRConnector(paper_trading=True)
        db = TradingDatabase("data/trading.db")
        
        # Create position manager
        pm = PositionManager(
            ibkr_connector=ibkr,
            database=db,
            default_quantity=10
        )
        
        print("✅ PositionManager initialized")
        
        # Test 1: Check if we can enter a position
        print("\n1. Testing position entry checks...")
        can_enter, reason = pm.can_enter_position("AAPL")
        print(f"   Can enter AAPL? {can_enter} - {reason}")
        
        # Test 2: Simulate position entry (if IBKR connected)
        if ibkr.check_connection()['connected']:
            print("\n2. Testing position entry...")
            success, message, position = pm.enter_position(
                ticker="AAPL",
                entry_price=150.25,
                pattern_type="3step",
                preset="default",
                quantity=10
            )
            print(f"   Entry result: {success} - {message}")
            
            if success:
                # Test 3: Check 1-position-per-ticker enforcement
                print("\n3. Testing 1-position-per-ticker enforcement...")
                can_enter2, reason2 = pm.can_enter_position("AAPL")
                print(f"   Can enter AAPL again? {can_enter2} - {reason2}")
                
                # Test 4: Update position price
                print("\n4. Testing position price update...")
                pm.update_position_price("AAPL", 151.50)
                pos = pm.get_position("AAPL")
                print(f"   AAPL P&L: ${pos.unrealized_pnl:.2f} ({pos.get_pnl_pct():+.2f}%)")
                
                # Test 5: Get position summary
                print("\n5. Testing position summary...")
                summary = pm.get_position_summary()
                print(f"   Active positions: {summary['position_count']}")
                print(f"   Total unrealized P&L: ${summary['total_unrealized_pnl']:.2f}")
                
                # Test 6: Exit position
                print("\n6. Testing position exit...")
                success, message = pm.exit_position("AAPL", 151.50, "Test exit")
                print(f"   Exit result: {success} - {message}")
        else:
            print("\n⚠️ IBKR not connected - skipping live tests")
            print("   (This is normal in test environments)")
        
        # Test 7: Summary after cleanup
        print("\n7. Final position count...")
        print(f"   Active positions: {pm.get_position_count()}")
        
        print("\n" + "=" * 60)
        print("✅ All PositionManager tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
