from strategies import Strategy
import statistics as stat
from collections import deque

class VolatilityBreakoutStrategy(Strategy):
    def __init__(self, window=20):
        self.name = "volatility"
        self.__prev_returns = {}
        self.__prev_price = {}
        self.__window = window
        

    def generate_signals(self, tick):
        price, symbol = tick.price, tick.symbol

        # initialize symbol if not already initialized
        if symbol not in self.__prev_returns:
            self.__prev_returns[symbol] = deque(maxlen=self.__window)
            self.__prev_price[symbol] = price
            return ["HOLD"]

        # add new value
        prev_price = self.__prev_price[symbol]
        if prev_price == 0.0:
            return ["HOLD"]

        # get daily return on prices, and update previous returns/prices
        daily_return = (price - prev_price) / prev_price
        self.__prev_returns[symbol].append(daily_return)
        self.__prev_price[symbol] = price

        if len(self.__prev_returns[symbol]) < self.__window:
            return ["HOLD"]
        # compute population standard deviation from current returns
        past_vol = stat.pstdev(self.__prev_returns[symbol])
        # TODO: signal buy if daily return is greater than rolling 20-day volatility
        if past_vol < daily_return:
            return ["BUY"]
        # elif past_vol > daily_return:
        #     return ["SELL"]
        elif daily_return < -past_vol:
            return ["SELL"]
        else:
            return ["HOLD"]