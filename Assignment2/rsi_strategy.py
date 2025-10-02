from strategies import Strategy
import math
from collections import deque

class RSIStrategy(Strategy):
    def __init__(self):
        self.__total_gain = {}
        self.__total_loss = {}
        self.__prev_price = {}
        self.__dq = {}


    def generate_signals(self, tick):
        # get attributes from MarketDataPoint
        price = tick.price
        symbol = tick.symbol
        # calculate price change. There's probably a way to make this more efficient
        if symbol not in self.__dq:
            self.__dq[symbol] = deque([])
            self.__total_gain[symbol] = 0.0
            self.__total_loss[symbol] = 0.0
            self.__prev_price[symbol] = price
            return ["HOLD"]
        
        # calculate price change and update previous price
        price_change = price - self.__prev_price[symbol]
        self.__prev_price[symbol] = price
        # add value to total gain/loss depending on difference
        if price_change < 0:
            # add value to losses
            self.__total_loss[symbol] = self.__total_loss[symbol] + abs(price_change)
        elif price_change > 0:
            self.__total_gain[symbol] = self.__total_gain[symbol] + price_change
        self.__dq[symbol].append(price_change)
        
        # if our deque doesn't have enough price changes, hold until we do
        if len(self.__dq.get(symbol, deque([]))) < 14:
            return ["HOLD"]

        # trim while you can
        dq = self.__dq[symbol]
        
        # we only exceed ideal deque length by 1 at any given point. we subtract value from loss/gain
        if len(dq) > 14:
            old_change = dq.popleft()
            if old_change < 0:
                self.__total_loss[symbol]  = self.__total_loss[symbol] - abs(old_change)
            elif old_change > 0:
                self.__total_gain[symbol]  = self.__total_gain[symbol] - old_change
        
        # get average gain/loss for rsi
        avg_gain = self.__total_gain[symbol] / 14
        avg_loss = self.__total_loss[symbol] / 14
        
        # make sure average gain/loss isn't maximum/minimum RSI values.
        if avg_gain == 0:
            rsi = 0
        elif avg_loss == 0:
            rsi = 100
        else:
            rel_strength = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rel_strength))
        
        # use RSI to determine signaling
        if rsi < 30:
            return ["BUY"]
        elif rsi > 70:
            return ["SELL"]
        return ["HOLD"]