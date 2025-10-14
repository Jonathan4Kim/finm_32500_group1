from backtester.strategy import VolatilityBreakoutStrategy
from backtester.price_loader import generate_price_series
import pytest
import pandas as pd
import numpy as np

# tests/test_strategy.py
def test_hold():
    strategy = VolatilityBreakoutStrategy(20)
    signals = strategy.generate_signals(generate_price_series(n=19, trend="up"))
    assert len(signals.unique()) == 1
    assert signals.unique()[0] == "HOLD"

def test_buy_signals_basic():
    strategy = VolatilityBreakoutStrategy()
    signals = strategy.generate_signals(generate_price_series(trend="up"))
    assert "BUY" in signals.values

def test_sell_signals_basic():
    strategy = VolatilityBreakoutStrategy()
    signals = strategy.generate_signals(generate_price_series(trend="down"))
    assert "SELL" in signals.values

def test_hold_signals_basic():
    strategy = VolatilityBreakoutStrategy()
    signals = strategy.generate_signals(generate_price_series(trend="flat"))
    assert "HOLD" in signals.values

def test_hold_signals_prev():
    strategy = VolatilityBreakoutStrategy()
    signals = strategy.generate_signals(generate_price_series(trend="flat", n=19))
    assert "HOLD" in signals.values

def test_signals_length():
    strategy = VolatilityBreakoutStrategy(window=30)
    prices = generate_price_series(trend="flat", n=19)
    signals = strategy.generate_signals(prices)
    assert len(signals) == len(prices)
    
def test_strategy_signals_length():
    series = generate_price_series(trend="up", n=30)
    strategy = VolatilityBreakoutStrategy(window=5)
    signals = strategy.generate_signals(series)
    assert len(signals) == len(series)

def test_strategy_outputs_valid_signals():
    series = generate_price_series(trend="volatile", n=30)
    strategy = VolatilityBreakoutStrategy(window=5)
    signals = strategy.generate_signals(series)
    assert set(signals.unique()).issubset({"BUY", "SELL", "HOLD"})