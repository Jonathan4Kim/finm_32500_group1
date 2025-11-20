# strategy.py
from collections import deque
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional, Deque, List
import numpy as np


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    timestamp: datetime
    signal: SignalType
    symbol: str
    price: float
    reason: str


# ----------------- MA Crossover (streaming) -----------------
class MAStrategy:
    """
    Streaming moving-average crossover.
    Use on_new_bar(...) for each incoming bar.
    Emits a BUY on a crossover from short<=long to short>long and
    a SELL on a crossover from short>=long to short<long.
    """

    def __init__(self, symbol: str, short_window: int = 20, long_window: int = 50, position_size: int = 100):
        if short_window >= long_window:
            raise ValueError("short_window must be < long_window")
        self.symbol = symbol
        self.short_w = short_window
        self.long_w = long_window
        self.position_size = position_size

        # rolling buffers
        self._dq_long: Deque[float] = deque(maxlen=self.long_w)
        self._dq_short: Deque[float] = deque(maxlen=self.short_w)
        self._long_sum = 0.0
        self._short_sum = 0.0

        # state
        self.position = 0  # 0 flat, 1 long
        self._prev_short_gt_long: Optional[bool] = None

        # history (optional)
        self.signals: List[Signal] = []

    def on_new_bar(self, timestamp: datetime, open_p: float, high: float, low: float, close: float, volume: float) -> Optional[Signal]:
        price = float(close)

        # update long window
        if len(self._dq_long) == self.long_w:
            # deque full: subtract oldest from sum (popleft will happen automatically by deque maxlen, so we pop manually)
            oldest = self._dq_long.popleft()
            self._long_sum -= oldest
        self._dq_long.append(price)
        self._long_sum += price

        # update short window
        if len(self._dq_short) == self.short_w:
            oldest_s = self._dq_short.popleft()
            self._short_sum -= oldest_s
        self._dq_short.append(price)
        self._short_sum += price

        # Not enough data yet
        if len(self._dq_long) < self.long_w or len(self._dq_short) < self.short_w:
            return None

        short_avg = self._short_sum / self.short_w
        long_avg = self._long_sum / self.long_w
        curr_rel = short_avg > long_avg

        # initialize prev relation on first full-bar observation
        if self._prev_short_gt_long is None:
            self._prev_short_gt_long = curr_rel
            return None

        signal = None
        # crossing logic
        if (not self._prev_short_gt_long) and curr_rel and self.position == 0:
            signal = Signal(timestamp, SignalType.BUY, self.symbol, price, f"short_ma {short_avg:.6f} crossed above long_ma {long_avg:.6f}")
            self.position = 1
        elif self._prev_short_gt_long and (not curr_rel) and self.position == 1:
            signal = Signal(timestamp, SignalType.SELL, self.symbol, price, f"short_ma {short_avg:.6f} crossed below long_ma {long_avg:.6f}")
            self.position = 0

        self._prev_short_gt_long = curr_rel

        if signal:
            self.signals.append(signal)
        return signal

    def get_position_size(self) -> int:
        return self.position_size


# ----------------- Momentum Strategy (streaming ROC) -----------------
class MomentumStrategy:
    """
    Streaming Rate-of-Change momentum strategy.
    Emits BUY when momentum (price - price_n)/price_n crosses above threshold from below,
    emits SELL when momentum crosses below -threshold while in position.
    """

    def __init__(self, symbol: str, momentum_window: int = 10, momentum_threshold: float = 0.001, position_size: int = 100):
        if momentum_window < 1:
            raise ValueError("momentum_window must be >= 1")
        self.symbol = symbol
        self.m_window = momentum_window
        self.threshold = momentum_threshold
        self.position_size = position_size

        self._dq: Deque[float] = deque(maxlen=self.m_window + 1)  # need price_n and current
        self.position = 0
        self.signals: List[Signal] = []
        self._prev_momentum_above = None  # track previous relation (bool or None)

    def on_new_bar(self, timestamp: datetime, open_p: float, high: float, low: float, close: float, volume: float) -> Optional[Signal]:
        price = float(close)
        self._dq.append(price)

        # need at least m_window + 1 prices to compute momentum
        if len(self._dq) <= self.m_window:
            return None

        # momentum = (price_now - price_n) / price_n
        price_n = self._dq[0]
        if price_n == 0:
            return None
        momentum = (price - price_n) / price_n

        curr_above = momentum > self.threshold

        # initialize
        if self._prev_momentum_above is None:
            self._prev_momentum_above = curr_above
            # don't fire on first observation
            return None

        signal = None
        if (not self._prev_momentum_above) and curr_above and self.position == 0:
            signal = Signal(timestamp, SignalType.BUY, self.symbol, price, f"Momentum surged to {momentum:.6f} (> {self.threshold})")
            self.position = 1
        elif momentum < -self.threshold and self.position == 1:
            signal = Signal(timestamp, SignalType.SELL, self.symbol, price, f"Momentum collapsed to {momentum:.6f} (< -{self.threshold})")
            self.position = 0

        self._prev_momentum_above = curr_above

        if signal:
            self.signals.append(signal)
        return signal

    def get_position_size(self) -> int:
        return self.position_size


# ----------------- Statistical Z-Score Mean Reversion (streaming) -----------------
class StatisticalSignalStrategy:
    """
    Streaming Z-Score mean-reversion. Uses a lookback window (number of bars).
    BUY when current z-score < -zscore_threshold (oversold) and flat.
    SELL when z-score crosses zero while in a long position.
    """

    def __init__(self, symbol: str, lookback_window: int = 20, zscore_threshold: float = 1.5, position_size: int = 100):
        if lookback_window < 2:
            raise ValueError("lookback_window must be >= 2")
        self.symbol = symbol
        self.window = lookback_window
        self.threshold = zscore_threshold
        self.position_size = position_size

        self._dq: Deque[float] = deque(maxlen=self.window)
        self.position = 0
        self.signals: List[Signal] = []
        self._entry_zscore = None

    def _compute_zscore(self, price: float):
        arr = np.array(self._dq)
        mean = arr.mean()
        std = arr.std(ddof=0)
        if std == 0:
            return None
        return (price - mean) / std

    def on_new_bar(self, timestamp: datetime, open_p: float, high: float, low: float, close: float, volume: float) -> Optional[Signal]:
        price = float(close)
        self._dq.append(price)

        if len(self._dq) < self.window:
            return None

        z = self._compute_zscore(price)
        if z is None:
            return None

        signal = None
        # entry: oversold
        if self.position == 0 and z < -self.threshold:
            self._entry_zscore = z
            signal = Signal(timestamp, SignalType.BUY, self.symbol, price, f"Oversold z={z:.6f} < -{self.threshold}")
            self.position = 1

        # exit (long): z crosses zero from below to >= 0
        elif self.position == 1:
            # compute previous zscore using previous price if available
            # We can approximate by recomputing z-score for previous price (second to last in deque)
            if len(self._dq) >= 2:
                prev_price = list(self._dq)[-2]
                prev_z = self._compute_zscore(prev_price)
            else:
                prev_z = None

            if prev_z is not None and prev_z < 0 and z >= 0:
                signal = Signal(timestamp, SignalType.SELL, self.symbol, price, f"Mean reversion z crossed zero: prev {prev_z:.6f} -> curr {z:.6f}")
                self.position = 0
                self._entry_zscore = None

        if signal:
            self.signals.append(signal)
        return signal

    def get_position_size(self) -> int:
        return self.position_size