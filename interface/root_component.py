"""
COMPONENTS=
- Watchlist
- Logging
- Strategies
-Trades
"""
import logging
import tkinter as tk
from interface.styling import *
from interface.logging_component import Logging
from connectors.bitmex import BitmexClient
from connectors.binance_futures import BinanceFuturesClient
from interface.watchlist_component import WatchList
from interface.trades_component import TradesWatch
from interface.strategy_component import StrategyEditor

logger = logging.getLogger()


class Root(tk.Tk):
    def __init__(self, binance: BinanceFuturesClient, bitmex: BitmexClient):
        super().__init__()

        self.binance = binance
        self.bitmex = bitmex

        self.title("$$$🚀💵 MoneyMachine v1.0 💵🚀$$$")
        self.configure(bg=BG_COLOR)

        self._left_frame = tk.Frame(self, bg=BG_COLOR)
        self._left_frame.pack(side=tk.LEFT)

        self._right_frame = tk.Frame(self, bg=BG_COLOR)
        self._right_frame.pack(side=tk.RIGHT)

        self._watchlist_frame = WatchList(self.binance.contracts, self.bitmex.contracts,
                                          self._left_frame, bg=BG_COLOR)
        self._watchlist_frame.pack(side=tk.TOP)

        self.logging_frame = Logging(self._left_frame, bg=BG_COLOR)
        self.logging_frame.pack(side=tk.TOP)

        self._strategy_frame = StrategyEditor(self, self.binance, self.bitmex, self._right_frame, bg=BG_COLOR)
        self._strategy_frame.pack(side=tk.TOP)

        self._trades_frame = TradesWatch(self.binance, self.bitmex, self._right_frame, bg=BG_COLOR)
        self._trades_frame.pack(side=tk.TOP)

        self._update_ui()

    def _update_ui(self):

        # Logs

        for log in self.bitmex.logs:
            if not log["displayed"]:
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True

        for log in self.binance.logs:
            if not log["displayed"]:
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True

        # Trades and Logs

        for client in [self.binance, self.bitmex]:
            try:

                for b_index, strategy in client.strategies.items():
                    for log in strategy.logs:
                        if not log['displayed']:
                            self.logging_frame.add_log(log['log'])
                            log['displayed'] = True

                    for trade in strategy.trades:
                        if trade.time not in self._trades_frame.body_widgets['symbol']:  # we can select any column
                            self._trades_frame.add_trade(trade)

                        if trade.contract.platform == "binance":
                            precision_pnl = trade.contract.price_decimals
                        else:
                            precision_pnl = 8   # pnl will always be in xbt for bitmex (??)

                        pnl_str = "{0:.{prec}f}".format(trade.pnl, prec=precision_pnl)
                        self._trades_frame.body_widgets['pnl_var'][trade.time].set(pnl_str)
                        self._trades_frame.body_widgets['status_var'][trade.time].set(trade.status.capitalize())

            except RuntimeError as e:
                logger.error("RuntimeError while looping through strategies dictionary: %s", e)

        # Watchlist Prices

        try:
            for key, value in self._watchlist_frame.body_widgets['symbol'].items():
                symbol = self._watchlist_frame.body_widgets['symbol'][key].cget('text')
                exchange = self._watchlist_frame.body_widgets['exchange'][key].cget('text')

                if exchange == "Binance":

                    self.binance.subscribe_channel([self.binance.contracts[symbol]], "aggTrade")

                    if symbol not in self.binance.contracts:
                        continue
                    if symbol not in self.binance.prices:
                        try:
                            self.binance.get_bid_ask(self.binance.contracts)
                        except AttributeError as e:
                            # This try-except catches exception where in the first couple minutes of running,
                            # websockets might not get all bid/asks so UI gets Attribute error for contract.symbol
                            # entered to the watchlist
                            logger.error("AttributeError while getting bid/asks for a symbol: %s", e)
                            # t = threading.Thread(target=self.binance._start_ws)
                            # t.start()
                            # TODO: Sometimes Binance Websocket does not connect for 1-2 minutes,
                            # I need to be sure not to take action before connection established or
                            # retry connection like commented 2 lines above (?)
                            # Above 2 lines work, it forces a new websocket and eventually we get a
                            # connection. Still needs manual handling though
                            # EUREKA!: Create sample contract object with missing symbol, get_bid_ask() and add
                            # that to binance.contracts in the exception code-block
                            continue
                    precision = self.binance.contracts[symbol].price_decimals
                    prices = self.binance.prices[symbol]

                elif exchange == "Bitmex":
                    if symbol not in self.bitmex.contracts:
                        continue
                    if symbol not in self.bitmex.prices:
                        continue
                    precision = self.bitmex.contracts[symbol].price_decimals
                    prices = self.bitmex.prices[symbol]
                else:
                    continue

                if prices['bid'] is not None:
                    price_str = "{0:.{prec}f}".format(prices['bid'], prec=precision)
                    self._watchlist_frame.body_widgets['bid_var'][key].set(price_str)
                if prices['ask'] is not None:
                    price_str = "{0:.{prec}f}".format(prices['ask'], prec=precision)
                    self._watchlist_frame.body_widgets['ask_var'][key].set(price_str)
        except RuntimeError as e:
            logger.error("RuntimeError while looping through watchlist dictionary: %s", e)

        self.after(1500, self._update_ui)
