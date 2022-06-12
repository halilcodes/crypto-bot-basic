

# TODO: Make each class a "platform" parameter. defince a platform variable in each client's __init__ method.
# so tht each class should get the right info like that instead of try/except blocks.

BITMEX_MULTIPLIER = 0.00000001


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

    def __init__(self, platform, candle_info) -> None:
        self.candle_info = candle_info
        self.platform = platform
        if self.platform == "binance":
            self._get_binance_candles()
        elif self.platform == "bitmex":
            self._get_bitmex_candles()

    def _get_binance_candles(self):
        self.timestamp = self.candle_info[0]
        self.open = float(self.candle_info[1])
        self.high = float(self.candle_info[2])
        self.low = float(self.candle_info[3])
        self.close = float(self.candle_info[4])
        self.volume = float(self.candle_info[5])

    def _get_bitmex_candles(self):
        self.timestamp = self.candle_info["timestamp"]
        self.open = self.candle_info["open"]
        self.high = self.candle_info["high"]
        self.low = self.candle_info["low"]
        self.close = self.candle_info["close"]
        self.volume = self.candle_info["volume"]


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

    def _get_bitmex_contracts(self):
        self.symbol = self.contract_info['symbol']
        self.base_asset = self.contract_info['rootSymbol']
        self.quote_asset = self.contract_info['quoteCurrency']
        self.price_decimals = self.contract_info['tickSize']
        self.quantity_decimals = self.contract_info['lotSize']
        # TODO: figure out bitmex precision levels from its API


class OrderStatus:

    def __init__(self, platform, order_info):
        self.platform = platform
        self.order_info = order_info
        if self.platform == "binance":
            self._get_binance_order_status()
        elif self.platform == "bitmex":
            self._get_bitmex_order_status()

    def _get_binance_order_status(self):
        self.order_id = self.order_info['orderId']
        self.status = self.order_info['status']
        self.avg_price = float(self.order_info['avgPrice'])

    def _get_bitmex_order_status(self):
        self.order_id = self.order_info['orderID']
        self.status = self.order_info['ordStatus']
        self.avg_price = self.order_info['avgPx']