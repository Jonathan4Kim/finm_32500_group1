from strategies import Strategy
from collections import deque

class MACDStrategy(Strategy):
    # MACD Strategy: Buy if MACD line crosses above the signal line (bullish crossover).
    def __init__(self):
        # Store price history for each symbol
        self.price_history = {}
        # Store MACD and signal line values
        self.macd_values = {}
        self.signal_values = {}
        # Store previous values for crossover detection
        self.prev_macd = {}
        self.prev_signal = {}
        
    def generate_signals(self, tick):
        symbol = tick.symbol
        price = tick.price
        
        # Initialize data structures for new symbols
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=26)  # Need at least 26 periods for MACD
            self.macd_values[symbol] = deque(maxlen=9)    # Need 9 periods for signal line
            self.signal_values[symbol] = deque(maxlen=9)
            self.prev_macd[symbol] = None
            self.prev_signal[symbol] = None
        
        # Add current price to history
        self.price_history[symbol].append(price)
        
        # Need at least 26 periods to calculate MACD
        if len(self.price_history[symbol]) < 26:
            return ["HOLD"]
        
        # Calculate MACD line: EMA(12) - EMA(26)
        prices = list(self.price_history[symbol])
        short_ema = self._calculate_ema(prices, 12)
        long_ema = self._calculate_ema(prices, 26)
        macd = short_ema - long_ema
        
        # Store MACD value
        self.macd_values[symbol].append(macd)
        
        # Need at least 9 MACD values to calculate signal line
        if len(self.macd_values[symbol]) < 9:
            return ["HOLD"]
        
        # Calculate signal line: EMA(9) of MACD
        macd_list = list(self.macd_values[symbol])
        signal = self._calculate_ema(macd_list, 9)
        
        # Store signal value
        self.signal_values[symbol].append(signal)
        
        # Check for crossover
        if self.prev_macd[symbol] is not None and self.prev_signal[symbol] is not None:
            # Bullish crossover: MACD crosses above signal line
            if (self.prev_macd[symbol] <= self.prev_signal[symbol] and 
                macd > signal):
                self.prev_macd[symbol] = macd
                self.prev_signal[symbol] = signal
                return ["BUY"]
            # Bearish crossover: MACD crosses below signal line
            elif (self.prev_macd[symbol] >= self.prev_signal[symbol] and 
                  macd < signal):
                self.prev_macd[symbol] = macd
                self.prev_signal[symbol] = signal
                return ["SELL"]
        # Update previous values
        self.prev_macd[symbol] = macd
        self.prev_signal[symbol] = signal
        return ["HOLD"]
    
    def _calculate_ema(self, prices, span):
        if len(prices) == 0:
            return 0.0
        # Calculate alpha (smoothing factor)
        alpha = 2.0 / (span + 1)
        # Initialize with first price
        ema = prices[0]
        # Calculate EMA for remaining prices
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema 
        return ema