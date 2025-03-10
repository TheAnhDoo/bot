from src.main import TradingBot

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