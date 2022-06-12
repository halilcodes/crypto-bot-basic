import hashlib
import hmac
import pprint
from urllib.parse import urlencode
import time
import requests
import json
import typing
import logging
from keys import *
import threading
from models import *

logger = logging.getLogger()


def _has_underscore(input_string):
    return any(char == "_" for char in input_string)


def _has_numbers(input_string):
    return any(char.isdigit() for char in input_string)


def _is_tradable(symbol: str, ends_with="USDT") -> bool:
    return not _has_numbers(symbol) and not _has_underscore(symbol)\
           and symbol.endswith(ends_with)


class BitmexClient:

    def __init__(self, public_key: str, secret_key: str, testnet: bool):
        self._public_key = public_key
        self._secret_key = secret_key
        if testnet:
            self._base_url = "https://testnet.bitmex.com/api/v1"
            self._wss_url = "wss://ws.testnet.bitmex.com/realtime"
            self.connection_type = "Testnet"
        else:
            self._base_url = "https://www.bitmex.com/api/v1"
            self._wss_url = "wss://ws.bitmex.com/realtime"
            self.connection_type = "Real Account"

        self._ws = None
        self.platform = "bitmex"

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.prices = dict()

        # t = threading.Thread(target=self._start_ws)
        # t.start()

        logger.info("Bitmex Client successfully initialized")

    def _generate_signature(self, method: str, endpoint: str, expires: str, data: typing.Dict) -> str:

        api_secret = self._secret_key
        verb = method
        path = "/api/v1"+endpoint
        message = verb+path + "?" + urlencode(data) + expires if len(data) > 0 else verb + path + expires

        return hmac.new(api_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    def _make_request(self, method: str, endpoint: str, params: typing.Dict):

        api_expires = str(int(time.time() + 5))
        header = {"api-expires": api_expires, "api-key": self._public_key,
                  "api-signature": self._generate_signature(method=method, endpoint=endpoint,
                                                            expires=api_expires, data=params)}

        try:
            if method == "GET":
                response = requests.get(url=self._base_url + endpoint, params=params, headers=header)
            elif method == "POST":
                response = requests.post(url=self._base_url + endpoint, params=params, headers=header)
            elif method == "DELETE":
                response = requests.delete(url=self._base_url + endpoint, params=params, headers=header)
            else:
                raise ValueError("so far, only GET, POST and DELETE methods are coded.")
        except Exception as e:
            logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
            return None

        if response.status_code == 200:
            return response.json()
        else:
            print(response.status_code)
            pprint.pprint(response.json())

    def get_contracts(self) -> typing.Dict[str, Contract]:
        endpoint = "/instrument/active"
        contracts = dict()
        instruments = self._make_request("GET", endpoint, dict())
        if instruments is not None:
            for s in instruments:
                symbol = s['symbol']
                if _is_tradable(symbol, ""):
                    contracts[s['symbol']] = Contract(self.platform, s)

        return contracts

    def get_balances(self) -> typing.Dict[str, Balance]:
        # TODO: Not finished
        margin_endpoint = "/user/margin"
        method = "GET"
        data = dict()
        data['currency'] = "all"
        margin_data = self._make_request(method=method, endpoint=margin_endpoint, params=data)
        balances = dict()
        if margin_data is not None:
            for each in margin_data:
                balances[each['currency']] = Balance(self.platform, each)

        return balances

    def get_historical_candles(self, contract: Contract, timeframe: str) -> typing.List[Candle]:
        endpoint = "/trade/bucketed"
        data = dict()
        data['symbol'] = contract.symbol
        data['partial'] = True
        data['binSize'] = timeframe
        data['count'] = 500
        
        raw_candles = self._make_request(method="GET", endpoint=endpoint, params=data)
        
        candles = []
        
        if raw_candles is not None:
            for each in raw_candles:
                candles.append(Candle(self.platform, each))

        return candles

    def place_order(self, contract: Contract, side: str, quantity: int,
                    order_type: str, price=None, tif="GoodTillCancel") -> OrderStatus:
        endpoint = "/order"
        method = "POST"
        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side.capitalize()
        data['orderQty'] = quantity
        data['ordType'] = order_type.capitalize()
        if price is not None:
            data['price'] = price
        if tif is not None:
            data['timeInForce'] = tif

        order_info = self._make_request(method=method, endpoint=endpoint, params=data)
        
        if order_info is not None:
            order_info = OrderStatus(self.platform, order_info)

        return order_info
        
    def get_order_status(self, order_id: str, contract: Contract):
        endpoint = "/order"
        method = "GET"
        data = dict()
        data['symbol'] = contract.symbol
        data['reverse'] = True

        order_status = self._make_request(method=method, endpoint=endpoint, params=data)

        if order_status is not None:
            for order in order_status:
                if order['orderID'] == order_id:
                    order_status = OrderStatus(self.platform, order)
                    return order_status

    def cancel_order(self, order_id: str):
        endpoint = "/order"
        method = "DELETE"
        data = dict()
        data['orderID'] = order_id

        order_info = self._make_request(method=method, endpoint=endpoint, params=data)

        if order_info is not None:
            order_info = OrderStatus(self.platform, order_info[0])

        return order_info


if __name__ == "__main__":

    bitmex = BitmexClient(BITMEX_TESTNET_API_PUBLIC, BITMEX_TESTNET_API_SECRET, testnet=True)
    pprint.pprint(bitmex.get_order_status())
