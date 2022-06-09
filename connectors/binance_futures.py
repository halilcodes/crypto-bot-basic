from pickle import NONE
import time
import requests
import pprint
import json
import logging

import hmac
import hashlib
from urllib.parse import urlencode

from keys import BINANCE_TESTNET_API_PUBLIC, BINANCE_TESTNET_API_SECRET

binance_url = "https://fapi.binance.com"
exchange_info_endpoint = "/fapi/v1/exchangeInfo" #GET
order_book_endpoint = "/fapi/v1/ticker/bookTicker"  # GET
binance_testnet_url = "https://testnet.binancefuture.com"
binance_websocket = "wss://fsrteam.binance.com"
binance_testnet_websocket = "wss://stream.binancefuture.com"

""" 
apis send requests and recieves data 
    for current balance, waiting orders etc.
websockets subscribes to a data feed and gets data stream
    for live market data
"""

logger = logging.getLogger()

binance_futures_url = "https://fapi.binance.com/fapi/v1/exchangeInfo"

"""
1- make_request() should have different class. OR something like;
    if self.isget(method):
        response = self.get_request(endpoint, parameters)
"""


class BinanceFuturesClient:

    def __init__(self, public_key: str, secret_key: str, testnet: bool) -> None:
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
            self.connection_type = "Testnet"
        else:
            self.base_url = "https://fapi.binance.com"
            self.connection_type = "Real Account"
        
        self.public_key = public_key
        self.secret_key = secret_key
        self.headers = {'X-MBX-APIKEY': self.public_key}

        self.prices = dict()
        
        logger.info(f"Binance Futures Client {self.connection_type} successfully initialized")

    def generate_signature(self, data):
        # TODO: Inspect and explore this method.
        return hmac.new(self.secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()

    def make_requests(self, method, endpoint, parameters):
        if method =="GET":
            response = requests.get(self.base_url + endpoint, params=parameters, headers=self.headers)
        elif method == "POST":
            response = requests.post(self.base_url + endpoint, params=parameters, headers=self.headers)
        elif method == "DELETE":
            response = requests.delete(self.base_url + endpoint, params=parameters, headers=self.headers)
        else:
            raise ValueError("so far, only GET, POST and DELETE methods are coded.")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
             method, endpoint, response.json(), response.status_code)
            return None

    def get_contracts(self):
        exchange_info = self.make_requests("GET", "/fapi/v1/exchangeInfo", None)

        if exchange_info is not None:
            contracts = {contract_data['pair']: contract_data for contract_data in exchange_info['symbols']}
            return contracts
        else:
            return None

    def get_historical_candles(self, symbol, interval):
        candlesticks_endpoint = "/fapi/v1/klines"   # GET
        data = dict()
        data['symbol'] = symbol
        data['interval'] = interval
        data['limit'] = 1000

        raw_candles = self.make_requests("GET", candlesticks_endpoint, parameters=data)
        candles = []
        if raw_candles is not None:
            for candle in raw_candles:
                candles.append([candle[0], float(candle[1]), float(candle[2]),
                 float(candle[3]), float(candle[4]), float(candle[5])])

        return candles  # time, open, high, low, close, volume

    def get_bid_ask(self, symbol):
        order_book_endpoint = "/fapi/v1/ticker/bookTicker"  # GET
        data = dict()
        data['symbol'] = symbol
        order_book_request = self.make_requests("GET", order_book_endpoint, data)

        if order_book_request is not None:
            if symbol not in self.prices:
                self.prices[symbol] = {'bid': float(order_book_request['bidPrice']),
                'ask': float(order_book_request['askPrice'])}
            else:
                self.prices[symbol]['bid'] = float(order_book_request['bidPrice'])
                self.prices[symbol]['ask'] = float(order_book_request['askPrice'])
        return self.prices[symbol]

    def get_balances(self):
        endpoint = "/fapi/v1/account"
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self.generate_signature(data)
        
        balances = dict()
        account_data = self.make_requests("GET", endpoint, data)
        if account_data is not None:
            for asset in account_data['assets']:
                balances[asset['asset']] = asset
        return balances

    def place_order(self, symbol, side, quantity, order_type, price=None, tif=None):
        """
        
        """
        endpoint = "/fapi/v1/order"    # POST
        data = dict()
        data['symbol'] = symbol
        data['side'] = side
        data['quantity'] = quantity
        data["type"] = order_type

        if price is not None:
            data['price'] = price
        if tif is not None:
            data['timeInForce'] = tif
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self.generate_signature(data)

        order_status = self.make_requests("POST", endpoint, data)

        return order_status
    
    def cancel_order(self, symbol, order_id):
        endpoint = "/fapi/v1/order" # DELETE
        data = dict()
        data['orderID'] = order_id
        data['symbol'] = symbol

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self.generate_signature(data)

        order_status = self.make_requests("DELETE", endpoint, data)

        return order_status

    def get_order_status(self, symbol, order_id):
        endpoint = "/fapi/v1/order" # GET
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = symbol
        data['orderId'] = order_id
        data['signature'] = self.generate_signature(data)

        order_status = self.make_requests("GET", endpoint, data)

        return order_status

    

if __name__ == "__main__":
    binanceTestnet = BinanceFuturesClient(BINANCE_TESTNET_API_PUBLIC, 
    BINANCE_TESTNET_API_SECRET,testnet=True)
    
    #print(binanceTestnet.get_bid_ask("BTCUSDT"))
    #pprint.pprint(binanceTestnet.place_order("BTCUSDT", "BUY", 0.01, "LIMIT", 20000, "GTC"))
    #pprint.pprint(binanceTestnet.get_order_status("BTCUSDT", 3045148508))
    #pprint.pprint(binanceTestnet.cancel_order("BTCUSDT", 3045148508))