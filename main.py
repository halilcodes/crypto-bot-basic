from keys import *
import tkinter as tk
import logging
from connectors.bitmex import BitmexClient
from connectors.binance_futures import BinanceFuturesClient
import pprint
from logkeeper import log_keeper


if __name__ == "__main__":

    log_keeper("info.log")

    # binance = BinanceFuturesClient(BINANCE_TESTNET_API_PUBLIC, BINANCE_TESTNET_API_SECRET, True)
    bitmex_testnet = BitmexClient(BITMEX_API_PUBLIC, BITMEX_API_SECRET, True)
    # bitmex = BitmexClient(BITMEX_REAL_API_PUBILC, BITMEX_REAL_API_SECRET, False)

    window = tk.Tk()
    window.title("$$$🚀💵 MoneyMachine 💵🚀$$$")
    window.configure(bg='gray12')

    bitmex_testnet.get_historical_candles(bitmex_testnet.contracts['LINKUSDT'], "1h")

    window.mainloop()
