from strategies import Strategy
from collections import deque

# Moving Average Crossover
class MAC(Strategy):
    def __init__(self, s: int, l: int):
        # initialize short term and long term length of moving averages. we assume s and l < len(dataset)
        self.__dq = deque([])
        # keeps track of the deque
        self.__size = 0
        # s and l show how many ticks far back we should look
        self.__short_window = s
        self.__long_window = l
        # establish short term and long term sums, that will change over time
        self.__short_sum = 0.0
        self.__long_sum = 0.0

    def generate_signals(self, tick):
        if self.__size < self.__long_window:

            # if self.__size > l - s: add to s average
            if self.__size >= self.__long_window - self.__short_window:
                self.__short_sum += tick.price

            # always add to lsum
            self.__long_sum+= tick.price

            # regardless, we will always add this to the deque
            self.__dq.append(tick.price)

            # add 1 to size to avoid it
            self.__size += 1
            return ["HOLD"]

        # compute moving average
        short_avg = self.__short_sum / self.__short_window
        long_avg = self.__long_sum / self.__long_window
        # update __ssum and __lsum by taking out least recent item in window
        self.__short_sum -= self.__dq[self.__long_window - self.__short_window]
        self.__long_sum -= self.__dq[0]
        # pop the least recent item from the deque as well
        self.__dq.popleft()
        # add the new price to the deque and sums
        self.__dq.append(tick.price)
        self.__short_sum += tick.price
        self.__long_sum += tick.price
        if short_avg > long_avg:
            return ["BUY"]
        elif short_avg < long_avg:
            return ["SELL"]
        else:
            return ["HOLD"]