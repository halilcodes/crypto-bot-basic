import hashlib
import hmac
import pprint
from urllib.parse import urlencode

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


class BitmexClient:

    def __init__(self, public_key: str, secret_key: str):
        self._api_public = public_key
        self._api_secret = secret_key
        self._base_url = "https://testnet.bitmex.com/api/v1"
        self._wss_url = "wss://ws.testnet.bitmex.com/realtime"
        self.connection_type = "Testnet"
        self.platform = "bitmex"

    def _generate_signature(self, data: typing.Dict) -> str:
        # TODO: Inspect and explore this method.
        return hmac.new(self._secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()

    def _make_request(self, method: str, endpoint: str, params: dict):

        try:
            if method == "GET":
                response = requests.get(url=self._base_url + endpoint, params=params)
            elif method == "POST":
                response = requests.post(url=self._base_url + endpoint, params=params)
            elif method == "DELETE":
                response = requests.delete(url=self._base_url + endpoint, params=params)
            else:
                raise ValueError("so far, only GET, POST and DELETE methods are coded.")
        except Exception as e:
            logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
            return None

        if response.status_code == 200:
            return response.json()

    def get_contracts(self) -> typing.List[Contract]:
        endpoint = "/instrument/active"
        contracts = []
        output = self._make_request("GET", endpoint, dict())

        for contract in output:
            symbol = contract['symbol']

            if _is_tradable(symbol, "USDT"):
                contracts.append(Contract(self.platform, contract))

        return contracts


    def get_balances(self):
        endpoint = "/wallet/assets"




if __name__ == "__main__":

    bitmex = BitmexClient(BITMEX_API_PUBLIC, BITMEX_API_SECRET)
    for each in bitmex.get_contracts():
        print(each.symbol)
