import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Ensure ProjectTradingSystem modules are importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gateway import load_market_data, log_order_event  # noqa: E402
from order import Order  # noqa: E402
from order_manager import OrderManager  # noqa: E402
from orderbook import OrderBook  # noqa: E402
from matching_engine import MatchingEngine  # noqa: E402
from risk_engine import RiskEngine  # noqa: E402
from strategy import MarketDataPoint, MAStrategy, MomentumStrategy, StatisticalSignalStrategy  # noqa: E402


@pytest.fixture(autouse=True)
def reset_risk_engine():
    # RiskEngine is a singleton; reset between tests.
    RiskEngine._instance = None
    yield
    RiskEngine._instance = None


def test_gateway_loads_market_data(tmp_path):
    csv_file = tmp_path / "market_data.csv"
    csv_file.write_text(
        "Datetime,Open,High,Low,Close,Volume,Symbol\n"
        "2025-01-01 09:30:00,100,101,99,100.5,1000,ABC\n"
        "2025-01-01 09:31:00,100.5,102,100,101,1200,ABC\n"
    )
    points = list(load_market_data(str(csv_file)))
    assert len(points) == 2
    assert points[0].symbol == "ABC"
    assert points[0].price == 100.5


def test_mastrategy_buy_and_sell_signals():
    strat = MAStrategy(symbol="ABC", short_window=2, long_window=3, position_size=1)
    base = datetime(2025, 1, 1, 9, 30, 0)
    prices = [100, 99, 101, 102, 99]  # should buy at 102 crossover, sell on drop to 99
    signals = []
    for i, p in enumerate(prices):
        mdp = MarketDataPoint(timestamp=base + timedelta(minutes=i), symbol="ABC", price=p)
        sig = strat.on_new_bar(mdp)
        if sig:
            signals.append(sig.signal.name)
    assert "BUY" in signals
    assert "SELL" in signals


def test_momentum_strategy_buy_and_sell():
    strat = MomentumStrategy(symbol="ABC", momentum_window=1, momentum_threshold=0.0, position_size=1)
    base = datetime(2025, 1, 1, 9, 30, 0)
    # Prices dip, then rise (BUY), then drop (SELL)
    prices = [100, 99, 100.5, 99]
    signals = []
    for i, p in enumerate(prices):
        mdp = MarketDataPoint(timestamp=base + timedelta(minutes=i), symbol="ABC", price=p)
        sig = strat.on_new_bar(mdp)
        if sig:
            signals.append(sig.signal.name)
    assert "BUY" in signals
    assert "SELL" in signals


def test_statistical_strategy_buy_and_sell():
    strat = StatisticalSignalStrategy(symbol="ABC", lookback_window=3, zscore_threshold=0.5, position_size=1)
    base = datetime(2025, 1, 1, 9, 30, 0)
    prices = [100, 101, 102, 90, 100]  # oversold then mean reversion above 0
    signals = []
    for i, p in enumerate(prices):
        mdp = MarketDataPoint(timestamp=base + timedelta(minutes=i), symbol="ABC", price=p)
        sig = strat.on_new_bar(mdp)
        if sig:
            signals.append(sig.signal.name)
    assert signals[0] == "BUY"
    assert "SELL" in signals[1:]


def test_orderbook_add_modify_cancel():
    ob = OrderBook()
    ob.add_order({"order_id": 1, "side": "BUY", "symbol": "ABC", "price": 100, "qty": 10})
    trades = ob.add_order({"order_id": 2, "side": "SELL", "symbol": "ABC", "price": 99, "qty": 4})
    assert trades and trades[0]["qty"] == 4
    # Modify remaining buy to cross again
    trades2 = ob.modify_order(1, new_price=101)
    # some matching may occur if asks remain; ensure still valid call
    assert isinstance(trades2, list)
    assert ob.cancel_order(1) is True


def test_orderbook_partial_fill_and_depth():
    ob = OrderBook()
    ob.add_order({"order_id": 1, "side": "BUY", "symbol": "ABC", "price": 100, "qty": 5})
    trades = ob.add_order({"order_id": 2, "side": "SELL", "symbol": "ABC", "price": 100, "qty": 10})
    assert trades and trades[0]["qty"] == 5  # partial fill of sell
    depth = ob.depth()
    # remaining sell quantity should appear on asks
    assert depth["asks"][0][1] == 5


def test_matching_engine_simulation_returns_expected_keys():
    for side in ("BUY", "SELL"):
        for _ in range(3):
            result = MatchingEngine.simulate_execution(Order(side=side, symbol="ABC", qty=5, price=100))
            assert result["status"] in {"FILLED", "PARTIAL", "CANCELLED"}
            if result["status"] != "CANCELLED":
                assert result["price"] is not None


def test_risk_engine_limits_and_cash_updates():
    re = RiskEngine(max_order_size=10, max_position=10, cash_balance=100, max_total_buy=8, max_total_sell=8)
    buy_order = Order(side="BUY", symbol="ABC", qty=5, price=10)
    assert re.check(buy_order)
    re.update_position(buy_order, filled_qty=5)
    assert re.cash_balance == 50  # 100 - 5*10
    # Exceeds total buy limit
    assert not re.check(Order(side="BUY", symbol="ABC", qty=10, price=1))
    # Sell increases cash and updates totals
    sell_order = Order(side="SELL", symbol="ABC", qty=3, price=11)
    assert re.check(sell_order)
    re.update_position(sell_order, filled_qty=3)
    assert re.cash_balance == 83  # 50 + 3*11
    assert not re.check(Order(side="SELL", symbol="ABC", qty=10, price=1))


def test_order_manager_flow_with_logging(tmp_path, monkeypatch):
    # Redirect audit log to temp folder
    audit_file = tmp_path / "audit.csv"
    monkeypatch.setattr("gateway._default_audit_path", lambda: audit_file)

    om = OrderManager(RiskEngine(max_order_size=1000, max_position=1000, cash_balance=1_000_000), simulated=True)
    order = Order(side="BUY", symbol="ABC", qty=5, price=100)
    result = om.process_order(order)
    assert result["ok"] is True
    assert audit_file.exists()
    # Expect qty/price populated and status in allowed set
    assert result["status"] in {"FILLED", "PARTIAL", "CANCELLED"}
    if result["status"] != "CANCELLED":
        assert result["filled_qty"] > 0
        assert result["filled_price"] is not None
    # Ensure the audit log captured both send and terminal events
    rows = audit_file.read_text().strip().splitlines()
    assert len(rows) >= 3  # header + send + terminal
