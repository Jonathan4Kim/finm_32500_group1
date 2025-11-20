# main.py
from typing import Optional

from gateway import load_market_data
from order import Order
from order_manager import OrderManager
from strategy import MAStrategy, Signal, MarketDataPoint
from risk_engine import RiskEngine


def process_stream():
    """Iterate over market data, generate strategy signals, and route to OrderManager."""
    strategy = MAStrategy(symbol="AAPL", short_window=3, long_window=5, position_size=10)
    risk_engine = RiskEngine(max_order_size=1000, max_position=2000, cash_balance=10000)
    om = OrderManager(risk_engine)

    for mdp in load_market_data():
        if mdp.symbol != strategy.symbol:
            continue

        signal: Optional[Signal] = strategy.on_new_bar(mdp)
        if not signal:
            continue

        order = Order(
            side=signal.signal.value,
            symbol=signal.symbol,
            qty=strategy.get_position_size(),
            price=signal.price,
        )
        result = om.process_order(order)
        print(f"{signal.timestamp.isoformat()} {signal.signal.value} -> {result}")

    om.save_orders_to_csv()


if __name__ == "__main__":
    process_stream()
