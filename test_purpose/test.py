import time
import hashlib
import hmac
import requests
import json

# API Credentials
API_KEY = "DcYvbavAYfA3oO44wuvDqJzj6FVoiL5lGhPqr8gkfVaJKz8r8x4EAsoiEsai0yaOPUuKrtqXhG1HeImjH8Xcw"
SECRET_KEY = "YywDSqUaOYTEUoyZsdkyws1Kbxrd6TDU1WJRGjZ5YTtLe8twTy6wa8BEQnQsxEV1nxak3m5U3ER8O0kfQlmw"

# BingX API Endpoints
BASE_URL = "https://open-api.bingx.com"
GET_OPEN_ORDERS = "/openApi/swap/v2/trade/openOrders"
CANCEL_REPLACE_ORDER = "/openApi/swap/v1/trade/cancelReplace"
GET_POSITIONS = "/openApi/swap/v2/user/positions"

# Symbol (Modify as needed)
SYMBOL = "LTC-USDT"

# ✅ Hardcoded TP & SL values
NEW_TP_PRICE = 110  # Modify this as needed
NEW_SL_PRICE = 89.0  # Modify this as needed

def get_timestamp():
    return int(time.time() * 1000)

def generate_signature(params):
    sorted_params = sorted(params.items())
    query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
    
    return hmac.new(
        SECRET_KEY.encode(), query_string.encode(), hashlib.sha256
    ).hexdigest()

def get_open_positions():
    params = {
        "symbol": SYMBOL,
        "timestamp": get_timestamp()
    }
    params["signature"] = generate_signature(params)
    
    headers = {"X-BX-APIKEY": API_KEY}
    
    try:
        response = requests.get(BASE_URL + GET_POSITIONS, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 0:
            print(f"API Error: {data.get('msg', 'Unknown error')}")
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON:", response.text)
        return None

    positions = data.get("data", [])
    
    if not isinstance(positions, list):
        print("⚠️ Unexpected API response format.")
        return None

    if not positions:
        print("⚠️ No open positions found.")
        return None
    
    return positions[0]  # Assume only one position per symbol

def get_open_orders():
    params = {
        "symbol": SYMBOL,
        "timestamp": get_timestamp()
    }
    params["signature"] = generate_signature(params)
    
    headers = {"X-BX-APIKEY": API_KEY}
    
    try:
        response = requests.get(BASE_URL + GET_OPEN_ORDERS, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != 0:
            print(f"API Error: {data.get('msg', 'Unknown error')}")
            return []
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []
    except json.JSONDecodeError:
        print("Error decoding JSON:", response.text)
        return []

    orders = data.get("data", {}).get("orders", [])

    order_ids = [
        {"orderId": order.get("orderId"), "type": order.get("type")}
        for order in orders
        if order.get("type") in ["STOP_MARKET", "TAKE_PROFIT_MARKET"]
    ]

    print("Open SL/TP Orders:", order_ids)
    return order_ids

def cancel_replace_order(order_id, new_order_params):
    params = {
        "cancelReplaceMode": "STOP_ON_FAILURE",
        "cancelOrderId": order_id,
        "symbol": SYMBOL,
        "side": new_order_params["side"],
        "positionSide": new_order_params["positionSide"],
        "type": new_order_params["type"],  
        "quantity": new_order_params["quantity"],  
        "stopPrice": new_order_params["stopPrice"],  
        "timestamp": get_timestamp()
    }
    
    params["signature"] = generate_signature(params)
    
    url = f"{BASE_URL}{CANCEL_REPLACE_ORDER}"
    headers = {"X-BX-APIKEY": API_KEY}
    
    try:
        response = requests.post(url, headers=headers, json=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != 0:
            print(f"❌ Cancel & Replace Order Error: {data.get('msg', 'Unknown error')}")
        
        return data
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON:", response.text)
        return None

def main():
    open_positions = get_open_positions()
    
    if not open_positions:
        print("⚠️ No open positions detected.")
        return
    
    position_side = open_positions.get("positionSide", "LONG")
    quantity = float(open_positions.get("positionAmt", 0))

    if quantity == 0:
        print("⚠️ No open position size detected.")
        return
    
    open_orders = get_open_orders()
    
    if not open_orders:
        print("No Stop-Loss or Take-Profit orders found.")
        return
    
    for order in open_orders:
        order_id = order["orderId"]
        order_type = order["type"]
        print(f"\n🔄 Cancelling & Replacing {order_type} Order ID: {order_id}...")

        # ✅ Use predefined TP/SL values
        new_order_params = {
            "type": order_type,  
            "quantity": quantity,
            "stopPrice": NEW_TP_PRICE if order_type == "TAKE_PROFIT_MARKET" else NEW_SL_PRICE,
            "side": "SELL" if position_side == "LONG" else "BUY",
            "positionSide": position_side
        }

        result = cancel_replace_order(order_id, new_order_params)
        print(f"✅ Cancel & Replace Result: {result}")

if __name__ == "__main__":
    main()
