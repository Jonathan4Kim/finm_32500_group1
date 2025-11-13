import order as order_module
from order import Order, OrderState


def test_transition_follows_allowed_paths():
    order = Order("AAPL", 10, "1")

    order.transition(OrderState.ACKED)
    assert order.state == OrderState.ACKED

    order.transition(OrderState.FILLED)
    assert order.state == OrderState.FILLED


def test_transition_logs_failure_when_invalid(monkeypatch):
    events = []

    def fake_log(event_type, message):
        events.append((event_type, message))

    monkeypatch.setattr(order_module.Logger, "log", staticmethod(fake_log))
    order = Order("AAPL", 10, "1")

    order.transition(OrderState.CANCELED)

    assert order.state == OrderState.NEW
    assert events == [
        ("OrderTransFailed", "Cannot transition to OrderState.CANCELED from NEW")
    ]
