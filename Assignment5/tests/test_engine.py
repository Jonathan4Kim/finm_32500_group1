# tests/test_engine.py
from unittest.mock import MagicMock
import numpy as np
import pandas as pd
from backtester.engine import Backtester
import pytest


def test_engine_uses_tminus1_signal(prices, broker, monkeypatch):
    # Force exactly one buy at t=10 by controlling signals
    fake_strategy = MagicMock()
    fake_strategy.signals = prices*0
    fake_strategy.signals.iloc[9] = 1  # triggers buy at t=10
    bt = Backtester(fake_strategy, broker)
    eq = bt.run(prices)
    assert broker.position == 1
    assert broker.cash == 1000 - float(prices.iloc[10])


def test_engine_no_trades(prices, broker):
    # Force zero by controlling signals
    fake_strategy = MagicMock()
    fake_strategy.signals = prices * 0
    bt = Backtester(fake_strategy, broker)
    assert broker.position == 0
    assert broker.cash == 1000


def test_engine_one_trade(prices, broker):
    # Force exactly one buy at t=10  and sell at t=11 by controlling signals
    fake_strategy = MagicMock()
    fake_strategy.signals = prices * 0
    fake_strategy.signals.iloc[9] = 1  # triggers buy at t=10
    fake_strategy.signals.iloc[10] = -1  # triggers buy at t=11
    bt = Backtester(fake_strategy, broker)
    eq = bt.run(prices)
    assert broker.position == 0
    assert broker.cash == 1000 - float(prices.iloc[10]) + float(prices.iloc[11])


def test_engine_error_trade_invalid_signal(prices, broker):
    fake_strategy = MagicMock()
    fake_strategy.signals = prices * -999
    bt = Backtester(fake_strategy, broker)
    with pytest.raises(ValueError):
        bt.run(prices)


def test_engine_error_trade_no_signals(prices, broker):
    fake_strategy = MagicMock()
    fake_strategy.signals = None
    bt = Backtester(fake_strategy, broker)
    with pytest.raises(ValueError):
        bt.run(prices)


def test_engine_error_trade_no_prices(prices, broker):
    fake_strategy = MagicMock()
    fake_strategy.signals = prices * 0
    fake_prices = None
    bt = Backtester(fake_strategy, broker)
    with pytest.raises(ValueError):
        bt.run(fake_prices)


def test_engine_equity_matches_cash_plus_position(prices, broker):
    """Ensure final equity = cash + pos × price."""
    fake_strategy = MagicMock()
    fake_strategy.signals = prices * 0
    fake_strategy.signals.iloc[9] = 1  # triggers buy at t=10
    bt = Backtester(fake_strategy, broker)
    eq = bt.run(prices)
    final_equity = broker.cash + broker.position * prices.iloc[-1]

    expected_cash = 1000 - prices.iloc[10]
    expected_position = 1
    expected_equity = expected_cash + expected_position * prices.iloc[-1]

    assert np.isclose(final_equity, expected_equity), "Final equity must equal cash + position × price."


def test_constant_price_series(broker):
    """Constant prices shouldn’t break logic."""
    prices = pd.Series([100, 100, 100, 100])
    fake_strategy = MagicMock()
    fake_strategy.signals = prices * 0
    bt = Backtester(fake_strategy, broker)
    bt.run(prices)
    assert broker.position == 0 and broker.cash == 1000,"Equity series contains NaN for constant prices."


def test_nans_at_head(broker):
    """NaNs at start should filled with zeros."""
    prices = pd.Series([np.nan, np.nan, 100, 101, 102])
    fake_strategy = MagicMock()
    fake_strategy.signals = prices * 0
    bt = Backtester(fake_strategy, broker)
    bt.run(prices)
    assert broker.position == 0 and broker.cash == 1000


def test_very_short_series(broker):
    """Series with one or two prices should not crash."""
    prices = pd.Series([100])
    fake_strategy = MagicMock()
    fake_strategy.signals = prices * 0
    bt = Backtester(fake_strategy, broker)
    bt.run(prices)
    assert broker.position == 0 and broker.cash == 1000