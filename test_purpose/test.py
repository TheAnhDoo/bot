import time
import hashlib
import hmac
import requests
import json

# API credentials
API_KEY = "DcYvbavAYfA3oO44wuvDqJzj6FVoiL5lGhPqr8gkfVaJKz8r8x4EAsoiEsai0yaOPUuKrtqXhG1HeImjH8Xcw"
SECRET_KEY = "YywDSqUaOYTEUoyZsdkyws1Kbxrd6TDU1WJRGjZ5YTtLe8twTy6wa8BEQnQsxEV1nxak3m5U3ER8O0kfQlmw"

# BingX API endpoints
BASE_URL = "https://open-api.bingx.com"
GET_OPEN_ORDERS = "/openApi/swap/v2/trade/openOrders"
CANCEL_ORDER = "/openApi/swap/v2/trade/cancel"

# Symbol (Change as needed)
SYMBOL = "LTC-USDT"

def get_timestamp():
    """Returns current timestamp in milliseconds."""
    return str(int(time.time() * 1000))

def generate_signature(params):
    """Generates HMAC SHA256 signature."""
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return hmac.new(SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def get_open_orders():
    """Fetches open orders and filters only SL & TP orders."""
    params = {"symbol": SYMBOL, "timestamp": get_timestamp()}
    params["signature"] = generate_signature(params)
    
    headers = {"X-BX-APIKEY": API_KEY}
    response = requests.get(BASE_URL + GET_OPEN_ORDERS, headers=headers, params=params)
    
    try:
        data = response.json()
        if not isinstance(data, dict):
            print("Unexpected response format:", data)
            return []
    except requests.exceptions.JSONDecodeError:
        print("Error decoding JSON:", response.text)
        return []
    # Ensure 'data' and 'orders' exist before accessing them
    orders = data.get("data", {}).get("orders", [])

    # Extract order IDs safely
    order_ids = [
        {"orderId": order.get("orderId"), "type": order.get("type")}
        for order in orders
        if order.get("type") in ["STOP_MARKET", "TAKE_PROFIT_MARKET"]
    ]

    # Print the result
    print(order_ids)
    return(order_ids)
def cancel_order(order_id):
    """Cancels a given order by order ID."""
    params = {
        "symbol": SYMBOL,
        "orderId": order_id,
        "timestamp": get_timestamp()
    }
    params["signature"] = generate_signature(params)
    
    headers = {"X-BX-APIKEY": API_KEY}
    response = requests.post(BASE_URL + CANCEL_ORDER, headers=headers, params=params)
    
    try:
        data = response.json()
        return data
    except requests.exceptions.JSONDecodeError:
        print("Error decoding JSON:", response.text)
        return None

def main():
    """Main function to cancel SL & TP orders."""
    open_orders = get_open_orders()
    
    if not open_orders:
        print("No Stop-Loss or Take-Profit orders found.")
        return
    
    for order in open_orders:
        print(open_orders)
        order_id = order["orderId"]
        order_type = order["type"]
        print(f"Cancelling {order_type} Order ID: {order_id}")
        
        result = cancel_order(order_id)
        print(f"Cancel Result: {result}")

if __name__ == "main":
    main()