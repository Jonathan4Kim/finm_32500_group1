from abc import ABC, abstractmethod
from collections import deque

class Strategy(ABC):
    def __init__(self, params: dict):
        self.params = params
        self.price_history = {}

    @abstractmethod
    def generate_signals(self, tick) -> list:
        pass


class BreakoutStrategy(Strategy):
    def __init__(self, params: dict):
        super().__init__(params)
        self.lookback_window = params['lookback_window']  # 15
        self.threshold = params['threshold']  # 0.03

    def generate_signals(self, tick) -> list:
        symbol = tick.symbol
        price = tick.price
        
        # STEP 1: Initialize history for new symbol
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.lookback_window)
        
        # STEP 2: Add current price to history
        self.price_history[symbol].append(price)
        
        # STEP 3: Check if we have enough data
        if len(self.price_history[symbol]) < self.lookback_window:
            return []
        
        # STEP 4: Get the list of prices and find max/min
        prices_list = list(self.price_history[symbol])
        max_price = max(prices_list)
        min_price = min(prices_list)
        
        # STEP 5: Check for upside breakout
        upside_breakout = (price - max_price) / max_price
        
        if upside_breakout > self.threshold:
            return [{"action": "BUY", "symbol": symbol, "quantity": 100}]
        
        # STEP 6: Check for downside breakout
        downside_breakout = (price - min_price) / min_price
        
        if downside_breakout < -self.threshold:
            return [{"action": "SELL", "symbol": symbol, "quantity": 100}]
        
        return []


class MeanReversionStrategy(Strategy):
    def __init__(self, params: dict):
        super().__init__(params)
        self.lookback_window = params['lookback_window']  # 20
        self.threshold = params['threshold']  # 0.02

    def generate_signals(self, tick) -> list:
        symbol = tick.symbol
        price = tick.price
        
        # STEP 1: Initialize history for new symbol
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.lookback_window)
        
        # STEP 2: Add current price to history
        self.price_history[symbol].append(price)
        
        # STEP 3: Check if we have enough data
        if len(self.price_history[symbol]) < self.lookback_window:
            return []
        
        # STEP 4: Calculate moving average
        prices_list = list(self.price_history[symbol])
        avg_price = sum(prices_list) / len(prices_list)
        
        # STEP 5: Calculate deviation from average
        deviation = (price - avg_price) / avg_price
        
        # STEP 6: Generate signals based on deviation
        if deviation > self.threshold:
            # Price too high → SELL
            return [{"action": "SELL", "symbol": symbol, "quantity": 100}]
        elif deviation < -self.threshold:
            # Price too low → BUY
            return [{"action": "BUY", "symbol": symbol, "quantity": 100}]
        
        return []