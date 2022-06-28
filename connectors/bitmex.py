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
import websocket
from strategies import *
import dateutil.parser

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

        self.platform = "bitmex"

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.prices = dict()
        self._ws_id = 1
        self.ws: websocket.WebSocketApp
        self.reconnect = True

        self.logs = []

        # TODO: Instead of pointing out like that, can we say 'all child classes of Strategy class'?
        self.strategies: typing.Dict[int, typing.Union[TechnicalStrategy, BreakoutStrategy]] = dict()

        t = threading.Thread(target=self._start_ws)
        t.start()

        logger.info("Bitmex Client successfully initialized")

    def _add_log(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})

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
                if _is_tradable(symbol, "") and not symbol.startswith("."):
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
        data['reverse'] = True
        
        raw_candles = self._make_request(method="GET", endpoint=endpoint, params=data)
        
        candles = []
        
        if raw_candles is not None:
            for each in reversed(raw_candles):
                candles.append(Candle(self.platform, each, timeframe))

        return candles

    def place_order(self, contract: Contract, side: str, quantity: float,
                    order_type: str, price=None, tif=None) -> OrderStatus:
        """
        Args:
            contract:
            side:
            quantity: Limit order quantity of base asset. i.e: 100 of XBTUSD is 100 USD worth of XBT at set price.
                        This may be counter-intuitive and needs solving
            order_type:
            price:
            tif: default "GoodTillCancel"

        Returns:

        """
        # TODO: quantity parameter needs fine-tuning

        input_quantity = round(quantity / (contract.multiplier / 0.01), 8)
        print(input_quantity)


        print("we reached PLACE_ORDER bitmex")

        endpoint = "/order"
        method = "POST"
        data = dict()
        data['symbol'] = contract.symbol.upper()
        data['side'] = side.capitalize()
        data['orderQty'] = round(round(input_quantity / contract.lot_size) * contract.lot_size, 8)
        data['ordType'] = order_type.capitalize()
        if price is not None:
            data['price'] = round(price / contract.tick_size) * contract.tick_size
        if tif is not None:
            data['timeInForce'] = tif

        order_info = self._make_request(method=method, endpoint=endpoint, params=data)
        
        if order_info is not None:
            order_info = OrderStatus(self.platform, order_info)

        return order_info
        
    def get_order_status(self, contract: Contract, order_id: str) -> OrderStatus:
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

    def cancel_order(self, order_id: str) -> OrderStatus:
        endpoint = "/order"
        method = "DELETE"
        data = dict()
        data['orderID'] = order_id

        order_info = self._make_request(method=method, endpoint=endpoint, params=data)

        if order_info is not None:
            order_info = OrderStatus(self.platform, order_info[0])

        return order_info

    def get_current_open_orders(self):
        pass

    def get_bid_ask(self, contract: Contract):
        contract.symbol = contract.symbol.upper()
        endpoint = "/quote"
        method = "GET"
        data = dict()
        data['symbol'] = contract.symbol
        data['count'] = 1
        data['reverse'] = True

        bid_ask_info = self._make_request(method, endpoint, data)
        # pprint.pprint(bid_ask_info)
        if bid_ask_info is not None:
            return {'bid': bid_ask_info[0]['bidPrice'], 'ask': bid_ask_info[0]['askPrice']}
        else:
            return None

    def _start_ws(self):
        self.ws = websocket.WebSocketApp(self._wss_url,
                                         on_open=self._on_open, on_close=self._on_close,
                                         on_error=self._on_error, on_message=self._on_message)
        while True:
            try:
                if self.reconnect:
                    self.ws.run_forever()
                else:
                    break
            except Exception as e:
                logger.error("Bitmex error in run_forever() method: %s", e)
            time.sleep(2)

    def _on_open(self, ws):
        logger.info("Bitmex WebSocket connection opened.")

        self.subscribe_channel("instrument")
        self.subscribe_channel("trade")

    def _on_close(self, ws):
        logger.warning("Bitmex WebSocket connection closed.")

    def _on_error(self, ws, msg: str):
        logger.error("Bitmex WebSocket connection error: %s", msg)

    def _on_message(self, ws, msg: str):

        data = json.loads(msg)

        if "table" in data:
            if data['table'] == 'instrument':
                for d in data['data']:

                    symbol = d['symbol']
                    if symbol.startswith("."):
                        continue

                    if symbol not in self.prices:
                        self.prices[symbol] = {'bid': None, 'ask': None}

                    if 'bidPrice' in d:
                        self.prices[symbol]['bid'] = d['bidPrice']
                    if 'askPrice' in d:
                        self.prices[symbol]['ask'] = d['askPrice']

                    # PNL Calculation
                    try:
                        for b_index, strategy in self.strategies.items():
                            if strategy.contract.symbol == symbol:
                                for trade in strategy.trades:
                                    if trade.status == "open" and trade.entry_price is not None:
                                        if trade.side == "long":
                                            price = self.prices[symbol]['bid']
                                        else:
                                            price = self.prices[symbol]['ask']
                                        multiplier = trade.contract.multiplier
                                        if trade.contract.inverse:
                                            if trade.side == "long":
                                                trade.pnl = (1 / trade.entry_price - 1 / price) *\
                                                            trade.quantity * multiplier
                                            elif trade.side == "short":
                                                trade.pnl = (1 / price - 1 / trade.entry_price) *\
                                                            trade.quantity * multiplier

                                        else:
                                            if trade.side == "long":
                                                trade.pnl = (price - trade.entry_price) * trade.quantity * multiplier
                                            elif trade.side == "short":
                                                trade.pnl = (trade.entry_price - price) * trade.quantity * multiplier
                    except RuntimeError as e:
                        logger.error("Error while ooping through the Bitmex Strategies: %s", e)

            if data['table'] == 'trade':
                for d in data['data']:

                    symbol = d['symbol']
                    if symbol.startswith("."):
                        continue

                    ts = int(dateutil.parser.isoparse(d['timestamp']).timestamp() * 1000)

                    for key, strategy in self.strategies.items():

                        # print(f"we reached bitmex trade data for {strategy}")
                        print(symbol, strategy.contract.symbol)
                        if strategy.contract.symbol.lower() == symbol.lower():
                            print(f" matching strategy for {symbol} // bitmex.py")
                            res = strategy.parse_trades(float(d['price']), float(d['size']), ts)
                            strategy.check_trade(res)

    def subscribe_channel(self, topic: str):
        data = dict()
        data['op'] = "subscribe"
        data['args'] = []
        data['args'].append(topic)

        try:
            self.ws.send(json.dumps(data))
        except Exception as e:
            logger.error("Bitmex Websocket error while subscribing to %s: %s",topic, e)

        self._ws_id += 1

    # TODO: automated order gets error here with 'Invalid orderQty' response (error code 400) on .place_order() method.
    # orderQty must be greater than 100
    def get_trade_size(self, contract: Contract, price: float, balance_pct: float):
        balance = self.get_balances()
        if balance is not None:
            if 'XBt' in balance:
                balance = balance['XBt'].wallet_balance
            else:
                return None
        else:
            return None

        xbt_size = balance * balance_pct / 100

        # https://www.bitmex.com/app/perpetualContractsGuide
        # https://www.bitmex.com/app/futuresGuide
        if contract.inverse:
            contracts_number = xbt_size / (contract.multiplier / price)
        elif contract.quanto:
            contracts_number = xbt_size / (contract.multiplier * price)
        else:
            contracts_number = xbt_size / (contract.multiplier * price)

        logging.info("Bitmex current XBT balance =%s, contracts_number = %s", balance, contracts_number)

        return int(contracts_number)


