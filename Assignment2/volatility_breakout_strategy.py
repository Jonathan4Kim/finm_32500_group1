from strategies import Strategy
import statistics as stat
from collections import deque

class VolatilityBreakoutStrategy(Strategy):
    def __init__(self, window=20):
        # TODO: Intialize
        self.name = "volatility"
        self.__n = {}
        self.__prev_returns = {}
        self.__prev_price = {}
        self.__window = window
        

    def generate_signals(self, tick):
        price, symbol = tick.price, tick.symbol
        if symbol not in self.__prev_returns:
            self.__prev_returns[symbol] = deque(maxlen=self.__window)
            self.__prev_price[symbol] = price
            return ["HOLD"]
        # add new value
        prev_price = self.__prev_price.get(symbol, 0.0)
        daily_return = (price - prev_price) / prev_price
        # add newest value
        self.__prev_returns[symbol].append(daily_return)
        # add price to deque after computing volatility.
        self.__prev_price[symbol] = price
        if len(self.__prev_returns[symbol]) < self.__window:
            self.__prev_returns[symbol].append(daily_return)
            return ["HOLD"]
        # TODO:  compute rolling 20-day volatility
        past_vol = stat.stdev(self.__prev_returns[symbol])
        # TODO: signal buy if daily return is greater than rolling 20-day volatility
        if past_vol < daily_return:
            return ["BUY"]
        # elif past_vol > daily_return:
        #     return ["SELL"]
        else:
            return ["HOLD"]