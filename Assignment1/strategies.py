from abc import ABC, abstractmethod
# TODO: CHANGE IF WE MOVE MARKETDATAPOINT CLASS TO MODELS.PY
from data_loader import MarketDataPoint
from data_loader import load_data
from collections import deque

class Strategy(ABC):
    # TODO: remove list return
    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> list:
        pass

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

# Momentum
class Momentum(Strategy):
    def __init__(self):
        # we need previous price
        self.__prev_price = None
        # previous difference
        self.__prev_diff = None
        # iterations
        self.__iter = 0

    def generate_signals(self, tick):
        """
        Uses the previous tick price differences between the last two
        MarketDataPoint objects 

        Args:
            tick (_type_): a MarketDataPoint Object with
            price, timestamp, and symbol attributes.

        Returns:
            List: a single length list telling either of the following:
            {BUY, SELL, HOLD}, giving the action
        """
        # edge case: just starting: return, but update previous price.
        if self.__iter == 0:
            
            # there's no previous price, update it
            self.__prev_price = tick.price
            
            # update the iteration count for the future
            self.__iter += 1
            
            # hold signal
            return ["HOLD"]
        elif self.__iter == 1:
            # first difference! store it accordingly
            self.__prev_diff = tick.price - self.__prev_price
            
            # update previous price to the current tick price
            self.__prev_price = tick.price

            # add 1 to iteration attribute
            self.__iter += 1
            
            # hold signal
            return ["HOLD"]
        
        # add 1 to iteration count (not necessary after base cases)
        self.__iter += 1
        
        # subtract tick - previous tick
        new_diff = tick.price - self.__prev_price
        
        # compare it to previous momentum
        # if both >:
        if new_diff > 0 and self.__prev_diff > 0:
            # update previous diff (tick - previous tick)
            self.__prev_diff = new_diff
            # update previous tick (current tick variable)
            self.__prev_price = tick.price
            # sell
            return ["SELL"]
        # if both negative:
        elif new_diff < 0 and self.__prev_diff < 0:
            # update previous diff (tick - previous tick)
            self.__prev_diff = new_diff
            # update previous tick (current tick variable)
            self.__prev_price = tick.price
            # buy
            return ["BUY"]
        # else:
        else:
            # update previous diff (tick - previous tick)
            self.__prev_diff = new_diff
            # update previous tick (current tick variable)
            self.__prev_price = tick.price
            # hold
            return ["HOLD"]