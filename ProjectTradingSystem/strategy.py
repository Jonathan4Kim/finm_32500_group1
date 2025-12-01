# strategy.py
from collections import deque
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Deque, List, Callable, Dict
import numpy as np


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass(frozen=True)
class MarketDataPoint:
    # create timestamp, symbol, and price instances with established types
    timestamp: datetime
    symbol: str
    price: float

    def __str__(self):
        return f"timestamp: {self.timestamp}, symbol: {self.symbol}, price: {self.price}"


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

    def __init__(self, symbol: str, short_window: int = 20, long_window: int = 50):
        if short_window >= long_window:
            raise ValueError("short_window must be < long_window")
        self.symbol = symbol
        self.short_w = short_window
        self.long_w = long_window
        self.position_size = 0

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

    def on_new_bar(self, data_point: MarketDataPoint) -> Optional[Signal]:
        price = float(data_point.price)
        timestamp = data_point.timestamp

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

    def __init__(self, symbol: str, momentum_window: int = 10, momentum_threshold: float = 0.001, position_size: float = 100):
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

    def on_new_bar(self, data_point: MarketDataPoint) -> Optional[Signal]:
        price = float(data_point.price)
        timestamp = data_point.timestamp
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

    def __init__(self, symbol: str, lookback_window: int = 20, zscore_threshold: float = 1.5, position_size: float = 100):
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

    def on_new_bar(self, data_point: MarketDataPoint) -> Optional[Signal]:
        price = float(data_point.price)
        timestamp = data_point.timestamp
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


class SentimentStrategy:
    """
    Streaming sentiment-driven strategy that fuses price bars with external news or
    social media sentiment scores. Buys when sentiment crosses the positive
    threshold, sells when sentiment turns strongly negative.
    """

    def __init__(
        self,
        symbol: str,
        sentiment_lookup: Optional[Callable[[datetime, str], float]] = None,
        sentiment_scores: Optional[Dict[str, float]] = None,
        positive_threshold: float = 0.3,
        negative_threshold: float = -0.3,
        cooldown_bars: int = 3,
        position_size: int = 100,
    ):
        """
        Initialize the sentiment strategy with thresholds and an optional external sentiment provider.

        Args:
            symbol (str): Target trading symbol.
            sentiment_lookup (Optional[Callable[[datetime, str], float]]): External lookup hook returning
                a normalized sentiment score for the given timestamp and symbol.
            sentiment_scores (Optional[Dict[str, float]]): Static mapping of timestamps to sentiment values
                when no callable provider is supplied.
            positive_threshold (float): Trigger level to enter long positions.
            negative_threshold (float): Trigger level to exit longs / go flat.
            cooldown_bars (int): Minimum number of bars between trades to avoid over-trading.
            position_size (int): Quantity per order.
        """
        if cooldown_bars < 1:
            raise ValueError("cooldown_bars must be >= 1")

        self.symbol = symbol
        self.position_size = position_size
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold
        self.cooldown_bars = cooldown_bars
        self.position = 0
        self.signals: List[Signal] = []

        self._sentiment_scores = sentiment_scores or {}
        self._external_lookup = sentiment_lookup
        self._bars_since_trade = cooldown_bars

    def _format_key(self, timestamp: datetime) -> str:
        """
        Normalize timestamps into keys compatible with stored sentiment scores.

        Args:
            timestamp (datetime): The event timestamp to normalize.

        Returns:
            str: Compact representation used inside sentiment score dictionaries.
        """
        return timestamp.strftime("%Y-%m-%d %H:%M")

    def _default_sentiment_lookup(self, timestamp: datetime, symbol: str) -> float:
        """
        Fetch sentiment from the internal mapping when no external provider is supplied.

        Args:
            timestamp (datetime): Event timestamp.
            symbol (str): Symbol for which sentiment is requested (unused but accepted for compatibility).

        Returns:
            float: Sentiment score in [-1, 1]; defaults to 0.0 when no reading exists.
        """
        if symbol != self.symbol:
            return 0.0
        exact_key = timestamp.isoformat(timespec="minutes")
        if exact_key in self._sentiment_scores:
            return float(self._sentiment_scores[exact_key])
        return float(self._sentiment_scores.get(self._format_key(timestamp), 0.0))

    def update_sentiment(self, timestamp: datetime, score: float):
        """
        Add or overwrite a sentiment reading for an upcoming timestamp.

        Args:
            timestamp (datetime): When the sentiment applies.
            score (float): Normalized sentiment measure derived from external data.
        """
        self._sentiment_scores[self._format_key(timestamp)] = float(score)

    def _current_sentiment(self, timestamp: datetime) -> float:
        """
        Resolve the sentiment score for the provided timestamp using the chosen provider.

        Args:
            timestamp (datetime): Timestamp associated with the bar.

        Returns:
            float: Latest sentiment reading.
        """
        provider = self._external_lookup or self._default_sentiment_lookup
        return float(provider(timestamp, self.symbol))

    def on_new_bar(self, data_point: MarketDataPoint) -> Optional[Signal]:
        """
        Consume a fresh bar, compare sentiment to thresholds, and emit trading signals as needed.

        Args:
            data_point (MarketDataPoint): The incoming OHLC-derived price snapshot.

        Returns:
            Optional[Signal]: BUY/SELL signal when criteria are met, otherwise None.
        """
        if data_point.symbol != self.symbol:
            return None

        sentiment = self._current_sentiment(data_point.timestamp)
        self._bars_since_trade = min(self.cooldown_bars, self._bars_since_trade + 1)
        signal = None

        if (
            self.position == 0
            and sentiment >= self.positive_threshold
            and self._bars_since_trade >= self.cooldown_bars
        ):
            reason = f"Sentiment {sentiment:.4f} >= threshold {self.positive_threshold}"
            signal = Signal(data_point.timestamp, SignalType.BUY, self.symbol, float(data_point.price), reason)
            self.position = 1
            self._bars_since_trade = 0
        elif self.position == 1 and sentiment <= self.negative_threshold:
            reason = f"Sentiment {sentiment:.4f} <= threshold {self.negative_threshold}"
            signal = Signal(data_point.timestamp, SignalType.SELL, self.symbol, float(data_point.price), reason)
            self.position = 0
            self._bars_since_trade = 0

        if signal:
            self.signals.append(signal)
        return signal

    def get_position_size(self) -> int:
        """
        Return the configured position size for downstream order creation.

        Returns:
            int: Quantity per order.
        """
        return self.position_size
    
if __name__ == "__main__":
    # Quick demo to validate MAStrategy generates a buy then a sell signal.
    ma = MAStrategy(symbol="DEMO", short_window=3, long_window=5, position_size=10)
    prices = [105, 104, 103, 102, 101, 102, 103, 104, 103, 102, 101]
    start_ts = datetime.now()

    print("Running MAStrategy demo with sample prices...")
    for i, price in enumerate(prices):
        ts = start_ts + timedelta(minutes=i)
        data_point = MarketDataPoint(timestamp=ts, symbol="DEMO", price=price)
        sig = ma.on_new_bar(data_point)
        if sig:
            print(f"{sig.timestamp.isoformat()} -> {sig.signal.value} {sig.symbol} @ {sig.price:.2f} ({sig.reason})")
