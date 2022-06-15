from keys import *
import tkinter as tk
import logging
from connectors.bitmex import BitmexClient
from connectors.binance_futures import BinanceFuturesClient
import pprint
from logkeeper import log_keeper
from interface.root_component import Root

if __name__ == "__main__":

    log_keeper("info.log")
    binance = BinanceFuturesClient(BINANCE_TESTNET_API_PUBLIC, BINANCE_TESTNET_API_SECRET, True)
    bitmex = BitmexClient(BITMEX_TESTNET_API_PUBLIC, BITMEX_TESTNET_API_SECRET, True)

    root = Root(binance, bitmex)

    root.mainloop()
