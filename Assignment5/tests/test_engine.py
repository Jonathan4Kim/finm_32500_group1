# tests/test_engine.py
from unittest.mock import MagicMock
import numpy as np
from backtester.engine import Backtester


def test_engine_uses_tminus1_signal(prices, broker, strategy, monkeypatch):
    # Force exactly one buy at t=10 by controlling signals
    fake_strategy = MagicMock()
    fake_strategy.signals = prices*0
    fake_strategy.signals.iloc[9] = 1  # triggers buy at t=10
    bt = Backtester(fake_strategy, broker)
    eq = bt.run(prices)
    assert broker.position == 1
    assert broker.cash == 1000 - float(prices.iloc[10])


def test_engine_no_trades(prices, broker, strategy):
    # Force zero by controlling signals
    fake_strategy = MagicMock()
    fake_strategy.signals = prices * 0
    bt = Backtester(fake_strategy, broker)
    assert broker.position == 0
    assert broker.cash == 1000


def test_engine_one_trade(prices, broker, strategy):
    # Force exactly one buy at t=10  and sell at t=11 by controlling signals
    fake_strategy = MagicMock()
    fake_strategy.signals = prices * 0
    fake_strategy.signals.iloc[9] = 1  # triggers buy at t=10
    fake_strategy.signals.iloc[10] = -1  # triggers buy at t=11
    bt = Backtester(fake_strategy, broker)
    eq = bt.run(prices)
    assert broker.position == 0
    assert broker.cash == 1000 - float(prices.iloc[10]) + float(prices.iloc[11])


def test_engine_error_trade(prices, broker, strategy):
    # Force all error signals
    fake_strategy = MagicMock()
    fake_strategy.signals = prices * -999
    bt = Backtester(fake_strategy, broker)
    eq = bt.run(prices)
    assert broker.position == 0
    assert broker.cash == 1000