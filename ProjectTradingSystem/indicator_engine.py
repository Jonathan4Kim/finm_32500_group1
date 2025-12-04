from collections import deque
from typing import Optional

class IndicatorEngine:
    
    def __init__(self, maxlen=200):
        self.prices = deque(maxlen=maxlen)
        self.last_price: Optional[float] = None

        #EMA state
        self.ema9 = None
        self.ema21 = None
        self.ema50 = None

        # ATR state
        self.atr14 = None

    def on_price(self, price: float):
        self._update_price_buffer(price)
        self._update_emas(price)
        self._update_atr(price)

    def _update_price_buffer(self, price: float):
        self.prices.append(price)

    def _update_ema(self, prev_ema, price, period):
        k = 2 / (period + 1)
        if prev_ema is None:
            return price  # initialize EMA starting value
        return price * k + prev_ema * (1 - k)

    def _update_emas(self, price: float):
        self.ema9 = self._update_ema(self.ema9, price, 9)
        self.ema21 = self._update_ema(self.ema21, price, 21)
        self.ema50 = self._update_ema(self.ema50, price, 50)

    def _update_atr(self, price: float):
        if self.last_price is None:
            self.last_price = price
            return
        
        tr = abs(price - self.last_price)
        self.last_price = price
        
        # ATR uses EMA(14)
        if self.atr14 is None:
            self.atr14 = tr  # initialize
        else:
            k = 2 / (14 + 1)
            self.atr14 = tr * k + self.atr14 * (1 - k)

    def high_n(self, n):
        if len(self.prices) < n:
            return None
        return max(list(self.prices)[-n:])

    def low_n(self, n):
        if len(self.prices) < n:
            return None
        return min(list(self.prices)[-n:])


        