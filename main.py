from keys import *
import tkinter as tk
import logging
from connectors.bitmex import BitmexClient
from connectors.binance_futures import BinanceFuturesClient
import pprint
from logkeeper import log_keeper


if __name__ == "__main__":

    log_keeper("info.log")

    binance = BinanceFuturesClient(BINANCE_TESTNET_API_PUBLIC, BINANCE_TESTNET_API_SECRET, True)
    bitmex = BitmexClient(BITMEX_TESTNET_API_PUBLIC, BITMEX_TESTNET_API_SECRET, True)

    window = tk.Tk()
    window.title("$$$🚀💵 MoneyMachine 💵🚀$$$")
    window.configure(bg='gray12')

    # print(bitmex.place_order(bitmex.contracts['LINKUSD'], "buy", 50, "Limit", 2).order_id)
    print(bitmex.cancel_order("03713aaf-458c-48c8-b7b0-fb307a29f194"))

    window.mainloop()
