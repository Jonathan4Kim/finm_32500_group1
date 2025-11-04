from abc import ABC, abstractmethod
from Assignment3.models import MarketDataPoint
from collections import deque

class Strategy(ABC):
    # TODO: remove list return
    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> list:
        pass

class WindowedMovingAverageStrategy(Strategy):
    def __init__(self, s: int, l: int):
        """
        Initializes Windowed Moving Average Strategy
        Object

        Args:
            s (int): short window, s < l
            l (int): long window, l > s
        """
        # initialize short term and long term length of moving averages. we assume s and l < len(dataset)
        self.__dq_long = deque([])   # deque for long window
        self.__dq_short = deque([])  # deque for short window

        # keeps track of the deque
        self.__size = 0

        # s and l show how many ticks far back we should look
        self.__short_window = s
        self.__long_window = l

        # establish short term and long term sums, that will change over time
        self.__short_sum = 0.0
        self.__long_sum = 0.0

    def generate_signals(self, tick: MarketDataPoint):
        """

        Args:
            tick (MarketDataPoint): A single MarketDataPoint, with
            timestamp, price, and symbol attributes

        Returns:
            list[str]: a signal denoting whether to buy, sell, or hold
        
        Time Complexity: O(1): we see that if self.__size < self.__long_window: 
        then we add values that need to be contained in short sum O(1)
        Computing averages take O(1), since we update prices 
        and store long/short total in attributes O(1), and then also store long/short
        window length as well. With O(1) popping and 
        append methods in our deque that allow us to not only take out values in constant time, but use the return
        methods to update the short/long sums as well while minimizing space.
        
        Space Complexity: O(k), where k == long window length. At every iteration where our deque
        size == long window length, we compute the average (which we store via sums & window lengths, allowing for O(1) computations),
        and then we drop the least recent price for the most recent price from tick (MarketDataPoint).
        This allows for at maximum, k values in our deque. With O(1) popping and append methods, this allows for O(1) runtime and O(k)
        space complexity at maximum. We do have O(s) in our smaller short price window, but O(l/k) + O(s) = O(k)
        """
        if self.__size < self.__long_window:

            # if self.__size > l - s: add to s average O(1) check
            if self.__size >= self.__long_window - self.__short_window:
                self.__short_sum += tick.price
                self.__dq_short.append(tick.price)  # track short window in O(1)

            # always add to lsum O(1)
            self.__long_sum += tick.price
            self.__dq_long.append(tick.price)

            # add 1 to size to avoid it O(1)
            self.__size += 1
            
            # we're holding until we have enough values to at least compute long window average
            return ["HOLD"]

        # compute moving average O(1), since sums and window lengths are stored as attributes
        short_avg = self.__short_sum / self.__short_window
        long_avg = self.__long_sum / self.__long_window

        # update sums in O(1) by removing least recent elements
        self.__short_sum -= self.__dq_short.popleft()
        self.__long_sum -= self.__dq_long.popleft()

        # add the new price to both deques and sums O(1) each
        self.__dq_long.append(tick.price)
        self.__long_sum += tick.price

        self.__dq_short.append(tick.price)
        self.__short_sum += tick.price

        # if short deque grows larger than short_window, drop oldest
        if len(self.__dq_short) > self.__short_window:
            self.__short_sum -= self.__dq_short.popleft()

        # generate signals through comparison of averages: O(1)
        if short_avg > long_avg:
            return ["BUY"]
        elif short_avg < long_avg:
            return ["SELL"]
        else:
            return ["HOLD"]


class SentimentStrategy(Strategy):
    
    def __init__(self):
        super().__init__()
    
    
    def generate_signals(self, tick):
        return super().generate_signals(tick)