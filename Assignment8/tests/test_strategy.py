"""Unit tests for strategy module components."""

from datetime import datetime

import pytest

from strategy import (
    WindowedMovingAverageStrategy,
    SentimentStrategy,
    MarketDataPoint,
    SentimentDataPoint,
)


def _price_tick(price: float) -> MarketDataPoint:
    return MarketDataPoint(datetime.now(), "AAPL", price)


def _sentiment_tick(value: int) -> SentimentDataPoint:
    return SentimentDataPoint(datetime.now(), "AAPL", value)


def test_windowed_strategy_requires_short_less_than_long():
    with pytest.raises(ValueError):
        WindowedMovingAverageStrategy(s=5, l=5)


def test_windowed_strategy_emits_buy_signal_when_short_avg_exceeds_long_avg():
    strategy = WindowedMovingAverageStrategy(s=2, l=4)
    prices = [100, 101, 102, 103, 110]
    signals = [strategy.generate_signals(_price_tick(price)) for price in prices]
    assert signals[0] == ["HOLD"]
    assert signals[-1] == "BUY"


def test_windowed_strategy_emits_sell_signal_when_short_avg_below_long_avg():
    strategy = WindowedMovingAverageStrategy(s=2, l=4)
    prices = [110, 109, 108, 107, 90]
    signals = [strategy.generate_signals(_price_tick(price)) for price in prices]
    assert signals[-1] == "SELL"


def test_sentiment_strategy_handles_thresholds():
    strategy = SentimentStrategy()
    assert strategy.generate_signal(_sentiment_tick(75)) == "BUY"
    assert strategy.generate_signal(_sentiment_tick(25)) == "SELL"
    assert strategy.generate_signal(_sentiment_tick(50)) == "HOLD"

