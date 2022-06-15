"""
COMPONENTS=
- Watchlist
- Logging
- Strategies
-Trades
"""
import time
import tkinter as tk
from interface.styling import *
from interface.logging_component import Logging
from connectors.bitmex import BitmexClient
from connectors.binance_futures import BinanceFuturesClient
from interface.watchlist_component import WatchList


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

        self._logging_frame = Logging(self._left_frame, bg=BG_COLOR)
        self._logging_frame.pack(side=tk.TOP)

        self._update_ui()

    def _update_ui(self):

        # Logs

        for log in self.bitmex.logs:
            if not log["displayed"]:
                self._logging_frame.add_log(log['log'])
                log['displayed'] = True

        for log in self.binance.logs:
            if not log["displayed"]:
                self._logging_frame.add_log(log['log'])
                log['displayed'] = True

        # Watchlist Prices

        for key, value in self._watchlist_frame.body_widgets['Symbol'].items():
            symbol = self._watchlist_frame.body_widgets['Symbol'][key].cget('text')
            exchange = self._watchlist_frame.body_widgets['Exchange'][key].cget('text')

            if exchange == "Binance":
                if symbol not in self.binance.contracts:
                    continue
                if symbol not in self.binance.prices:
                    continue
                
        self.after(1500, self._update_ui)
