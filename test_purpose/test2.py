import requests

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'app_version': '5.7.7',
    'appid': '30004',
    'appsiteid': '0',
    'authorization': 'Bearer eyJicyI6MCwiYWlkIjoxMDAwOSwicGlkIjoiMzAiLCJzaWQiOiI3MmY4YTNmZDFkZTQ5NDNkYTI2NmZhMzdkZjkyNTAxYiIsImFsZyI6IkhTNTEyIn0.eyJzdWIiOiIxNDEzNDgzMzg2Njc1NTE5NDkyIiwiZXhwIjoxNzQxNjE3NDQ3LCJqdGkiOiIyZjc4MmVjOC01NzBhLTRkYzUtYjMxZi1kNjhhZWY5ZGFjMWYifQ.Af0963UKkgMAxGpAWDCdQW70LTkyIBX5wxS7XDfEUVqD49moxHtON-BxgvUeo0Lvh0aafQvSoWA9DCQKWLPnzg',
    'channel': 'official',
    'content-type': 'application/json',
    'device_brand': 'Mac OSX_Chrome_133.0.0.0',
    'device_id': 'fc47764b4f444247bd7508f80c933488',
    'lang': 'en',
    'mainappid': '10009',
    'origin': 'https://bingx.com',
    'platformid': '30',
    'priority': 'u=1, i',
    'referer': 'https://bingx.com/',
    'reg_channel': 'official',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'sec-fetch-storage-access': 'active',
    'sign': '49F3E0D883728864933044FAD1355E7DA8E1557D130856C3542645E1E62D6A0A',
    'timestamp': '1741283234865',
    'timezone': '7',
    'traceid': '847bf30c95194fe0be62ee969b037dac',
    'trade_env': 'simulation',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

json_data = {
    'userId': '1413483386675519492',
    'tradingUnit': 'COIN',
    'volumeType': 'Cont',
    'feeType': 0,
    'symbol': 'ETC-USDT',
    'positionId': '1897707233188249600',
    'stopLossPrice': '19.936',
    'stopLossTradeType': 'Market',
    'stopLossEntrustPrice': '',
    'stopLossTriggerSource': 'TradePrice',
    'stopLossVolume': '200.00',
    'ensureTrigger': False,
    'takeProfitTradeType': 'Market',
    'takeProfitEntrustPrice': '',
    'takeProfitPrice': '20.000',
    'takeProfitTriggerSource': 'TradePrice',
    'takeProfitVolume': '200.00',
    'ensureTakeProfit': 0,
    'orderTypes': 'PtpStop,PstStop',
}

response = requests.post('https://api-swap.we-api.com/api/swap/v2/proxy/trigger/close/set/post', headers=headers, json=json_data)

# Note: json_data will not be serialized by requests
# exactly as it was in the original request.
#data = '{"userId":"1413483386675519492","tradingUnit":"COIN","volumeType":"Cont","feeType":0,"symbol":"ETC-USDT","positionId":"1897705282715254784","stopLossPrice":"19.836","stopLossTradeType":"Market","stopLossEntrustPrice":"","stopLossTriggerSource":"TradePrice","stopLossVolume":"200.00","ensureTrigger":false,"takeProfitTradeType":"Market","takeProfitEntrustPrice":"","takeProfitPrice":"20.048","takeProfitTriggerSource":"TradePrice","takeProfitVolume":"200.00","ensureTakeProfit":0,"orderTypes":"PtpStop,PstStop"}'
#response = requests.post('https://api-swap.we-api.com/api/swap/v2/proxy/trigger/close/set/post', headers=headers, data=data)