if __name__ == "__main__":

    bitmex = BitmexClient(BITMEX_TESTNET_API_PUBLIC, BITMEX_TESTNET_API_SECRET, testnet=True)
    # bitmex = BitmexClient(BITMEX_REAL_API_PUBILC, BITMEX_REAL_API_SECRET, testnet=False)
    linkUsdt = bitmex.contracts['LINKUSDT']
    solUsdt = bitmex.contracts['SOLUSDT']
    xbtUsdt = bitmex.contracts['XBTUSDT']

    print("LINKUSDT: ")
    print("symbol: ", linkUsdt.symbol)
    print("base_asset: ", linkUsdt.base_asset)
    print("quote_asset: ", linkUsdt.quote_asset)
    print("tick_size: ", linkUsdt.tick_size)    # 0.001
    print("lot_size: ", linkUsdt.lot_size)
    print("price_decimals: ", linkUsdt.price_decimals)  # 3
    print("quantity_decimals: ", linkUsdt.quantity_decimals)
    print("quanto", linkUsdt.quanto)
    print("inverse", linkUsdt.inverse)
    print("multiplier", linkUsdt.multiplier)
    print("current bid/ask", bitmex.get_bid_ask(linkUsdt))
    link_ask = bitmex.get_bid_ask(linkUsdt)['ask']
    print("*" * 50)

    print("SOLSUDT: ")
    print("symbol: ", solUsdt.symbol)
    print("base_asset: ", solUsdt.base_asset)
    print("quote_asset: ", solUsdt.quote_asset)
    print("tick_size: ", solUsdt.tick_size)  # 0.01
    print("lot_size: ", solUsdt.lot_size)
    print("price_decimals: ", solUsdt.price_decimals)  # 2
    print("quantity_decimals: ", solUsdt.quantity_decimals)
    print("quanto", solUsdt.quanto)
    print("inverse", solUsdt.inverse)
    print("multiplier", solUsdt.multiplier)
    print("current bid/ask", bitmex.get_bid_ask(solUsdt))
    sol_ask = bitmex.get_bid_ask(solUsdt)['ask']
    print("*" * 50)

    print("XBTUSDT: ")
    print("symbol: ", xbtUsdt.symbol)
    print("base_asset: ", xbtUsdt.base_asset)
    print("quote_asset: ", xbtUsdt.quote_asset)
    print("tick_size: ", xbtUsdt.tick_size)  # 0.5
    print("lot_size: ", xbtUsdt.lot_size)
    print("price_decimals: ", xbtUsdt.price_decimals)  # 1
    print("quantity_decimals: ", xbtUsdt.quantity_decimals)
    print("quanto: ", xbtUsdt.quanto)
    print("inverse: ", xbtUsdt.inverse)
    print("multiplier: ", xbtUsdt.multiplier)
    print("current bid/ask", bitmex.get_bid_ask(xbtUsdt))
    xbt_ask = bitmex.get_bid_ask(xbtUsdt)['ask']
    print("*" * 50)

    # bitmex.place_order(xbtUsdt, "buy", 1000, "market")  # size: 0.001 XBT
    # bitmex.place_order(xbtUsdt, "buy", 10000, "market")  # size: 0.01 XBT

    # bitmex.place_order(solUsdt, "buy", 0.1, "market")  # size: 0.1 SOL
    # bitmex.place_order(solUsdt, "buy", 0.11, "market")  # size: 0.1 SOL

    # bitmex.place_order(linkUsdt, "buy", 1, "market")  # size: 1 link
    # bitmex.place_order(linkUsdt, "buy", 1.1, "market")  # size: 1 link

    # bitmex.place_order(solUsdt, "buy", 12, "limit", price=20.513218)    # 12 sol @20.51 usdt
    # bitmex.place_order(linkUsdt, "buy", 12, "limit", price=2.513218)    # 12 link @2.513 usdt

