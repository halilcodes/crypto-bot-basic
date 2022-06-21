import logging
import time
from threading import Timer
from models import *
import typing
import pandas as pd

logger = logging.getLogger()
TF_EQUIV = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400}

if typing.TYPE_CHECKING:
    from connectors.bitmex import BitmexClient
    from connectors.binance_futures import BinanceFuturesClient


class Strategy:
    def __init__(self, client: typing.Union["BitmexClient", "BinanceFuturesClient"],
                 contract: Contract, exchange: str, timeframe: str, balance_pct: float,
                 take_profit: float, stop_loss: float, strategy_name: str):

        self.client = client
        self.contract = contract
        self.exchange = exchange
        self.tf = timeframe
        self.tf_equiv = TF_EQUIV[timeframe] * 1000
        self.balance_pct = balance_pct
        self.take_profit = take_profit
        self.stop_loss = stop_loss

        self.strategy_name = strategy_name

        self.ongoing_position = False

        self.candles: typing.List[Candle] = []
        self.trades: typing.List[Trade] = []
        self.logs = []

    def _add_log(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})

    def parse_trades(self, price: float, size: float, timestamp: int):

        timestamp_diff = int(time.time() * 1000) - timestamp
        if timestamp_diff >= 2000:
            logger.warning("%s %s: %s milliseconds of difference between computer time and exchange time",
                           self.exchange, self.contract.symbol, timestamp_diff)

        last_candle = self.candles[-1]

        # Same Candle
        if timestamp < last_candle.timestamp + self.tf_equiv:
            last_candle.close = price
            last_candle.volume += size

            if price > last_candle.high:
                last_candle.high = price
            elif price < last_candle.low:
                last_candle.low = price

            # Check Exit Conditions
            for trade in self.trades:
                if trade.status == "open" and trade.entry_price is not None:
                    self._check_tp_sl(trade)

            return "same_candle"

        # Missing Candle(s)
        elif timestamp >= last_candle.timestamp + 2 * self.tf_equiv:

            missing_candles = int((timestamp - last_candle.timestamp) / self.tf_equiv) - 1

            logger.info("%s missing %s candles for %s %s (%s %s)",
                        self.exchange, missing_candles, self.contract.symbol, self.tf, timestamp, last_candle.timestamp)

            for missing in range(missing_candles):
                new_ts = last_candle.timestamp + self.tf_equiv
                candle_info = {'ts': new_ts, 'open': last_candle.close,
                               'high': last_candle.close, 'low': last_candle.close,
                               'close': last_candle.close, 'volume': 0}

                new_candle = Candle('parse_trade', candle_info, self.tf)
                self.candles.append(new_candle)

                last_candle = new_candle

            # new_ts = last_candle.timestamp + self.tf_equiv
            # candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': size}
            # new_candle = Candle('parse_trade', candle_info, self.tf)
            # self.candles.append(new_candle)
            return "new_candle"

        # New Candle
        elif timestamp >= last_candle.timestamp + self.tf_equiv:
            new_ts = last_candle.timestamp + self.tf_equiv
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': size}
            new_candle = Candle('parse_trade', candle_info, self.tf)
            
            self.candles.append(new_candle)
            
            logger.info("%s New candle for %s %s", self.exchange, self.contract.symbol, self.tf)

            return "new_candle"

    def _check_order_status(self, order_id):
        order_status = self.client.get_order_status(self.contract, order_id)

        if order_status is not None:
            logger.info("%s order status: %s", self.exchange, order_status.status)

            if order_status.status == "filled":
                for trade in self.trades:
                    if trade.entry_id == order_id:
                        trade.entry_price = order_status.avg_price
                        break
                return
        t = Timer(2.0, lambda: self._check_order_status(order_id))
        t.start()

    def _open_position(self, signal_result: int):
        trade_size = self.client.get_trade_size(self.contract, self.candles[-1].close, self.balance_pct)
        if trade_size is None:
            return

        order_side = "buy" if signal_result == 1 else "sell"
        position_side = "long" if signal_result == 1 else "short"
        
        self._add_log(f"{position_side} signal on {self.contract.symbol} - {self.tf}")
        # print("we reached _open_position breakout // strategies.py")
        order_status = self.client.place_order(self.contract, order_side, trade_size, "MARKET")

        if order_status is not None:
            self._add_log(f"{order_side.capitalize()} order placed on {self.exchange} | Status: {order_status.status}")

            self.ongoing_position = True
            avg_fill_price = None

            if order_status == "filled":    # might change for another exchange
                avg_fill_price = order_status.avg_price
            else:
                t = Timer(2.0, lambda: self._check_order_status(order_status.order_id))
                t.start()

            new_trade_specs = {"time": int(time.time() * 1000), "entry_price": avg_fill_price,
                               "contract": self.contract, "strategy": self.strategy_name, "side": position_side,
                               "status": "open", "pnl": 0, "quantity": trade_size, "entry_id": order_status.order_id}
            new_trade = Trade(new_trade_specs)

            self.trades.append(new_trade)

    def _check_tp_sl(self, trade: Trade):

        tp_triggered = False
        sl_triggered = False

        price = self.candles[-1].close

        if trade.side == "long":
            if self.stop_loss is not None:
                if price <= trade.entry_price * (1 - self.stop_loss) / 100:
                    sl_triggered = True
            if self.take_profit is not None:
                if price >= trade.entry_price * (1 + self.take_profit) / 100:
                    tp_triggered = True
        if trade.side == "short":
            if self.stop_loss is not None:
                if price >= trade.entry_price * (1 + self.stop_loss) / 100:
                    sl_triggered = True
            if self.take_profit is not None:
                if price <= trade.entry_price * (1 - self.take_profit) / 100:
                    tp_triggered = True

        if tp_triggered or sl_triggered:
            trigger = "Stop Loss" if sl_triggered else "Take Profit"
            self._add_log(f"{trigger} for {self.contract.symbol} {self.tf} on {self.contract.platform.capitalize()}")

            order_side = "SELL" if trade.side == "long" else "BUY"
            order_status = self.client.place_order(self.contract, order_side, trade.quantity, "market")

            if order_status is not None:
                self._add_log(f"Exit order on {self.contract.symbol} {self.tf} placed successfully")
                trade.status = "closed"
                self.ongoing_position = False


