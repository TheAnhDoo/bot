import websocket
import json
import time
import zlib
import threading
import hmac
from hashlib import sha256
import requests
from datetime import datetime
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class TradeConfig:
    SYMBOL: str = "LTC-USDT"
    SYMBOL_LOWER: str = "ltcusdt"
    PRICE_DIFF_THRESHOLD: float = 0.1  # % difference to trigger trade
    POSITION_SIZE: float = 0.1  # Trade size
    TRADE_COOLDOWN: int = 5  # Cooldown in seconds
    MAX_RETRIES: int = 3
    RECONNECT_DELAY: int = 5
    WEBSOCKET_TIMEOUT: int = 30
    DEBUG_MODE: bool = True

class TradingBot:
    def __init__(self):
        # API Configuration
        self.API_URL = "https://open-api.bingx.com"
        self.API_KEY = "DcYvbavAYfA3oO44wuvDqJzj6FVoiL5lGhPqr8gkfVaJKz8r8x4EAsoiEsai0yaOPUuKrtqXhG1HeImjH8Xcw"
        self.SECRET_KEY = "YywDSqUaOYTEUoyZsdkyws1Kbxrd6TDU1WJRGjZ5YTtLe8twTy6wa8BEQnQsxEV1nxak3m5U3ER8O0kfQlmw"

    # WebSocket URLs
        self.BINANCE_SOCKET = f"wss://fstream.binance.com/ws/{TradeConfig.SYMBOL_LOWER}@markPrice"
        self.BINGX_SOCKET = "wss://open-api-ws.bingx.com/market"

        # State Variables
        self.binance_price: Optional[float] = None
        self.bingx_price: Optional[float] = None
        self.last_trade_time = 0
        self.price_lock = threading.Lock()
        self.is_running = True
        self.last_price_check = 0
        self.price_update_interval = 1  # seconds
        self.DEBUG_MODE = True

        # Setup logging
        self.setup_logging()
        
        # Verify API connection (but don't raise exception)
        if not self.verify_api_permissions():
            self.logger.warning("⚠️ API verification failed at startup")

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'trading_bot_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def binance_on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Handle Binance WebSocket messages"""
        try:
            data = json.loads(message)
            if 'p' in data:  # Mark price data
                price = float(data['p'])
                with self.price_lock:
                    self.binance_price = price
                    self.logger.info(f"[Binance] Mark Price Updated: {price:.8f}")
                self.check_prices()
        except Exception as e:
            self.logger.error(f"[Binance] Message Error: {e}")
            self.logger.error(f"[Binance] Message Content: {message}")

    def bingx_on_message(self, ws: websocket.WebSocketApp, message: bytes) -> None:
        """Handle BingX WebSocket messages"""
        try:
            # Handle both compressed and uncompressed messages
            try:
                decompressed_data = zlib.decompress(message, zlib.MAX_WBITS | 16)
                data = json.loads(decompressed_data.decode('utf-8'))
            except:
                data = json.loads(message.decode('utf-8'))

            # Debug log for message structure
            self.logger.debug(f"BingX message: {data}")

            if 'data' in data and isinstance(data['data'], dict) and 'p' in data['data']:
                price = float(data['data']['p'])
                with self.price_lock:
                    self.bingx_price = price
                    self.logger.info(f"[BingX] Price Updated: {price:.8f}")
                self.check_prices()
        except Exception as e:
            self.logger.error(f"[BingX] Message Error: {e}")
            self.logger.error(f"[BingX] Message Content: {message}")

