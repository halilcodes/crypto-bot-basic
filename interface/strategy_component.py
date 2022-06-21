import tkinter as tk

from interface.styling import *
from connectors.bitmex import BitmexClient
from connectors.binance_futures import BinanceFuturesClient
from strategies import *
from utils import *


class StrategyEditor(tk.Frame):
    def __init__(self, root, binance: BinanceFuturesClient, bitmex: BitmexClient, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.root = root

        self._valid_integer = self.register(check_integer_format)
        self._valid_float = self.register(check_float_format)

        self._exchanges = {"Binance": binance, "Bitmex": bitmex}

        self._all_contracts = ["BTCUSDT", "ETHUSDT"]
        self._all_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h"]

        for exchange, client in self._exchanges.items():
            for symbol, contract in client.contracts.items():
                self._all_contracts.append(symbol + "_" + exchange.capitalize())

        self._commands_frame = tk.Frame(self, bg=BG_COLOR)
        self._commands_frame.pack(side=tk.TOP)

        self._add_button = tk.Button(self._commands_frame, text="Add Strategy", font=GLOBAL_FONT,
                                     command=self._add_strategy_row, bg=BG_COLOR_2, fg=FG_COLOR)
        self._add_button.pack(side=tk.TOP)

        self._table_frame = tk.Frame(self._commands_frame, bg=BG_COLOR)
        self._table_frame.pack(side=tk.TOP)

        self.body_widgets = dict()

        self._headers = ["Strategy", "Contract", "Timeframe", "Balance %", "TP %", "SL %"]

        self._additional_parameters = dict()
        # _extra_input is specific for each popup, so the code does not store for extra inputs for each strategy
        # but it does not seem right
        self._extra_input = dict()

        for idx, h in enumerate(self._headers):
            header = tk.Label(self._table_frame, text=h, bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
            header.grid(row=0, column=idx)

        self._base_params = [
            {"code_name": "strategy_type", "widget": tk.OptionMenu,
             "data_type": str, "values": ["Technical", "Breakout"], "width": 10},

            {"code_name": "contract", "widget": tk.OptionMenu,
             "data_type": str, "values": self._all_contracts, "width": 15},

            {"code_name": "timeframe", "widget": tk.OptionMenu,
             "data_type": str, "values": self._all_timeframes, "width": 7},

            {"code_name": "balance_pct", "widget": tk.Entry, "data_type": float, "width": 7},
            {"code_name": "take_profit", "widget": tk.Entry, "data_type": float, "width": 7},
            {"code_name": "stop_loss", "widget": tk.Entry, "data_type": float, "width": 7},
            {"code_name": "parameters", "widget": tk.Button, "data_type": float, "text": "Parameters",
             "bg": BG_COLOR_2, "command": self._show_popup},

            {"code_name": "activation", "widget": tk.Button, "text": "OFF", "data_type": float,
             "bg": "darkred", "command": self._switch_strategy},

            {"code_name": "delete", "widget": tk.Button, "text": "X", "data_type": float,
             "bg": "darkred", "command": self._delete_row}
        ]

        self._extra_params = {
            "Technical": [
                {"code_name": "rsi_length", "name": "RSI Periods", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_fast", "name": "MACD Fast Length", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_slow", "name": "MACD Slow Length", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_signal", "name": "MACD Signal Length", "widget": tk.Entry, "data_type": int}
            ],
            "Breakout": [
                {"code_name": "min_volume", "name": "Minimum Volume", "widget": tk.Entry, "data_type": float}
            ]
        }

        for h in self._base_params:
            self.body_widgets[h['code_name']] = dict()
            if h['widget'] == tk.OptionMenu:
                self.body_widgets[h['code_name'] + "_var"] = dict()

        self._body_index = 1

    def _add_strategy_row(self):
        b_index = self._body_index

        for col, base_param in enumerate(self._base_params):
            code_name = base_param['code_name']
            if base_param['widget'] == tk.OptionMenu:
                self.body_widgets[code_name + "_var"][b_index] = tk.StringVar()
                self.body_widgets[code_name + "_var"][b_index].set(base_param['values'][0])
                self.body_widgets[code_name][b_index] = tk.OptionMenu(self._table_frame,
                                                                      self.body_widgets[code_name + "_var"][b_index],
                                                                      *base_param['values'])
                self.body_widgets[code_name][b_index].config(width=base_param['width'])

            elif base_param['widget'] == tk.Entry:
                self.body_widgets[code_name][b_index] = tk.Entry(self._table_frame, justify=tk.CENTER)

                # invalid key catcher
                if base_param['data_type'] == int:
                    self.body_widgets[code_name][b_index].config(validate='key',
                                                                 validatecommand=(self._valid_integer, "%P"))
                if base_param['data_type'] == float:
                    self.body_widgets[code_name][b_index].config(validate='key',
                                                                 validatecommand=(self._valid_float, "%P"))

            elif base_param['widget'] == tk.Button:
                self.body_widgets[code_name][b_index] = tk.Button(self._table_frame,
                                                                  text=base_param['text'], bg=base_param['bg'],
                                                                  fg=FG_COLOR,
                                                                  command=lambda frozen_command=base_param['command']:
                                                                  frozen_command(b_index))
                # TODO: check lambda function mote detailed
            else:
                continue

            self.body_widgets[code_name][b_index].grid(row=b_index, column=col)

        self._additional_parameters[b_index] = dict()

        for strat, params in self._extra_params.items():
            for param in params:
                self._additional_parameters[b_index][param['code_name']] = None

        self._body_index += 1

    def _delete_row(self, b_index: int):
        
        for element in self._base_params:
            self.body_widgets[element['code_name']][b_index].grid_forget()

            del self.body_widgets[element['code_name']][b_index]
        del self._additional_parameters[b_index]
        # pprint.pprint(self._additional_parameters)
        # print(f"b_index = {b_index}")
        # print("*" * 50)

    def _show_popup(self, b_index: int):
        x = self.body_widgets["parameters"][b_index].winfo_rootx()
        y = self.body_widgets["parameters"][b_index].winfo_rooty()

        self._popup_window = tk.Toplevel(self)
        self._popup_window.wm_title("Parameters")
        self._popup_window.config(bg=BG_COLOR)
        self._popup_window.attributes("-topmost", "true")
        self._popup_window.grab_set()

        self._popup_window.geometry(f"+{x - 80}+{y + 30}")

        strategy_selected = self.body_widgets['strategy_type_var'][b_index].get()
        # TODO: I don't get it!

        row_num = 0
        for param in self._extra_params[strategy_selected]:
            code_name = param['code_name']

            temp_label = tk.Label(self._popup_window, bg=BG_COLOR, fg=FG_COLOR, text=param['name'], font=BOLD_FONT)
            temp_label.grid(row=row_num, column=0)

            if param['widget'] == tk.Entry:
                self._extra_input[code_name] = tk.Entry(self._popup_window, bg=BG_COLOR_2, justify=tk.CENTER,
                                                        fg=FG_COLOR, insertbackground=FG_COLOR)
                # invalid key catcher
                if param['data_type'] == int:
                    self._extra_input[code_name].config(validate='key', validatecommand=(self._valid_integer, "%P"))
                if param['data_type'] == float:
                    self._extra_input[code_name].config(validate='key', validatecommand=(self._valid_float, "%P"))

                if self._additional_parameters[b_index][code_name] is not None:
                    self._extra_input[code_name].insert(0, str(self._additional_parameters[b_index][code_name]))
            else:
                continue

            self._extra_input[code_name].grid(row=row_num, column=1)

            row_num += 1

        # Validation button

        validation_button = tk.Button(self._popup_window, text="Validate", bg=BG_COLOR_2, fg=FG_COLOR,
                                      command=lambda: self._validate_parameters(b_index))
        validation_button.grid(row=row_num, column=0, columnspan=2)

    def _validate_parameters(self, b_index: int):
        strategy_selected = self.body_widgets['strategy_type_var'][b_index].get()

        for param in self._extra_params[strategy_selected]:
            code_name = param['code_name']

            if self._extra_input[code_name].get() == "":
                self._additional_parameters[b_index][code_name] = None
            else:
                self._additional_parameters[b_index][code_name] = param['data_type'](self._extra_input[code_name].get())

        self._popup_window.destroy()

    def _switch_strategy(self, b_index: int):

        for param in ["balance_pct", "take_profit", "stop_loss"]:
            if self.body_widgets[param][b_index].get() == "":
                self.root.logging_frame.add_log(f"Missing {param} parameter")
                return

        strategy_selected = self.body_widgets['strategy_type_var'][b_index].get()

        for param in self._extra_params[strategy_selected]:
            code_name = param['code_name']
            if self._additional_parameters[b_index][code_name] is None:
                self.root.logging_frame.add_log(f"Missing {code_name} parameter")
                return

        contract_name = self.body_widgets['contract_var'][b_index].get()   # "ADAUSDT_Binance"
        symbol = contract_name.split("_")[0]
        print(symbol, " //strategy_component.py")
        exchange = contract_name.split("_")[1]
        timeframe = self.body_widgets['timeframe_var'][b_index].get()
        contract = self._exchanges[exchange].contracts[symbol]

        balance_pct = float(self.body_widgets['balance_pct'][b_index].get())
        take_profit = float(self.body_widgets['take_profit'][b_index].get())
        stop_loss = float(self.body_widgets['stop_loss'][b_index].get())

        if self.body_widgets['activation'][b_index].cget('text') == "OFF":  # .cget() gets the text written in the ui
            # create a new_strategy Object for selected strategy
            # disable changes in the running strategy, change off button config and add log entry
            if strategy_selected == "Technical":
                new_strategy = TechnicalStrategy(self._exchanges[exchange], contract, exchange,
                                                 timeframe, balance_pct, take_profit,
                                                 stop_loss, self._additional_parameters[b_index])

            elif strategy_selected == "Breakout":
                new_strategy = BreakoutStrategy(self._exchanges[exchange], contract, exchange,
                                                timeframe, balance_pct, take_profit,
                                                stop_loss, self._additional_parameters[b_index])
                print(f"{strategy_selected} chosen on {exchange} for {contract.symbol}// strategy_component.py")

            else:
                return
            
            new_strategy.candles = self._exchanges[exchange].get_historical_candles(contract, timeframe)

            if len(new_strategy.candles) == 0:
                self.root.logging_frame.add_log(f"No historical data retrieved for {contract.symbol}.")
                return

            # When its added to the client on_open function, it closes because it quickly reaches subscription limit
            # of 200. This way, we only subscribe for entered symbols
            if exchange.lower() == "binance":
                print("exchange is binance // strategy_component.py")
                self._exchanges[exchange].subscribe_channel([contract], "aggTrade")

            # here we add the started strategy to its client object.so, when client is run, websocket runs the
            # strategy immediately
            self._exchanges[exchange].strategies[b_index] = new_strategy
            print(self._exchanges["Bitmex"].strategies)

            for param in self._base_params:
                code_name = param['code_name']

                if code_name != "activation" and "_var" not in code_name:
                    self.body_widgets[code_name][b_index].config(state=tk.DISABLED)

            self.body_widgets['activation'][b_index].config(bg="darkgreen", text="ON")
            self.root.logging_frame.add_log(f"{strategy_selected} strategy on {symbol} / {timeframe} started.")

        else:

            del self._exchanges[exchange].strategies[b_index]

            # enable changes in the running strategy, change on button config and add log entry
            for param in self._base_params:
                code_name = param['code_name']

                if code_name != "activation" and "_var" not in code_name:
                    self.body_widgets[code_name][b_index].config(state=tk.NORMAL)

            self.body_widgets['activation'][b_index].config(bg="darkred", text="OFF")
            self.root.logging_frame.add_log(f"{strategy_selected} strategy on {symbol} / {timeframe} /"
                                            f"on {exchange} stopped.")
