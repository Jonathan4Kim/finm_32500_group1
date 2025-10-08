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


class NaiveMovingAverageStrategy(Strategy):
    
    def __init__(self, s: int, l: int):
        """
        Initializes Naive Moving strategy
        with list (keeps track of prices)

        Args:
            s (int): short window length
            l (int): long window length
        """
        # initialize short term and long term length of moving averages. we assume s and l < len(dataset)
        self.__prices = []
        # keeps track of the deque
        self.__size = 0
        # s and l show how many ticks far back we should look
        self.__short_window = s
        self.__long_window = l
    
    def generate_signals(self, tick: MarketDataPoint):
        """
        Uses deque to compute signals for moving average strategy

        Args:
            tick (MarketDataPoint): A single marketdatapoint, with
            timestamp, price, and symbol attributes

        Returns:
            list[str]: a signal denoting whether to buy, sell, or hold

        Time Complexity: O(n) in our worst case, where our long window length == # of prices
        we have in self.__prices. When we compute this average, we iterate through all n elements to calculate
        total price naively for the long window.

        Space Complexity: O(n), as we store n prices in self.__prices continuously
        """
        # never consider until we have enough values for long sum window
        if self.__size < self.__long_window:
            # add value to array amortized O(1) in python
            self.__prices.append(tick.price)
            # add 1 to size attribute O(1)
            self.__size += 1

            # return hold position since there's not enough values to generate buy/sell signal
            return ["HOLD"]
        # take averages of previous s term naively O(1)
        short_avg = 0.0
        # gets sum of previous s prices: : O(s), not O(n) because atp we must go through all n elements worst case with l: see below
        for i in range(self.__size - 1, self.__size - self.__short_window - 1, -1):
            short_avg += self.__prices[i]
        # divide by short window length: O(1)
        short_avg /= self.__short_window
        long_avg = 0.0
        # iterate through l most recent components: O(l), or O(n) worst case when we go through entire price array
        for i in range(self.__size - 1, self.__size - self.__long_window - 1, -1):
            long_avg += self.__prices[i]
        # Divide by long window length O(1)
        long_avg /= self.__long_window

        # generate signals through comparison of averages: O(1)
        if short_avg > long_avg:
            return ["BUY"]
        elif short_avg < long_avg:
            return ["SELL"]
        else:
            return ["HOLD"]

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