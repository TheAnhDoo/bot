# Trading Bot

A Python-based trading bot that monitors price differences between Binance and BingX exchanges and executes trades based on configurable parameters. The bot uses WebSocket connections to get real-time mark prices and executes trades when price differences exceed a specified threshold.

## Features

- Real-time price monitoring from Binance and BingX using WebSocket connections
- Automatic trade execution based on price differences
- Take Profit and Stop Loss management
- Configurable trading parameters
- Automatic reconnection handling for WebSocket connections
- Detailed logging system
- Manual and automatic trading modes
- Support for compressed WebSocket messages
- Ping/Pong heartbeat mechanism

## Project Structure

```
trading-bot/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main entry point and bot orchestration
│   ├── config/
│   │   ├── __init__.py
│   │   └── trade_config.py     # Configuration parameters
│   ├── core/
│   │   ├── __init__.py
│   │   └── trading_logic.py    # Core trading logic and decision making
│   ├── api/
│   │   ├── __init__.py
│   │   └── bingx_client.py     # BingX API interactions
│   └── websocket/
│       ├── __init__.py
│       └── websocket_manager.py # WebSocket connection management
├── logs/                       # Log files directory
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Component Details

### 1. Main Bot (`src/main.py`)
- Initializes all components
- Sets up logging
- Handles keyboard shortcuts
- Manages the main bot loop

### 2. Configuration (`src/config/trade_config.py`)
Contains all configurable parameters:
- Trading pair symbol
- Price difference threshold
- Position size
- Trade cooldown
- Take Profit/Stop Loss percentages
- API credentials
- WebSocket settings

### 3. Trading Logic (`src/core/trading_logic.py`)
- Implements trading strategy
- Manages position state
- Handles order creation and management
- Implements Take Profit/Stop Loss logic

### 4. API Client (`src/api/bingx_client.py`)
- Handles all BingX API interactions
- Manages API authentication
- Implements request signing
- Handles API responses

### 5. WebSocket Manager (`src/websocket/websocket_manager.py`)
- Manages WebSocket connections
- Handles message processing
- Implements reconnection logic
- Processes compressed messages
- Manages Ping/Pong heartbeat

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd trading-bot
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your API keys in `src/config/trade_config.py`:
```python
API_KEY = "your-api-key"
SECRET_KEY = "your-secret-key"
```

## Usage

1. Start the bot:
```bash
python run.py
```

2. The bot will:
   - Verify API permissions
   - Connect to WebSocket streams
   - Monitor price differences
   - Execute trades when conditions are met

3. Controls:
   - If running with administrator privileges:
     - Press 'c' to toggle automatic order creation
   - If running without administrator privileges:
     - Type 'toggle' to toggle automatic order creation
     - Type 'exit' to stop the bot
   - Press Ctrl+C to stop the bot at any time

## Configuration

You can modify the following parameters in `src/config/trade_config.py`:

### Trading Parameters
- `SYMBOL`: Trading pair (default: "RARE-USDT")
- `PRICE_DIFF_THRESHOLD`: Price difference threshold to trigger trades (default: 2.5%)
- `POSITION_SIZE`: Size of each trade (default: 23.5)
- `TRADE_COOLDOWN`: Minimum time between trades (default: 5 seconds)
- `TP_PERCENT`: Take Profit percentage (default: 2%)
- `SL_PERCENT`: Stop Loss percentage (default: 1%)

### WebSocket Configuration
- `WEBSOCKET_TIMEOUT`: Connection timeout (default: 30 seconds)
- `RECONNECT_DELAY`: Delay between reconnection attempts (default: 5 seconds)
- `MAX_RETRIES`: Maximum number of reconnection attempts (default: 3)

### System Configuration
- `DEBUG_MODE`: Enable/disable debug logging (default: True)
- `PRICE_UPDATE_INTERVAL`: Time between price checks (default: 1 second)

## Logging

Logs are saved to the `logs` directory with the format `trading_bot_YYYYMMDD.log`. The logs include:
- Price updates from both exchanges
- Trade signals and executions
- WebSocket connection status
- API interactions
- Error messages and warnings

## Trading Strategy

The bot implements the following trading strategy:
1. Monitors real-time mark prices from both Binance and BingX
2. Calculates price difference percentage
3. When price difference exceeds threshold:
   - If Binance price > BingX price: Opens LONG position
   - If Binance price < BingX price: Opens SHORT position
4. Sets Take Profit and Stop Loss levels
5. Monitors position and closes when TP/SL is hit

## Error Handling

The bot includes comprehensive error handling for:
- WebSocket connection issues
- API request failures
- Invalid message formats
- Network timeouts
- Authentication errors

## Security Considerations

1. API Keys:
   - Never commit API keys to version control
   - Use environment variables or secure configuration files
   - Regularly rotate API keys

2. WebSocket Security:
   - Uses secure WebSocket connections (wss://)
   - Implements proper authentication
   - Handles connection errors gracefully

## Disclaimer

This bot is for educational purposes only. Use at your own risk. Always:
1. Test with small amounts first
2. Monitor the bot's performance
3. Understand the trading strategy
4. Be aware of market risks
5. Keep your API keys secure

## Contributing

Feel free to submit issues and enhancement requests!
