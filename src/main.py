import logging
import keyboard
import threading
import time
import os
from datetime import datetime
from src.config.trade_config import TradeConfig
from src.core.trading_logic import TradingLogic
from src.websocket.websocket_manager import WebSocketManager

def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    log_file = os.path.join('logs', f'trading_bot_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.config = TradeConfig()
        self.logger = setup_logging()
        
        # Initialize components
        self.trading_logic = TradingLogic()
        self.websocket_manager = WebSocketManager(self.trading_logic.update_price)
        
        # Try to setup keyboard shortcut, fallback to manual toggle if it fails
        try:
            keyboard.add_hotkey('c', self.trading_logic.toggle_auto_create)
            self.use_keyboard = True
        except OSError as e:
            self.logger.warning("⚠️ Keyboard shortcuts require administrator privileges. Using manual toggle instead.")
            self.use_keyboard = False
        
        # Verify API connection
        if not self.trading_logic.api_client.verify_api_permissions():
            self.logger.warning("⚠️ API verification failed at startup")

    def run(self):
        """Start the trading bot"""
        self.logger.info("🔹 Starting Trading Bot...")
        
        # Start WebSocket connections
        self.websocket_manager.start()
        
        # Start position checker
        position_checker_thread = threading.Thread(
            target=self.trading_logic.run_position_checker
        )
        position_checker_thread.start()

        try:
            if self.use_keyboard:
                self.logger.info("Press 'c' to toggle auto order creation")
            else:
                self.logger.info("Enter 'toggle' to toggle auto order creation, or 'exit' to stop")
            
            while True:
                if not self.use_keyboard:
                    command = input().strip().lower()
                    if command == 'toggle':
                        self.trading_logic.toggle_auto_create()
                    elif command == 'exit':
                        break
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("\n🔻 Stopping Trading Bot...")
            self.trading_logic.stop()
            self.websocket_manager.stop()
            time.sleep(1)
            self.logger.info("✅ Stopped.")

if __name__ == "__main__":
    bot = TradingBot()
    
    # Test API order
    response = input("Test order creation? (y/n): ")
    if response.lower() == 'y':
        bot.trading_logic.api_client.test_order()
    
    # Ask to start bot
    response = input("Start trading bot? (y/n): ")
    if response.lower() == 'y':
        bot.run()
    else:
        print("Bot execution cancelled") 