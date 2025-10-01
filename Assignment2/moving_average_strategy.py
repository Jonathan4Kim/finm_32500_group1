from strategies import Strategy
from collections import deque

# Moving Average Crossover
class MAC(Strategy):
    def __init__(self, s: int, l: int):
        # initialize short term and long term length of moving averages. we assume s and l < len(dataset)
        self.__dq = {}
        # keeps track of the deque
        self.__size = {}
        # s and l show how many ticks far back we should look
        self.__short_window = s
        self.__long_window = l
        # establish short term and long term sums, that will change over time
        self.__short_sum = {}
        self.__long_sum = {}

    def generate_signals(self, tick):
        symbol = tick.symbol
        if self.__size.get(symbol, 0) < self.__long_window:

            # if self.__size > l - s: add to s average
            if self.__size.get(symbol, 0) >= self.__long_window - self.__short_window:
                self.__short_sum[symbol] = self.__short_sum.get(symbol, 0.0) + tick.price

            # always add to lsum
            self.__long_sum[symbol] = self.__long_sum.get(symbol, 0.0) + tick.price

            # regardless, we will always add this to the deque
            if symbol in self.__dq:
                self.__dq[symbol].append(tick.price)
            else:
                self.__dq[symbol] = deque([tick.price])

            # add 1 to size to avoid it
            self.__size[symbol] = self.__size.get(symbol, 0) + 1
            return ["HOLD"]

        # compute moving average
        short_avg = self.__short_sum.get(symbol, 0.0) / self.__short_window
        long_avg = self.__long_sum.get(symbol, 0.0) / self.__long_window
        # update __ssum and __lsum by taking out least recent item in window
        self.__short_sum[symbol] = self.__short_sum.get(symbol, 0.0) - self.__dq.get(symbol, deque([]))[self.__long_window - self.__short_window]
        self.__long_sum[symbol] = self.__long_sum.get(symbol, 0.0) - self.__dq.get(symbol, deque([]))[0]
        # pop the least recent item from the deque as well
        self.__dq[symbol].popleft()
        # add the new price to the deque and sums
        if symbol in self.__dq:
            self.__dq[symbol].append(tick.price)
        else:
            self.__dq[symbol] = deque([tick.price])
        self.__short_sum[symbol] = self.__short_sum.get(symbol, 0.0) + tick.price
        self.__long_sum[symbol] = self.__long_sum.get(symbol, 0.0)  + tick.price
        if short_avg > long_avg:
            return ["BUY"]
        elif short_avg < long_avg:
            return ["SELL"]
        else:
            return ["HOLD"]