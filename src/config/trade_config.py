from dataclasses import dataclass

@dataclass
class TradeConfig:
    # Trading Parameters
    SYMBOL: str = "RARE-USDT"
    SYMBOL_LOWER: str = "rareusdt"
    PRICE_DIFF_THRESHOLD: float = 5  # % difference to trigger trade
    POSITION_SIZE: float = 400  # Trade size
    TRADE_COOLDOWN: int = 5  # Cooldown in seconds
    TP_PERCENT: float = 2  # Take Profit percentage
    SL_PERCENT: float = 1  # Stop Loss percentage

    # API Configuration
    API_URL: str = "https://open-api.bingx.com"
    API_KEY: str = "DcYvbavAYfA3oO44wuvDqJzj6FVoiL5lGhPqr8gkfVaJKz8r8x4EAsoiEsai0yaOPUuKrtqXhG1HeImjH8Xcw"
    SECRET_KEY: str = "YywDSqUaOYTEUoyZsdkyws1Kbxrd6TDU1WJRGjZ5YTtLe8twTy6wa8BEQnQsxEV1nxak3m5U3ER8O0kfQlmw"

    # WebSocket Configuration
    @property
    def BINANCE_SOCKET(self) -> str:
        return f"wss://fstream.binance.com/ws/{self.SYMBOL_LOWER}@markPrice@1s"
    
    BINGX_SOCKET: str = "wss://open-api-swap.bingx.com/swap-market"
    WEBSOCKET_TIMEOUT: int = 30
    RECONNECT_DELAY: int = 5
    MAX_RETRIES: int = 3

    # System Configuration
    DEBUG_MODE: bool = True
    PRICE_UPDATE_INTERVAL: int = 1  # seconds 