from keys import *
import tkinter as tk
import logging
from connectors.bitmex import get_bitmex_contracts
from connectors.binance_futures import BinanceFuturesClient


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler("info.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# logger.debug("This message is important only when debugging the program")
# logger.info("This message just shows basic information")
# logger.warning("This message is about something youshould pay attention to")
# logger.error("This message helps to debug an error that occured in your program")



if __name__ == "__main__":


    binance = BinanceFuturesClient(BINANCE_TESTNET_API_PUBLIC, BINANCE_TESTNET_API_SECRET, True)
    print(binance.get_balances())

    window = tk.Tk()
    window.title("$$$🚀💵 MoneyMachine 💵🚀$$$")
    window.configure(bg='gray12')




    window.mainloop()