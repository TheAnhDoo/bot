import hmac
from hashlib import sha256
import requests
import time
import json
from typing import Dict, Any, Optional
import logging
from src.config.trade_config import TradeConfig

class BingXClient:
    def __init__(self):
        self.config = TradeConfig()
        self.logger = logging.getLogger(__name__)

    def send_request(self, method: str, path: str, params_str: str, payload: dict = {}) -> str:
        """Send request to BingX API"""
        try:
            signature = self.get_signature(params_str)
            url = f"{self.config.API_URL}{path}?{params_str}&signature={signature}"
            
            headers = {
                'X-BX-APIKEY': self.config.API_KEY
            }
            
            self.logger.debug(f"Sending request to: {url}")
            self.logger.debug(f"Headers: {headers}")
            
            response = requests.request(method, url, headers=headers, data=payload)
            return response.text
            
        except Exception as e:
            self.logger.error(f"Request Error: {e}")
            return ""

    def send_signed_request(self, method: str, path: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Send signed API request to BingX"""
        try:
            params_str = self.parse_params(params)
            signature = self.get_signature(params_str)
            url = f"{self.config.API_URL}{path}?{params_str}&signature={signature}"
            
            headers = {
                'X-BX-APIKEY': self.config.API_KEY
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
                self.config.SECRET_KEY.encode("utf-8"),
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
            return params_str
        except Exception as e:
            self.logger.error(f"Error parsing parameters: {e}")
            return ""

    def verify_api_permissions(self) -> bool:
        """Verify API key permissions by checking account balance"""
        try:
            path = '/openApi/swap/v3/user/balance'
            method = "GET"
            
            params_map = {
                "timestamp": str(int(time.time() * 1000))
            }
            
            params_str = self.parse_params(params_map)
            response_text = self.send_request(method, path, params_str)
            
            self.logger.info(f"Account Balance Response: {response_text}")
            
            response = json.loads(response_text)
            
            if response and response.get('code') == 0:
                self.logger.info("✅ API permissions verified")
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

    def test_order(self) -> None:
        """Test order creation"""
        try:
            self.logger.info("Testing order creation...")
            
            params_map = {
                "symbol": self.config.SYMBOL,
                "side": "BUY",
                "positionSide": "LONG",
                "type": "MARKET",
                "quantity": str(self.config.POSITION_SIZE),
                "timestamp": str(int(time.time() * 1000))
            }
            
            path = '/openApi/swap/v2/trade/order/test'
            method = "POST"
            
            response = self.send_signed_request(method, path, params_map)
            self.logger.info(f"Test Order Response: {response}")
            
        except Exception as e:
            self.logger.error(f"Test Order Error: {e}") 