class TechnicalStrategy(Strategy):
    def __init__(self, client, contract: Contract, exchange: str, timeframe: str, balance_pct: float,
                 take_profit: float, stop_loss: float, other_params: typing.Dict):
        super().__init__(client, contract, exchange, timeframe, balance_pct, take_profit, stop_loss, "Technical")

        self._ema_fast = other_params["ema_fast"]
        self._ema_slow = other_params["ema_slow"]
        self._ema_signal = other_params["ema_signal"]

        self._rsi_length = other_params['rsi_length']

    def _rsi(self) -> float:
        close_list = [candle.close for candle in self.candles]

        closes = pd.Series(close_list)

        delta = closes.diff().dropna()
        up, down = delta.copy(), delta.copy()

        up[up < 0] = 0
        down[down > 0] = 0

        avg_gain = up.ewm(com=(self._rsi_length - 1), min_periods=self._rsi_length).mean()  # com: center of mass
        avg_loss = down.abs().ewm(com=(self._rsi_length - 1), min_periods=self._rsi_length).mean()

        rs = avg_gain / avg_loss    # rs = relative strength
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.round(2)

        return rsi.iloc[-2]

    def _macd(self) -> typing.Tuple[float, float]:

        close_list = [candle.close for candle in self.candles]

        closes = pd.Series(close_list)

        ema_fast = closes.ewm(span=self._ema_fast).mean()
        ema_slow = closes.ewm(span=self._ema_slow).mean()

        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=self._ema_signal).mean()

        return macd_line.iloc[-2], macd_signal.iloc[-2]

    def _check_signal(self) -> int:

        macd_line, macd_signal = self._macd()
        rsi = self._rsi()

        # print(rsi, macd_line, macd_signal)

        if rsi < 30 and macd_line > macd_signal:
            return 1
        elif rsi > 70 and macd_line < macd_signal:
            return -1
        else:
            return 0

    def check_trade(self, tick_type: str):
        if tick_type == "new_candle":
            signal_result = self._check_signal()

            if signal_result in [-1, 1] and not self.ongoing_position:
                self._open_position(signal_result)


class BreakoutStrategy(Strategy):
    def __init__(self, client, contract: Contract, exchange: str, timeframe: str, balance_pct: float,
                 take_profit: float, stop_loss: float, other_params: typing.Dict):
        super().__init__(client, contract, exchange, timeframe, balance_pct, take_profit, stop_loss, "Breakout")

        self._min_volume = other_params["min_volume"]

    def _check_signal(self) -> int:

        if self.candles[-1].volume > self._min_volume:
            if self.candles[-1].close > self.candles[-2].high:
                return 1
            elif self.candles[-1].close < self.candles[-2].low:
                return -1
            else:
                return 0
        else:
            return 0

    def check_trade(self, tick_type):
        if not self.ongoing_position:
            signal_result = self._check_signal()
            # print(f"signal result is {signal_result} // strategies.py")

            if signal_result in [-1, 1]:
                self._open_position(signal_result)
