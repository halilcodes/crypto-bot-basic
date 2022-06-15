import tkinter as tk
from interface.styling import *
import typing
from models import *
from connectors.bitmex import BitmexClient
from connectors.binance_futures import BinanceFuturesClient


class TradesWatch(tk.Frame):
    def __init__(self, binance: BinanceFuturesClient, bitmex: BitmexClient, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._table_frame = tk.Frame(self, bg=BG_COLOR)
        self._table_frame.pack(side=tk.TOP)

        self._headers = ["Time", "Symbol", "Exchange", "Strategy", "Side", "Quantity", "Status", "Pnl"]
        self._body_index = 1
        self.body_widgets = dict()

        for idx, h in enumerate(self._headers):
            header = tk.Label(self._table_frame, text=h.capitalize(),
                              bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
            header.grid(row=0, column=idx)

        for h in self._headers:
            self.body_widgets[h] = dict()
            if h in ["Status", "Pnl"]:
                self.body_widgets[h + "_var"] = dict()

    def _add_trade(self, order_status: OrderStatus):
        exchange = order_status.platform


