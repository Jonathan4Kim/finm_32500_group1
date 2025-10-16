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
    eq = bt.run(prices)
    assert broker.position == 0
    assert broker.cash == 1000


# ---------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------
# def test_engine_handles_edge_cases(prices):
#     broker = Broker(initial_cash=1000)
#     strategy = VolatilityBreakoutStrategy(window=3)
#     bt = Backtester(strategy, broker)
#     eq = bt.run(prices)
#     assert isinstance(eq, pd.Series)
#     # Shouldn't raise or crash
#     assert len(eq) == len(prices)
#
#
# # ---------------------------------------------------------------------
# # Failure handling
# # ---------------------------------------------------------------------
# def test_engine_handles_broker_failure(monkeypatch):
#     # Mock broker that raises on buy
#     bad_broker = MagicMock()
#     bad_broker.buy.side_effect = RuntimeError("Buy failed")
#     bad_broker.sell.side_effect = None
#     bad_broker.position = 0
#     bad_broker.cash = 1000
#
#     prices = pd.Series(np.linspace(100, 110, 5))
#     fake_strategy = MagicMock()
#     fake_strategy.signals = pd.Series([0, 0, 1, 0, 0])
#
#     bt = Backtester(fake_strategy, bad_broker)
#
#     with pytest.raises(RuntimeError, match="Buy failed"):
#         bt.run(prices)