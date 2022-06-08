from pickle import NONE
import requests
import pprint
import json
import logging

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


class BinanceFuturesClient:

    def __init__(self, testnet: bool) -> None:
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
            self.connection_type = "Testnet"
        else:
            self.base_url = "https://fapi.binance.com"
            self.connection_type = "Real Account"

        self.prices = dict()
        
        logger.info(f"Binance Futures Client {self.connection_type} successfully initialized")

    def make_requests(self, method, endpoint, parameters):
        if method =="GET":
            response = requests.get(self.base_url + endpoint, params=parameters)
        else:
            raise ValueError("so far, only GET method is coded.")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
             method, endpoint, response.json(), response.status_code)
            return None

    def get_contracts(self):
        exchange_info = self.make_requests("GET", "/fapi/v1/exchangeInfo", None)
        # contracts = dict()
        if exchange_info is not None:
            # for contract_data in exchange_info['symbols']:
            #     contracts[contract_data['pair']] = contract_data
            contracts = {contract_data['pair']: contract_data for contract_data in exchange_info['symbols']}
            return contracts

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

        return candles

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

    

if __name__ == "__main__":
    binanceTestnet = BinanceFuturesClient(testnet=True)

