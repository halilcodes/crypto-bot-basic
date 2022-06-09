from keys import *
import tkinter as tk
import logging
from connectors.bitmex import get_bitmex_contracts
from connectors.binance_futures import BinanceFuturesClient
import pprint
from logkeeper import log_keeper


if __name__ == "__main__":

    log_keeper("info.log")
    
    binance = BinanceFuturesClient(BINANCE_TESTNET_API_PUBLIC, BINANCE_TESTNET_API_SECRET, True)
    pprint.pprint(binance.get_balances())

    window = tk.Tk()
    window.title("$$$🚀💵 MoneyMachine 💵🚀$$$")
    window.configure(bg='gray12')




    window.mainloop()