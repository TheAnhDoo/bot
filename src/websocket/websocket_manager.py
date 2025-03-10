import websocket
import json
import zlib
import threading
import time
import logging
import io
import gzip
from typing import Optional, Callable
from src.config.trade_config import TradeConfig

class WebSocketManager:
    def __init__(self, on_price_update: Callable[[str, float], None]):
        self.config = TradeConfig()
        self.logger = logging.getLogger(__name__)
        self.on_price_update = on_price_update
        self.is_running = True
        self.ws = None
        self.last_ping_time = {'binance': 0, 'bingx': 0}
        self.last_pong_time = {'binance': 0, 'bingx': 0}
        self.connection_established = {'binance': False, 'bingx': False}
        # Add message queues for async processing
        self.message_queues = {
            'binance': [],
            'bingx': []
        }
        self.queue_lock = threading.Lock()
        self.price_lock = threading.Lock()  # Add price lock
        self.binance_price = None  # Add price storage
        self.bingx_price = None    # Add price storage
        self.start_message_processors()

    def start_message_processors(self):
        """Start message processor threads for each exchange"""
        for exchange in ['binance', 'bingx']:
            processor = threading.Thread(
                target=self.process_message_queue,
                args=(exchange,),
                daemon=True
            )
            processor.start()

    def process_message_queue(self, exchange: str):
        """Process messages in the queue for the given exchange"""
        while self.is_running:
            messages = []
            with self.queue_lock:
                if self.message_queues[exchange]:
                    messages = self.message_queues[exchange]
                    self.message_queues[exchange] = []
            
            for msg in messages:
                if exchange == 'binance':
                    self._process_binance_message(msg)
                else:
                    self._process_bingx_message(msg)
            
            time.sleep(0.001)  # Small sleep to prevent CPU overuse

    def _process_binance_message(self, message: str):
        """Process a single Binance message"""
        try:
            data = json.loads(message)
            if 'p' in data:  # Mark price data
                price = float(data['p'])
                timestamp = data.get('E', time.time() * 1000)
                latency = (time.time() * 1000) - timestamp
                
                # Process price update without lock for better performance
                self.binance_price = price
                self.on_price_update('binance', price)
                
                # Log after the price update for minimal latency
                self.logger.info(
                    f"[Binance] Mark Price Updated: {price:.8f} | "
                    f"Symbol: {data.get('s', 'N/A')} | "
                    f"Time: {timestamp} | "
                    f"Latency: {latency:.2f}ms"
                )
        except Exception as e:
            self.logger.error(f"[Binance] Message Error: {e}")

    def _process_bingx_message(self, message: bytes):
        """Process a single BingX message with optimized handling"""
        try:
            # Handle ping/pong first
            try:
                text_msg = message.decode('utf-8')
                if text_msg == "Ping":
                    self.logger.debug("[BingX] Received Ping, sending Pong")
                    return "Pong"
            except:
                pass

            # Decompress and process message
            data = self._decompress_bingx_message(message)
            
            # Log raw message for debugging
            self.logger.debug(f"BingX raw message: {data}")
            
            if isinstance(data, dict):
                # Handle mark price data
                if 'data' in data:
                    price_data = data['data']
                    if isinstance(price_data, dict) and 'p' in price_data:
                        price = float(price_data['p'])
                        timestamp = price_data.get('E', time.time() * 1000)
                        latency = (time.time() * 1000) - timestamp
                        
                        # Process price update without lock for better performance
                        self.bingx_price = price
                        self.on_price_update('bingx', price)
                        
                        # Log after the price update for minimal latency
                        self.logger.info(
                            f"[BingX] Mark Price Updated: {price:.8f} | "
                            f"Symbol: {price_data.get('s', 'N/A')} | "
                            f"Time: {timestamp} | "
                            f"Latency: {latency:.2f}ms"
                        )
        except Exception as e:
            self.logger.error(f"[BingX] Message Error: {str(e)}")
            if self.config.DEBUG_MODE:
                self.logger.debug(f"Message content (first 100 bytes): {message[:100]}...")

    def _decompress_bingx_message(self, message: bytes) -> dict:
        """Decompress BingX message with optimized handling"""
        try:
            # Use gzip decompression as specified in docs
            with gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb') as f:
                decompressed_data = f.read()
            return json.loads(decompressed_data.decode('utf-8'))
        except Exception as e:
            self.logger.error(f"Failed to decode BingX message: {str(e)}")
            self.logger.debug(f"Raw message: {message[:100]}...")  # Log first 100 bytes for debugging
            return {}

    def binance_on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Queue Binance WebSocket messages for processing"""
        with self.queue_lock:
            self.message_queues['binance'].append(message)

    def bingx_on_message(self, ws: websocket.WebSocketApp, message: bytes) -> None:
        """Queue BingX WebSocket messages for processing"""
        with self.queue_lock:
            self.message_queues['bingx'].append(message)

    def run_websocket(self, ws_url: str, on_message, name: str) -> None:
        """Run WebSocket connection with optimized settings"""
        def on_error(ws, error):
            self.logger.error(f"[{name}] WebSocket Error: {error}")
            self.connection_established[name.lower()] = False

        def on_close(ws, close_status_code, close_msg):
            self.logger.warning(f"[{name}] WebSocket Closed: {close_status_code} - {close_msg}")
            self.connection_established[name.lower()] = False

        def on_open(ws):
            self.logger.info(f"[{name}] WebSocket Connected")
            if name == "BingX":
                # Subscribe with correct format from documentation
                subscribe_msg = {
                    "id": str(int(time.time() * 1000)),
                    "reqType": "sub",
                    "dataType": f"{self.config.SYMBOL}@markPrice"  # Format: BTC-USDT@markPrice
                }
                ws.send(json.dumps(subscribe_msg))
                self.logger.info(f"Subscribed to: {json.dumps(subscribe_msg)}")
            self.connection_established[name.lower()] = True

        def on_message_wrapper(ws, message):
            if name == "BingX":
                response = on_message(ws, message)
                if response == "Pong":
                    ws.send(response)
            else:
                on_message(ws, message)

        while self.is_running:
            try:
                # Enable performance optimizations
                websocket.enableTrace(False)
                
                # Create WebSocket with optimized settings
                ws = websocket.WebSocketApp(
                    "wss://open-api-swap.bingx.com/swap-market" if name == "BingX" else ws_url,
                    on_message=on_message_wrapper,
                    on_error=on_error,
                    on_close=on_close,
                    on_open=on_open
                )
                
                # Optimized WebSocket settings
                ws.run_forever(
                    ping_interval=5,        # Frequent pings for stability
                    ping_timeout=3,         # Quick timeout for faster recovery
                    skip_utf8_validation=True,  # Skip validation for performance
                )
                
                if self.is_running:
                    self.logger.warning(f"[{name}] Reconnecting in 1 second...")
                    time.sleep(1)
            except Exception as e:
                self.logger.error(f"[{name}] Connection Error: {e}")
                time.sleep(1)

    def start(self):
        """Start WebSocket connections"""
        # Create WebSocket threads
        binance_thread = threading.Thread(
            target=self.run_websocket,
            args=(self.config.BINANCE_SOCKET, self.binance_on_message, "Binance")
        )
        bingx_thread = threading.Thread(
            target=self.run_websocket,
            args=(self.config.BINGX_SOCKET, self.bingx_on_message, "BingX")
        )

        # Start threads
        binance_thread.start()
        bingx_thread.start()

    def stop(self):
        """Stop WebSocket connections"""
        self.is_running = False 