import dateutil.parser
import datetime
# TODO: Make each class a "platform" parameter. defince a platform variable in each client's __init__ method.
# so tht each class should get the right info like that instead of try/except blocks.

BITMEX_MULTIPLIER = 0.00000001
BITMEX_TF_MINUTES = {"1m": 1, "5m": 5, "1h": 60, "1d": 1440}
# available options: [1m,5m,1h,1d]


class Balance:

    """
    This class gets the output of binance's /fapi/v1/account in .json format as an input
    and organizes it

    Parameters:
    info: dict (json) format of binance account information request's response

    Caution: each asset should be passed separately
            (preferably by passing the account info through a for loop)
    """
    def __init__(self, platform, info) -> None:
        self.info = info
        self.platform = platform
        if self.platform == "binance":
            self._get_binance_balance()
        elif self.platform == "bitmex":
            self._get_bitmex_balance()

    def _get_binance_balance(self):
        self.initial_margin = float(self.info['initialMargin'])
        self.maintenance_margin = float(self.info['maintMargin'])
        self.margin_balance = float(self.info['marginBalance'])
        self.wallet_balance = float(self.info['walletBalance'])
        self.unrealized_pnl = float(self.info['unrealizedProfit'])

    def _get_bitmex_balance(self):
        self.initial_margin = self.info['initMargin'] * BITMEX_MULTIPLIER
        self.maintenance_margin = self.info['maintMargin'] * BITMEX_MULTIPLIER
        self.margin_balance = self.info['marginBalance'] * BITMEX_MULTIPLIER
        self.wallet_balance = self.info['walletBalance'] * BITMEX_MULTIPLIER
        self.unrealized_pnl = self.info['unrealisedPnl'] * BITMEX_MULTIPLIER


class Candle:

    def __init__(self, platform, candle_info, timeframe: str) -> None:
        self.candle_info = candle_info
        self.platform = platform
        self.timeframe = timeframe
        if self.platform == "binance":
            self._get_binance_candles()
        elif self.platform == "bitmex":
            self._get_bitmex_candles()
        elif self.platform == "parse_trade":
            self._get_parse_trade_candles()

    def _get_binance_candles(self):
        self.timestamp = self.candle_info[0]
        self.open = float(self.candle_info[1])
        self.high = float(self.candle_info[2])
        self.low = float(self.candle_info[3])
        self.close = float(self.candle_info[4])
        self.volume = float(self.candle_info[5])

    def _get_bitmex_candles(self):
        """ timestamp in Bitmex are the END of the period and in string format"""
        str_time = dateutil.parser.isoparse(self.candle_info["timestamp"])
        str_time = str_time - datetime.timedelta(minutes=BITMEX_TF_MINUTES[self.timeframe])
        self.timestamp = int(str_time.timestamp() * 1000)
        # print(self.candle_info["timestamp"], str_time, self.timestamp)
        self.open = self.candle_info["open"]
        self.high = self.candle_info["high"]
        self.low = self.candle_info["low"]
        self.close = self.candle_info["close"]
        self.volume = self.candle_info["volume"]

    def _get_parse_trade_candles(self):
        self.timestamp = self.candle_info['ts']
        self.open = self.candle_info["open"]
        self.high = self.candle_info["high"]
        self.low = self.candle_info["low"]
        self.close = self.candle_info["close"]
        self.volume = self.candle_info["volume"]


def tick_to_decimals(tick_size: float) -> int:
    tick_size_str = "{0:.8f}".format(tick_size)
    # 0.000010000
    while tick_size_str[-1] == "0":
        tick_size_str = tick_size_str[:-1]

    split_tick = tick_size_str.split(".")

    if len(split_tick) > 1:
        return len(split_tick[1])
    else:
        return 0


class Contract:

    def __init__(self, platform, contract_info):
        self.contract_info = contract_info
        self.platform = platform
        if self.platform == "binance":
            self._get_binance_contracts()
        elif self.platform == "bitmex":
            self._get_bitmex_contracts()

    def _get_binance_contracts(self):
        self.symbol = self.contract_info['symbol']   # ETHUSDT
        self.base_asset = self.contract_info['baseAsset']    # ETH
        self.quote_asset = self.contract_info['quoteAsset']  # USDT
        self.price_decimals = self.contract_info['pricePrecision']
        self.quantity_decimals = self.contract_info['quantityPrecision']
        self.tick_size = 1 / pow(10, self.price_decimals)
        self.lot_size = 1 / pow(10, self.quantity_decimals)

    def _get_bitmex_contracts(self):
        self.symbol = self.contract_info['symbol']
        self.base_asset = self.contract_info['rootSymbol']
        self.quote_asset = self.contract_info['quoteCurrency']
        self.tick_size = self.contract_info['tickSize']
        self.lot_size = self.contract_info['lotSize']
        self.price_decimals = tick_to_decimals(self.tick_size)
        self.quantity_decimals = tick_to_decimals(self.lot_size)

        self.quanto = self.contract_info['isQuanto']
        self.inverse = self.contract_info['isInverse']
        self.multiplier = self.contract_info['multiplier'] * BITMEX_MULTIPLIER

        if self.inverse:
            self.multiplier *= -1


class OrderStatus:
    #   TODO: this class should hold a lot more data ie symbol, time, leverage etc.
    def __init__(self, platform, order_info):
        self.platform = platform
        self.order_info = order_info
        if self.platform == "binance":
            self._get_binance_order_status()
        elif self.platform == "bitmex":
            self._get_bitmex_order_status()

    def _get_binance_order_status(self):
        self.order_id = self.order_info['orderId']
        self.status = self.order_info['status'].lower()
        self.avg_price = float(self.order_info['avgPrice'])

    def _get_bitmex_order_status(self):
        self.order_id = self.order_info['orderID']
        self.status = self.order_info['ordStatus'].lower()
        self.avg_price = self.order_info['avgPx']


class Trade:
    def __init__(self, trade_info):
        self.time: int = trade_info['time']
        self.contract: Contract = trade_info['contract']
        self.strategy: str = trade_info['strategy']
        self.side: str = trade_info['side']
        self.entry_price: float = trade_info['entry_price']
        self.status: str = trade_info['status']
        self.pnl: float = trade_info['pnl']
        self.quantity = trade_info['quantity']
        self.entry_id = trade_info['entry_id']
