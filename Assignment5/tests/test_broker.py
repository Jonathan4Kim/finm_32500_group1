# tests/test_broker.py
import pytest

# Buy Tests

def test_market_order_buy_updates_cash_and_position(broker):
    """Buying reduces cash and increases position."""
    broker.market_order("buy", qty=2, price=10)
    assert broker.position == 2
    assert broker.cash == pytest.approx(1_000 - (2 * 10))

def test_buy_insufficient_funds_raises_error(broker):
    """Buying more than available cash should raise ValueError."""
    with pytest.raises(ValueError, match="insufficient funds"):
        broker.market_order("buy", qty=200, price=10)

def test_buy_with_invalid_qty_raises_error(broker):
    """Invalid quantities (zero, None, or non-integer) should raise ValueError."""
    invalid_values = [0, None, 1.5]
    for qty in invalid_values:
        with pytest.raises(ValueError, match="Quantity is invalid"):
            broker.market_order("buy", qty, 100)

# Sell Tests

def test_market_order_sell_updates_cash_and_position(broker):
    """Selling increases cash and decreases position."""
    broker.market_order("buy", 5, 10)
    broker.market_order("sell", 2, 20)
    assert broker.position == 3
    assert broker.cash == pytest.approx(1_000 - 5*10 + 2*20)

def test_sell_without_position_raises_error(broker):
    """Selling with no open position should raise ValueError."""
    with pytest.raises(ValueError, match="no position to sell"):
        broker.market_order("sell", 1, 50)

def test_sell_invalid_qty_raises_error(broker):
    """Invalid sell quantity should raise ValueError."""
    broker.market_order("buy", 5, 10)
    with pytest.raises(ValueError, match="Quantity is invalid"):
        broker.market_order("sell", 0, 100)

# Invalid Side Test

def test_invalid_side_raises_error(broker):
    """Passing an invalid side (not buy/sell) should raise ValueError."""
    with pytest.raises(ValueError, match="Invalid side"):
        broker.market_order("hold", 10, 100)

# A few additional tests for edge cases

def test_multiple_trades_accumulate_correctly(broker):
    """Verify cumulative effects of multiple buys/sells."""
    broker.market_order("buy", 2, 10)
    broker.market_order("buy", 3, 20)
    broker.market_order("sell", 2, 25)
    expected_position = 3
    expected_cash = 1_000 - (2*10 + 3*20) + (2*25)
    assert broker.position == expected_position
    assert broker.cash == pytest.approx(expected_cash)

def test_sell_entire_position_returns_to_zero(broker):
    """Selling full position should zero it out and update cash correctly."""
    broker.market_order("buy", 4, 10)
    broker.market_order("sell", 4, 15)
    assert broker.position == 0
    assert broker.cash == pytest.approx(1_000 + (4 * (15 - 10)))