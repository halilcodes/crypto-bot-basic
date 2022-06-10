

# TODO: Make each class a "platform" parameter. defince a platform variable in each client's __init__ method.
# so tht each class should get the right info like that instead of try/except blocks.

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
        self.initial_margin = float(info['initialMargin'])
        self.maintenance_margin = float(info['maintMargin'])
        self.margin_balance = float(info['marginBalance'])
        self.wallet_balance = float(info['walletBalance'])
        self.unrealized_pnl = float(info['unrealizedProfit'])


class Candle:

    def __init__(self, candle_info) -> None:
        self.timestamp = candle_info[0]
        self.open = float(candle_info[1])
        self.high = float(candle_info[2])
        self.low = float(candle_info[3])
        self.close = float(candle_info[4])
        self.volume = float(candle_info[5])


class Contract:

    def __init__(self, platform, contract_info):
        if platform == "binance":
            self._get_binance_contracts(contract_info)
        elif platform == "bitmex":
            self._get_bitmex_contracts(contract_info)

    def _get_binance_contracts(self, contract_info):
        self.symbol = contract_info['symbol']   # ETHUSDT
        self.base_asset = contract_info['baseAsset']    # ETH
        self.quote_asset = contract_info['quoteAsset']  # USDT
        self.price_decimals = contract_info['pricePrecision']
        self.quantity_decimals = contract_info['quantityPrecision']

    def _get_bitmex_contracts(self, contract_info):
        self.symbol = contract_info['symbol']
        self.base_asset = contract_info['positionCurrency']
        self.quote_asset = contract_info['quoteCurrency']
        self.price_decimals = 0
        self.quantity_decimals = 0
        # TODO: figure out bitmex precision levels from its API


class OrderStatus:

    def __init__(self, order_info):
        self.order_id = order_info['orderId']
        self.status = order_info['status']
        self.avg_price = float(order_info['avgPrice'])