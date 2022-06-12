import pprint
import time
import requests
import typing
import json
import logging
import hmac
import hashlib
from urllib.parse import urlencode

import websocket

import threading

from keys import BINANCE_TESTNET_API_PUBLIC, BINANCE_TESTNET_API_SECRET


from models import *

# binance_url = "https://fapi.binance.com"
# exchange_info_endpoint = "/fapi/v1/exchangeInfo" #GET
# order_book_endpoint = "/fapi/v1/ticker/bookTicker"  # GET
# binance_testnet_url = "https://testnet.binancefuture.com"
# binance_websocket = "wss://fsrteam.binance.com"
# binance_testnet_websocket = "wss://stream.binancefuture.com"

""" 
apis send requests and receive data 
    for current balance, waiting orders etc.
websockets subscribes to a data feed and gets data stream
    for live market data
"""

logger = logging.getLogger()

binance_futures_url = "https://fapi.binance.com/fapi/v1/exchangeInfo"

# TODO:
"""
1- make_request() should have different class. OR something like;
    if self.is_get(method):
        response = self.get_request(endpoint, parameters)

2- Balance should be a totally different class

3- all this should be a child class of a strategy class (to try a strategy on different platforms etc.)
"""


class BinanceFuturesClient:

    def __init__(self, public_key: str, secret_key: str, testnet: bool) -> None:
        if testnet:
            self._base_url = "https://testnet.binancefuture.com"
            self._wss_url = "wss://testnet.binancefuture.com/ws"
            self.connection_type = "Testnet"
        else:
            self._base_url = "https://fapi.binance.com"
            self._wss_url = "wss://fsrteam.binance.com/ws"
            self.connection_type = "Real Account"

        self.platform = "binance"
        self._public_key = public_key
        self._secret_key = secret_key
        self.headers = {'X-MBX-APIKEY': self._public_key}

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.prices = dict()
        self._ws_id = 1
        self._ws = None

        t = threading.Thread(target=self._start_ws)
        t.start()

        logger.info(f"Binance Futures Client {self.connection_type} successfully initialized")

    def _generate_signature(self, data: typing.Dict) -> str:
        # TODO: Inspect and explore this method.
        return hmac.new(self._secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()

    def _make_requests(self, method: str, endpoint: str, parameters: typing.Dict):
        if method == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=parameters, headers=self.headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=parameters, headers=self.headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=parameters, headers=self.headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        else:
            raise ValueError("so far, only GET, POST and DELETE methods are coded.")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         method, endpoint, response.json(), response.status_code)
            return None

    def get_contracts(self) -> typing.Dict[str, Contract]:
        exchange_info = self._make_requests("GET", "/fapi/v1/exchangeInfo", dict())
        contracts = dict()

        if exchange_info is not None:
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['pair']] = Contract(self.platform, contract_data)

        return contracts

    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]:
        candlesticks_endpoint = "/fapi/v1/klines"   # GET
        data = dict()
        data['symbol'] = contract.symbol
        data['interval'] = interval
        data['limit'] = 1000

        raw_candles = self._make_requests("GET", candlesticks_endpoint, parameters=data)
        candles = []
        if raw_candles is not None:
            for candle in raw_candles:
                candles.append(Candle(self.platform, candle))

        return candles  # time, open, high, low, close, volume

    def get_bid_ask(self, contract: Contract) -> typing.Dict[str, float]:
        order_book_endpoint = "/fapi/v1/ticker/bookTicker"  # GET
        data = dict()
        data['symbol'] = contract.symbol
        order_book_request = self._make_requests("GET", order_book_endpoint, data)

        if order_book_request is not None:
            if contract.symbol not in self.prices:
                self.prices[contract.symbol] = {'bid': float(order_book_request['bidPrice']),
                                                'ask': float(order_book_request['askPrice'])}
            else:
                self.prices[contract.symbol]['bid'] = float(order_book_request['bidPrice'])
                self.prices[contract.symbol]['ask'] = float(order_book_request['askPrice'])

            return self.prices[contract.symbol]

    def get_balances(self) -> typing.Dict[str, Balance]:
        endpoint = "/fapi/v1/account"
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)
        
        balances = dict()
        account_data = self._make_requests("GET", endpoint, data)
        if account_data is not None:
            for asset in account_data['assets']:
                balances[asset['asset']] = Balance(self.platform, asset)

        return balances

    def place_order(self, contract: Contract, side: str, quantity: float, order_type: str, price=None, tif=None)\
            -> OrderStatus:
        """
        
        """
        endpoint = "/fapi/v1/order"    # POST
        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side
        data['quantity'] = quantity
        data["type"] = order_type

        if price is not None:
            data['price'] = price
        if tif is not None:
            data['timeInForce'] = tif
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        order_status = self._make_requests("POST", endpoint, data)

        if order_status is not None:
            order_status = OrderStatus(self.platform, order_status)

        return order_status

    # TODO: There should be an easy way to get order id and store them 
    # in order to access when we need to cancel or get status

    def place_market_order(self):
        return
    
    def place_limit_order(self):
        return

    def cancel_order(self, contract: Contract, order_id: int):
        endpoint = "/fapi/v1/order"  # DELETE
        data = dict()
        data['orderID'] = order_id
        data['symbol'] = contract.symbol

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        order_status = self._make_requests("DELETE", endpoint, data)

        if order_status is not None:
            order_status = OrderStatus(self.platform, order_status)

        return order_status

    def get_order_status(self, contract: Contract, order_id: int) -> OrderStatus:
        endpoint = "/fapi/v1/order"  # GET
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = contract.symbol
        data['orderId'] = order_id
        data['signature'] = self._generate_signature(data)

        order_status = self._make_requests("GET", endpoint, data)

        if order_status is not None:
            order_status = OrderStatus(self.platform, order_status)

        return order_status

    def get_current_open_orders(self, symbol=None) -> list:
        """
        returns all open positions in dict format
        if symbol is entered, returns only open positions for that symbol
        """
        endpoint = "/fapi/v1/openOrders"    # GET
        data = dict()
        data['timestamp'] = int(time.time() * 1000)

        if symbol is not None:
            data['symbol'] = symbol

        data['signature'] = self._generate_signature(data)

        open_orders = self._make_requests("GET", endpoint, data)

        return open_orders

    def _start_ws(self):
        self._ws = websocket.WebSocketApp(self._wss_url,
                                          on_open=self._on_open, on_close=self._on_close,
                                          on_error=self._on_error, on_message=self._on_message)
        while True:
            try:
                self._ws.run_forever()
            except Exception as e:
                logger.error("Binance error in run_forever() method: %s", e)
            time.sleep(2)
    
    def _on_open(self, ws):
        logger.info("Binance WebSocket connection opened.")

        self.subscribe_channel(list(self.contracts.values()), "bookTicker")

    def _on_close(self, ws):
        logger.warning("Binance WebSocket connection closed.")

    def _on_error(self, ws, msg: str):
        logger.error("Binance WebSocket connection error: %s", msg)

    def _on_message(self, ws, msg: str):

        data = json.loads(msg)

        if "e" in data:
            if data['e'] == 'bookTicker':

                symbol = data['s']

                if symbol not in self.prices:
                    self.prices[symbol] = {'bid': float(data['b']),
                                           'ask': float(data['a'])}
                else:
                    self.prices[symbol]['bid'] = float(data['b'])
                    self.prices[symbol]['ask'] = float(data['a'])

    def subscribe_channel(self, contracts: typing.List[Contract], channel: str):
        data = dict()
        data['method'] = "SUBSCRIBE"
        data['params'] = []

        for contract in contracts:
            data['params'].append(contract.symbol.lower() + "@" + channel)
        data['id'] = self._ws_id

        try:
            self._ws.send(json.dumps(data))
        except Exception as e:
            logger.error("Websocket error while subscribing to %s %s updates: %s",
                         len(contracts), channel, e)

        self._ws_id += 1
        return


if __name__ == "__main__":
    binance = BinanceFuturesClient(BINANCE_TESTNET_API_PUBLIC,
                                   BINANCE_TESTNET_API_SECRET, testnet=True)

    pprint.pprint(binance.get_balances())
