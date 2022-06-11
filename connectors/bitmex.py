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

from models import Contract

logger = logging.getLogger()


def _has_underscore(input_string):
    return any(char == "_" for char in input_string)


def _has_numbers(input_string):
    return any(char.isdigit() for char in input_string)


def _is_tradable(symbol: str, ends_with="USDT") -> bool:
    return not _has_numbers(symbol) and not _has_underscore(symbol)\
           and symbol.endswith(ends_with)


def _dict_to_string(data: typing.Dict):
    result = "?"
    for key, value in data.items():
        result += f"{key}={value}&"
    return result[:-1]


class BitmexClient:

    def __init__(self, public_key: str, secret_key: str):
        self._public_key = public_key
        self._secret_key = secret_key
        self._base_url = "https://testnet.bitmex.com/api/v1"
        self._wss_url = "wss://ws.testnet.bitmex.com/realtime"
        self.connection_type = "Testnet"
        self.platform = "bitmex"
        self.header = {"api-expires": str(), "api-key": self._public_key, "api-signature": str()}

    def _generate_signature(self, method: str, endpoint: str, data: typing.Dict) -> str:

        api_secret = self._secret_key
        verb = method
        path = "/api/v1"+endpoint
        expires = str(int(time.time() * 1000))
        full_msg = verb+path + _dict_to_string(data) + expires

        msg = full_msg.encode()
        print(full_msg)

        return hmac.new(api_secret.encode(), msg, hashlib.sha256).hexdigest()

    def _make_request(self, method: str, endpoint: str, params: dict):

        self.header["api-expires"] = str(int(time.time() * 1000))
        self.header["api-signature"] = self._generate_signature(method=method, endpoint=endpoint, data=params)

        try:
            if method == "GET":
                response = requests.get(url=self._base_url + endpoint, params=params, headers=self.header)
            elif method == "POST":
                response = requests.post(url=self._base_url + endpoint, params=params, headers=self.header)
            elif method == "DELETE":
                response = requests.delete(url=self._base_url + endpoint, params=params, headers=self.header)
            else:
                raise ValueError("so far, only GET, POST and DELETE methods are coded.")
        except Exception as e:
            logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
            return None
        print(response.status_code)
        pprint.pprint(response.json())
        if response.status_code == 200:
            return response.json()

    def get_contracts(self) -> typing.Dict[str, Contract]:
        endpoint = "/instrument/active"
        contracts = dict()
        output = self._make_request("GET", endpoint, dict())
        if output is not None:
            for contract in output:
                symbol = contract['symbol']

                if _is_tradable(symbol, "USDT"):
                    contracts[symbol] = Contract(self.platform, contract)

        return contracts

    def get_balances(self):
        # TODO: Not finished
        endpoint = "/user/margin"
        method = "GET"
        data = dict()
        data['currency'] = "all"

        output = self._make_request(method=method, endpoint=endpoint, params=data)
        if output is not None:
            return output

    def place_order(self, contract: Contract, side: str, quantity: float,
                    order_type: str, price=None, tif="GoodTillCancel"):
        endpoint = "/order"
        method = "POST"
        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side
        data['orderQty'] = quantity
        data['ordType'] = order_type
        if price is not None:
            data['price'] = price
        if tif is not None:
            data['timeInForce'] = tif

        output = self._make_request(method=method, endpoint=endpoint, params=data)

        if output is not None:
            return output


if __name__ == "__main__":

    bitmex = BitmexClient(BITMEX_API_PUBLIC, BITMEX_API_SECRET)
    # for each in bitmex.get_contracts():
    #     print(each.symbol)
    data = dict()
    data["symbol"] = "LINKUSD"
    data["positionCurrency"] = "LINK"
    data["quoteCurrency"] = "USD"
    btc = Contract("bitmex", data)
    pprint.pprint(bitmex.place_order(btc, "Buy", 50, "Limit", 7, "GoodTillCancel"))
