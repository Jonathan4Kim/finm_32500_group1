from strategies import Strategy
import math
from collections import deque

class RSIStrategy(Strategy):
    def __init__(self):
        self.__total_gain = {}
        self.__num_gain = {}
        self.__total_loss = {}
        self.__num_loss = {}
        self.__prev_price = {}
        self.__dq = {}

    def generate_signals(self, tick):
        # get attributes from MarketDataPoint
        price = tick.price
        symbol = tick.symbol
        # calculate price change
        if self.__dq.get(symbol, deque([])):
            self.__prev_price[symbol] = price
            price_change = price - self.__prev_price.get(symbol, 0.0)
        else:
            return ["HOLD"]
        # add value to total gain/loss depending on difference
        if price_change < 0:
            # add value to losses
            self.__total_loss[symbol] = self.__total_loss.get(symbol, 0.0) + abs(price_change)
            self.__num_loss[symbol] = self.__num_loss.get(symbol, 0) + 1
        elif price_change > 0:
            self.__total_gain[symbol] = self.__total_gain.get(symbol, 0.0) + price_change
            self.__num_gain[symbol] = self.__num_gain.get(symbol, 0) + 1
        # keep previous value and add new price change to deque
        self.__prev_price[symbol] = price
        if symbol not in self.__dq:
            self.__dq[symbol] = deque()
        self.__dq[symbol].append(price_change)
        if len(self.__dq.get(symbol, deque([]))) < 14:
            return ["HOLD"]
        # remove from deque if it's over 14 observations
        if self.__num_gain.get(symbol, 0) == 0 or self.__num_loss.get(symbol, 0) == 0:
            return ["HOLD"]
        avg_gain = self.__total_gain.get(symbol, 0.0) / self.__num_gain.get(symbol, 0)
        avg_loss = self.__total_loss.get(symbol, 0.0) / self.__num_loss.get(symbol, 0)
        rel_strength = avg_gain / avg_loss
        rsi = 100 - (1 / (1 + rel_strength))
        dq = self.__dq.get(symbol, deque([]))
        while len(dq) > 14:
            old_change = dq.popleft()
            if old_change < 0:
                self.__total_loss[symbol]  = self.__total_loss.get(symbol, 0.0) - abs(old_change)
                self.__num_loss[symbol]  = self.__num_loss.get(symbol, 0) - 1
            elif old_change > 0:
                self.__total_gain[symbol]  = self.__total_gain.get(symbol, 0.0) - old_change
                self.__num_gain[symbol]  = self.__num_gain.get(symbol, 0) - 1
        if rsi < 30:
            return ["BUY"]
        elif rsi > 70:
            return ["SELL"]
        return ["HOLD"]