import time
import threading
import logging
from typing import Optional
from src.config.trade_config import TradeConfig
from src.api.bingx_client import BingXClient

class TradingLogic:
    def __init__(self):
        self.config = TradeConfig()
        self.logger = logging.getLogger(__name__)
        self.api_client = BingXClient()
        
        # State Variables
        self.binance_price: Optional[float] = None
        self.bingx_price: Optional[float] = None
        self.last_trade_time = 0
        self.position_open = False
        self.current_order_id = None
        self.current_order_side = None
        self.current_order_price = None
        self.auto_create_order = False
        self.is_running = True

    def update_price(self, exchange: str, price: float) -> None:
        """Update price for a specific exchange"""
        if exchange == 'binance':
            self.binance_price = price
        elif exchange == 'bingx':
            self.bingx_price = price
        self.check_prices()

    def check_prices(self) -> None:
        """Check price differences and trading conditions"""
        current_time = time.time()
        if current_time - self.last_trade_time < self.config.TRADE_COOLDOWN:
            return

        if self.position_open:  # Skip checking if a position is open
            self.logger.info("Position is open, skipping price check.")
            return

        if self.binance_price is None or self.bingx_price is None:
            return

        diff_percent = ((self.bingx_price - self.binance_price) / self.binance_price) * 100
        
        self.logger.info(
            f"[Price Compare] "
            f"Binance: {self.binance_price:.8f} | "
            f"BingX: {self.bingx_price:.8f} | "
            f"Diff: {diff_percent:.4f}% | "
            f"Time: {time.strftime('%H:%M:%S.%f')[:-3]}"
        )

        if (abs(diff_percent) >= self.config.PRICE_DIFF_THRESHOLD and 
            current_time - self.last_trade_time >= self.config.TRADE_COOLDOWN):
            
            if self.binance_price > self.bingx_price:
                self.logger.info(
                    f"🔍 LONG Signal: Binance price ({self.binance_price:.8f}) is higher than "
                    f"BingX price ({self.bingx_price:.8f}) by {abs(diff_percent):.4f}%"
                )
                self.last_trade_time = current_time
                self.create_position(self.bingx_price, "LONG")
            
            elif self.binance_price < self.bingx_price:
                self.logger.info(
                    f"🔍 SHORT Signal: Binance price ({self.binance_price:.8f}) is lower than "
                    f"BingX price ({self.bingx_price:.8f}) by {abs(diff_percent):.4f}%"
                )
                self.last_trade_time = current_time
                self.create_position(self.bingx_price, "SHORT")

    def create_position(self, price: float, position_side: str) -> None:
        """Create a new position on BingX with TP/SL"""
        try:
            if not self.auto_create_order:
                self.logger.info("Auto order creation is disabled. Skipping order.")
                return

            path = '/openApi/swap/v2/trade/order'
            method = "POST"
            
            params_map = {
                "symbol": self.config.SYMBOL,
                "side": "BUY" if position_side == "LONG" else "SELL",
                "positionSide": position_side,
                "type": "MARKET",
                "quantity": str(self.config.POSITION_SIZE),
                "timestamp": str(int(time.time() * 1000))
            }
            
            response = self.api_client.send_signed_request(method, path, params_map)
            
            if response and response.get('code') == 0:
                self.position_open = True
                order_data = response.get('data', {}).get('order', {})
                order_id = order_data.get('orderId')
                self.current_order_id = order_id
                self.current_order_side = position_side
                self.current_order_price = price
                
                self.set_take_profit_stop_loss(order_id, price, position_side)
                
                self.logger.info(
                    f"✅ Order Successfully Created:\n"
                    f"   Order ID: {order_id}\n"
                    f"   Side: {position_side}\n"
                    f"   Quantity: {order_data.get('quantity')}\n"
                    f"   Status: {order_data.get('status')}"
                )
            else:
                self.logger.error(f"❌ Order Failed: {response}")
                
        except Exception as e:
            self.logger.error(f"❌ Error creating position: {str(e)}")

    def set_take_profit_stop_loss(self, order_id: str, price: float, position_side: str) -> None:
        """Set Take Profit and Stop Loss for the given order"""
        try:
            if position_side == "LONG":
                tp_price = price * (1 + self.config.TP_PERCENT / 100)
                sl_price = price * (1 - self.config.SL_PERCENT / 100)
            else:
                tp_price = price * (1 - self.config.TP_PERCENT / 100)
                sl_price = price * (1 + self.config.SL_PERCENT / 100)

            self.logger.info(
                f"Setting TP/SL for Order {order_id}:\n"
                f"   Take Profit: {tp_price:.8f}\n"
                f"   Stop Loss: {sl_price:.8f}"
            )

            self.monitor_tp_sl(order_id, tp_price, sl_price)

        except Exception as e:
            self.logger.error(f"❌ Error setting TP/SL: {str(e)}")

    def monitor_tp_sl(self, order_id: str, tp_price: float, sl_price: float) -> None:
        """Monitor the Take Profit and Stop Loss levels"""
        def monitor():
            while self.position_open:
                current_price = self.bingx_price

                if current_price is None:
                    time.sleep(1)
                    continue

                if (self.current_order_side == "LONG" and (current_price >= tp_price or current_price <= sl_price)) or \
                   (self.current_order_side == "SHORT" and (current_price <= tp_price or current_price >= sl_price)):
                    self.close_position(order_id)
                    break

                time.sleep(1)

        threading.Thread(target=monitor).start()

    def close_position(self, order_id: str) -> None:
        """Close the position"""
        try:
            path = '/openApi/swap/v2/trade/order'
            method = "DELETE"
            
            params_map = {
                "symbol": self.config.SYMBOL,
                "orderId": order_id,
                "timestamp": str(int(time.time() * 1000))
            }
            
            response = self.api_client.send_signed_request(method, path, params_map)
            
            if response and response.get('code') == 0:
                self.position_open = False
                self.current_order_id = None
                self.current_order_side = None
                self.current_order_price = None
                self.logger.info(f"✅ Position Closed for Order ID: {order_id}")
            else:
                self.logger.error(f"❌ Error closing position: {response}")
                
        except Exception as e:
            self.logger.error(f"❌ Error closing position: {str(e)}")

    def toggle_auto_create(self):
        """Toggle automatic order creation"""
        self.auto_create_order = not self.auto_create_order
        self.logger.info(f"Auto order creation {'enabled' if self.auto_create_order else 'disabled'}")

    def run_position_checker(self) -> None:
        """Continuously check for open positions"""
        while self.is_running:
            self.api_client.verify_position()
            time.sleep(5)  # Check every 5 seconds

    def stop(self):
        """Stop the trading logic"""
        self.is_running = False 