# ... (previous imports and TradeConfig remain the same)

    def check_prices(self) -> None:
        """Check price differences and trading conditions"""
        current_time = time.time()
        if current_time - self.last_price_check < self.price_update_interval:
            return

        self.last_price_check = current_time

        with self.price_lock:
            if self.binance_price is None or self.bingx_price is None:
                return

            diff_percent = ((self.bingx_price - self.binance_price) / self.binance_price) * 100
            
            self.logger.info(
                f"[Price Compare] "
                f"Binance: {self.binance_price:.8f} | "
                f"BingX: {self.bingx_price:.8f} | "
                f"Diff: {diff_percent:.4f}% | "
                f"Time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}"
            )

            if (abs(diff_percent) >= TradeConfig.PRICE_DIFF_THRESHOLD and 
                current_time - self.last_trade_time >= TradeConfig.TRADE_COOLDOWN):
                
                # If Binance price is HIGHER than BingX (LONG opportunity)
                # Because Binance price indicates where BingX price will likely move
                if self.binance_price > self.bingx_price:
                    self.logger.info(
                        f"🔍 LONG Signal: Binance price ({self.binance_price:.8f}) is higher than "
                        f"BingX price ({self.bingx_price:.8f}) by {abs(diff_percent):.4f}%"
                    )
                    self.last_trade_time = current_time
                    self.create_position(self.bingx_price, "LONG")
                
                # If Binance price is LOWER than BingX (SHORT opportunity)
                elif self.binance_price < self.bingx_price:
                    self.logger.info(
                        f"🔍 SHORT Signal: Binance price ({self.binance_price:.8f}) is lower than "
                        f"BingX price ({self.bingx_price:.8f}) by {abs(diff_percent):.4f}%"
                    )
                    self.last_trade_time = current_time
                    self.create_position(self.bingx_price, "SHORT")
    
    def create_position(self, price: float, position_side: str) -> None:
        """Create a new position on BingX"""
        try:
            path = '/openApi/swap/v2/trade/order'
            method = "POST"
            
            params_map = {
                "symbol": TradeConfig.SYMBOL,
                "side": "BUY" if position_side == "LONG" else "SELL",
                "positionSide": position_side,
                "type": "MARKET",
                "quantity": str(TradeConfig.POSITION_SIZE),  # Convert to string
                "timestamp": str(int(time.time() * 1000))  # Add timestamp here
            }
            
            params_str = self.parse_params(params_map)
            
            # Send request using send_signed_request instead of send_request
            response = self.send_signed_request(method, path, params_map)
            
            if response and response.get('code') == 0:
                order_data = response.get('data', {}).get('order', {})
                self.logger.info(
                    f"✅ Order Successfully Created:\n"
                    f"   Order ID: {order_data.get('orderId')}\n"
                    f"   Side: {position_side}\n"
                    f"   Quantity: {order_data.get('quantity')}\n"
                    f"   Status: {order_data.get('status')}"
                )
            else:
                self.logger.error(f"❌ Order Failed: {response}")
                
        except Exception as e:
            self.logger.error(f"❌ Error creating position: {str(e)}")
    
    def verify_api_permissions(self) -> bool:
        """Verify API key permissions by checking account balance"""
        try:
            # Use the correct endpoint for checking account balance
            path = '/openApi/swap/v3/user/balance'
            method = "GET"
            
            # Create parameters map with timestamp
            params_map = {
                "timestamp": str(int(time.time() * 1000))
            }
            
            # Convert parameters to string
            params_str = self.parse_params(params_map)
            
            # Send request
            response_text = self.send_request(method, path, params_str)
            
            # Log the response
            self.logger.info(f"Account Balance Response: {response_text}")
            
            # Parse the response
            response = json.loads(response_text)
            
            # Check if the response is valid
            if response and response.get('code') == 0:
                self.logger.info("✅ API permissions verified")
                # Optionally log account balance for verification
                if 'data' in response:
                    self.logger.info(f"Account Balance: {response['data']}")
                return True
            else:
                self.logger.error(f"❌ API verification failed: {response}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error verifying API permissions: {str(e)}")
            return False

    def verify_position(self, symbol: str = None) -> bool:
        """Verify positions"""
        try:
            path = '/openApi/swap/v2/trade/positions'
            params = {
                "timestamp": int(time.time() * 1000)
            }
            if symbol:
                params["symbol"] = symbol
                
            response = self.send_signed_request("GET", path, params)
            
            if response and response.get('code') == 0:
                positions = response.get('data', [])
                self.logger.info(f"Current positions: {positions}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"❌ Error verifying positions: {str(e)}")
            return False

    def send_request(self, method: str, path: str, params_str: str, payload: dict = {}) -> str:
        """Send request to BingX API"""
        try:
            # Get signature
            signature = self.get_signature(params_str)
            
            # Create URL
            url = f"{self.API_URL}{path}?{params_str}&signature={signature}"
            
            # Set headers
            headers = {
                'X-BX-APIKEY': self.API_KEY
            }
            
            # Log request details
            self.logger.debug(f"Sending request to: {url}")
            self.logger.debug(f"Headers: {headers}")
            
            # Send request
            response = requests.request(method, url, headers=headers, data=payload)
            
            # Return response text
            return response.text
            
        except Exception as e:
            self.logger.error(f"Request Error: {e}")
            return ""

    def send_signed_request(self, method: str, path: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Send signed API request to BingX"""
        try:
            params_str = self.parse_params(params)
            signature = self.get_signature(params_str)
            url = f"{self.API_URL}{path}?{params_str}&signature={signature}"
            
            headers = {
                'X-BX-APIKEY': self.API_KEY
            }
            
            response = requests.request(method, url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"HTTP Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Request Error: {e}")
            return None

    def get_signature(self, params_str: str) -> str:
        """Generate signature for request"""
        try:
            return hmac.new(
                self.SECRET_KEY.encode("utf-8"),
                params_str.encode("utf-8"),
                digestmod=sha256
            ).hexdigest()
        except Exception as e:
            self.logger.error(f"Error generating signature: {e}")
            return ""

    def parse_params(self, params_map: Dict) -> str:
        """Parse parameters into string"""
        try:
            sorted_keys = sorted(params_map)
            params_str = "&".join([f"{key}={params_map[key]}" for key in sorted_keys])
            
            # Don't add timestamp here as it should be in params_map already
            return params_str
            
        except Exception as e:
            self.logger.error(f"Error parsing parameters: {e}")
            return ""
        
    def run_websocket(self, ws_url: str, on_message, name: str) -> None:
        """Run WebSocket connection with automatic reconnection"""
        def on_error(ws, error):
            self.logger.error(f"[{name}] WebSocket Error: {error}")

        def on_close(ws, close_status_code, close_msg):
            self.logger.warning(f"[{name}] WebSocket Closed: {close_status_code} - {close_msg}")

        def on_open(ws):
            self.logger.info(f"[{name}] WebSocket Connected")
            if name == "BingX":
                subscribe_msg = {
                    "id": "future_price_123",
                    "reqType": "sub",
                    "dataType": f"{TradeConfig.SYMBOL}@trade"
                }
                ws.send(json.dumps(subscribe_msg))

        while self.is_running:
            try:
                ws = websocket.WebSocketApp(
                    ws_url,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close,
                    on_open=on_open
                )
                ws.run_forever(
                    ping_interval=TradeConfig.WEBSOCKET_TIMEOUT,
                    ping_timeout=TradeConfig.WEBSOCKET_TIMEOUT//2
                )
                
                if self.is_running:
                    self.logger.warning(f"[{name}] Reconnecting in {TradeConfig.RECONNECT_DELAY} seconds...")
                    time.sleep(TradeConfig.RECONNECT_DELAY)
            except Exception as e:
                self.logger.error(f"[{name}] Connection Error: {e}")
                time.sleep(TradeConfig.RECONNECT_DELAY)

    def run(self) -> None:
        """Start the trading bot"""
        self.logger.info("🔹 Starting Trading Bot...")
        
        # Create WebSocket threads
        binance_thread = threading.Thread(
            target=self.run_websocket,
            args=(self.BINANCE_SOCKET, self.binance_on_message, "Binance")
        )
        bingx_thread = threading.Thread(
            target=self.run_websocket,
            args=(self.BINGX_SOCKET, self.bingx_on_message, "BingX")
        )

        # Start threads
        binance_thread.start()
        bingx_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("\n🔻 Stopping Trading Bot...")
            self.is_running = False
            time.sleep(1)
            self.logger.info("✅ Stopped.")

    def test_order(self) -> None:
        """Test order creation"""
        try:
            self.logger.info("Testing order creation...")
            
            params_map = {
                "symbol": TradeConfig.SYMBOL,
                "side": "BUY",
                "positionSide": "LONG",
                "type": "MARKET",
                "quantity": str(TradeConfig.POSITION_SIZE),
                "timestamp": str(int(time.time() * 1000))
            }
            
            path = '/openApi/swap/v2/trade/order/test'
            method = "POST"
            
            response = self.send_signed_request(method, path, params_map)
            self.logger.info(f"Test Order Response: {response}")
            
        except Exception as e:
            self.logger.error(f"Test Order Error: {e}")
            
if __name__ == "__main__":
    bot = TradingBot()
    
    # Test API order
    response = input("Test order creation? (y/n): ")
    if response.lower() == 'y':
        bot.test_order()
    
    # Ask to start bot
    response = input("Start trading bot? (y/n): ")
    if response.lower() == 'y':
        bot.run()
    else:
        print("Bot execution cancelled")