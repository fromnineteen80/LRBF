"""
IBKR WebSocket Streaming - Microsecond Latency

Provides real-time tick-by-tick market data via IBKR WebSocket API.
Replaces 1-minute polling with sub-100ms streaming for intraminute trading.

Key Features:
- WebSocket connection to IBKR Client Portal Gateway
- Tick-by-tick price updates (last, bid, ask, VWAP)
- Microsecond timestamp precision
- Automatic reconnection on disconnect
- Buffer management for high-frequency data

Author: The Luggage Room Boys Fund
Date: October 2025
"""

import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Callable, Optional
import websocket
from collections import deque


class IBKRWebSocket:
    """
    WebSocket client for IBKR real-time market data.
    
    Maintains persistent connection and streams tick data for subscribed symbols.
    """
    
    def __init__(
        self,
        gateway_url: str = "https://localhost:8000",
        buffer_size: int = 1000,
        auto_reconnect: bool = True
    ):
        """
        Initialize IBKR WebSocket client.
        
        Args:
            gateway_url: IBKR Client Portal Gateway URL
            buffer_size: Maximum ticks to buffer per symbol
            auto_reconnect: Automatically reconnect on disconnect
        """
        self.gateway_url = gateway_url.replace('https://', 'wss://')
        self.buffer_size = buffer_size
        self.auto_reconnect = auto_reconnect
        
        # Connection state
        self.ws = None
        self.connected = False
        self.session_id = None
        
        # Data buffers (symbol -> deque of ticks)
        self.tick_buffers: Dict[str, deque] = {}
        self.latest_ticks: Dict[str, Dict] = {}
        
        # Subscriptions
        self.subscribed_symbols: List[str] = []
        self.conid_map: Dict[str, int] = {}  # symbol -> contract ID
        
        # Callbacks
        self.on_tick_callbacks: List[Callable] = []
        self.on_error_callbacks: List[Callable] = []
        
        # Threading
        self.receive_thread = None
        self.running = False
    
    def connect(self, session_id: str = None) -> bool:
        """
        Establish WebSocket connection to IBKR.
        
        Args:
            session_id: Optional session ID from REST API authentication
        
        Returns:
            True if connection successful
        """
        try:
            self.session_id = session_id
            
            # Build WebSocket URL
            ws_url = f"{self.gateway_url}/v1/api/ws"
            
            # Create WebSocket connection
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Start connection in background thread
            self.receive_thread = threading.Thread(
                target=self.ws.run_forever,
                kwargs={'sslopt': {'cert_reqs': 0}}  # Accept self-signed certs
            )
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                print(f"✅ WebSocket connected to {ws_url}")
                return True
            else:
                print(f"❌ WebSocket connection timeout")
                return False
                
        except Exception as e:
            print(f"❌ WebSocket connection error: {e}")
            return False
    
    def subscribe(self, symbols: List[str], conid_map: Dict[str, int] = None):
        """
        Subscribe to real-time data for symbols.
        
        Args:
            symbols: List of ticker symbols to subscribe
            conid_map: Mapping of symbol -> IBKR contract ID (optional)
        """
        if not self.connected:
            print("❌ WebSocket not connected. Call connect() first.")
            return
        
        self.subscribed_symbols.extend(symbols)
        
        if conid_map:
            self.conid_map.update(conid_map)
        
        # Initialize buffers
        for symbol in symbols:
            if symbol not in self.tick_buffers:
                self.tick_buffers[symbol] = deque(maxlen=self.buffer_size)
                self.latest_ticks[symbol] = {}
        
        # Send subscription request for each symbol
        for symbol in symbols:
            conid = self.conid_map.get(symbol)
            if not conid:
                print(f"⚠️  No contract ID for {symbol}. Skipping subscription.")
                continue
            
            subscription_msg = {
                "type": "subscribe",
                "channel": f"md+{conid}",
                "fields": ["31", "84", "86", "7633", "87"]  # Last, Bid, Ask, VWAP, Volume
            }
            
            self.ws.send(json.dumps(subscription_msg))
            print(f"✅ Subscribed to {symbol} (conid: {conid})")
    
    def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from symbols."""
        for symbol in symbols:
            conid = self.conid_map.get(symbol)
            if conid:
                unsubscribe_msg = {
                    "type": "unsubscribe",
                    "channel": f"md+{conid}"
                }
                self.ws.send(json.dumps(unsubscribe_msg))
                
            if symbol in self.subscribed_symbols:
                self.subscribed_symbols.remove(symbol)
    
    def get_latest_tick(self, symbol: str) -> Optional[Dict]:
        """
        Get most recent tick for a symbol.
        
        Returns:
            Dictionary with tick data:
            {
                'symbol': str,
                'timestamp': datetime,
                'last_price': float,
                'bid': float,
                'ask': float,
                'vwap': float,
                'volume': int,
                'latency_ms': float
            }
        """
        return self.latest_ticks.get(symbol)
    
    def get_tick_buffer(self, symbol: str, limit: int = None) -> List[Dict]:
        """
        Get buffered ticks for a symbol.
        
        Args:
            symbol: Ticker symbol
            limit: Maximum number of recent ticks to return
        
        Returns:
            List of tick dictionaries (newest first)
        """
        if symbol not in self.tick_buffers:
            return []
        
        buffer = list(self.tick_buffers[symbol])
        buffer.reverse()  # Newest first
        
        if limit:
            return buffer[:limit]
        return buffer
    
    def clear_buffer(self, symbol: str):
        """Clear tick buffer for a symbol."""
        if symbol in self.tick_buffers:
            self.tick_buffers[symbol].clear()
    
    def register_tick_callback(self, callback: Callable):
        """
        Register callback function to be called on each tick.
        
        Callback signature: callback(symbol: str, tick: Dict)
        """
        self.on_tick_callbacks.append(callback)
    
    def disconnect(self):
        """Close WebSocket connection."""
        self.running = False
        self.connected = False
        
        if self.ws:
            self.ws.close()
        
        print("🔌 WebSocket disconnected")
    
    # ========================================================================
    # PRIVATE METHODS (WebSocket Event Handlers)
    # ========================================================================
    
    def _on_open(self, ws):
        """Called when WebSocket connection opens."""
        self.connected = True
        self.running = True
        print("🔗 WebSocket connection opened")
    
    def _on_message(self, ws, message):
        """Called when WebSocket receives a message."""
        try:
            data = json.loads(message)
            
            # Parse market data update
            if 'topic' in data and data['topic'].startswith('md+'):
                self._process_market_data(data)
            
        except Exception as e:
            print(f"❌ Error processing WebSocket message: {e}")
    
    def _process_market_data(self, data: Dict):
        """Process market data tick from WebSocket."""
        try:
            # Extract contract ID from topic
            conid_str = data['topic'].replace('md+', '')
            conid = int(conid_str)
            
            # Find symbol from conid
            symbol = None
            for sym, cid in self.conid_map.items():
                if cid == conid:
                    symbol = sym
                    break
            
            if not symbol:
                return
            
            # Parse tick data
            tick = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'server_timestamp': data.get('timestamp'),
                'last_price': data.get('31'),  # Last price
                'bid': data.get('84'),  # Bid
                'ask': data.get('86'),  # Ask
                'vwap': data.get('7633'),  # VWAP
                'volume': data.get('87'),  # Volume
                'latency_ms': self._calculate_latency(data.get('timestamp'))
            }
            
            # Store in buffer
            self.tick_buffers[symbol].append(tick)
            self.latest_ticks[symbol] = tick
            
            # Call registered callbacks
            for callback in self.on_tick_callbacks:
                try:
                    callback(symbol, tick)
                except Exception as e:
                    print(f"❌ Error in tick callback: {e}")
                    
        except Exception as e:
            print(f"❌ Error processing market data: {e}")
    
    def _calculate_latency(self, server_timestamp: int) -> float:
        """Calculate latency between server and local time."""
        if not server_timestamp:
            return 0.0
        
        local_time = time.time() * 1000  # Convert to milliseconds
        return local_time - server_timestamp
    
    def _on_error(self, ws, error):
        """Called when WebSocket encounters an error."""
        print(f"❌ WebSocket error: {error}")
        
        for callback in self.on_error_callbacks:
            try:
                callback(error)
            except:
                pass
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Called when WebSocket connection closes."""
        self.connected = False
        print(f"🔌 WebSocket closed: {close_status_code} - {close_msg}")
        
        # Auto-reconnect if enabled
        if self.auto_reconnect and self.running:
            print("🔄 Attempting to reconnect...")
            time.sleep(5)
            self.connect(self.session_id)


# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

def create_websocket_client(
    gateway_url: str = "https://localhost:8000",
    symbols: List[str] = None,
    conid_map: Dict[str, int] = None
) -> IBKRWebSocket:
    """
    Create and connect IBKR WebSocket client.
    
    Args:
        gateway_url: IBKR Gateway URL
        symbols: Symbols to subscribe (optional)
        conid_map: Symbol -> contract ID mapping (optional)
    
    Returns:
        Connected IBKRWebSocket instance
    """
    client = IBKRWebSocket(gateway_url=gateway_url)
    
    if client.connect():
        if symbols:
            client.subscribe(symbols, conid_map)
        return client
    else:
        raise ConnectionError("Failed to connect WebSocket to IBKR")


def get_realtime_price(client: IBKRWebSocket, symbol: str) -> Optional[float]:
    """
    Get current price for a symbol from WebSocket stream.
    
    Args:
        client: Connected WebSocket client
        symbol: Ticker symbol
    
    Returns:
        Current price or None if unavailable
    """
    tick = client.get_latest_tick(symbol)
    if tick:
        return tick.get('last_price')
    return None
