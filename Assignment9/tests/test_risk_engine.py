import risk_engine as risk_engine_module
from order import Order
from risk_engine import RiskEngine


def spy_logger(monkeypatch):
    calls = []

    def fake_log(event_type, message):
        calls.append((event_type, message))

    monkeypatch.setattr(risk_engine_module.Logger, "log", staticmethod(fake_log))
    return calls


def test_check_rejects_order_over_size(monkeypatch):
    calls = spy_logger(monkeypatch)
    engine = RiskEngine(max_order_size=10)
    order = Order("AAPL", 15, "1")

    assert not engine.check(order)
    assert calls == [
        ("OrderFailed", "Order quantity of 15 exceeds max order size 10")
    ]


def test_check_rejects_when_position_limit_exceeded(monkeypatch):
    calls = spy_logger(monkeypatch)
    engine = RiskEngine(max_position=100)
    existing = Order("MSFT", 90, "1")
    engine.positions["MSFT"] = [existing]
    new_order = Order("MSFT", 15, "1")

    assert not engine.check(new_order)
    assert calls == [
        ("OrderFailed", "Order quantity of 15 would exceed max position size 100")
    ]


def test_update_position_persists_valid_orders(monkeypatch):
    spy_logger(monkeypatch)  # ensure logger is patched even if unused
    engine = RiskEngine()
    order = Order("TSLA", 50, "1")

    engine.update_position(order)

    assert engine.positions["TSLA"] == [order]


def test_update_position_skips_failed_orders(monkeypatch):
    calls = spy_logger(monkeypatch)
    engine = RiskEngine(max_order_size=5)
    order = Order("TSLA", 50, "1")

    engine.update_position(order)

    assert "TSLA" not in engine.positions
    assert calls == [
        ("OrderFailed", "Order quantity of 50 exceeds max order size 5")
    ]
