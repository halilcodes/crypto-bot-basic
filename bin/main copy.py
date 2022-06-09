from connectors.keys import *
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

    bitmex_contracts = get_bitmex_contracts()

    binance = BinanceFuturesClient(True)

    window = tk.Tk()
    window.title("$$$🚀💵 MoneyMachine 💵🚀$$$")
    window.configure(bg='gray12')

    i = 0
    j = 0
    calibri_font = ('Calibri', 11, 'normal')

    for contract in bitmex_contracts:
        label_widget = tk.Label(window, text=contract, bg='gray12',fg='SteelBlue1', relief=tk.SOLID, width=15, font=calibri_font)
        label_widget.grid(row=i, column=j, sticky='ew')

        if i == 4:
            j += 1
            i = 0
        else:
            i += 1



    window.mainloop()