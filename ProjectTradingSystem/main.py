# main_simulated.py
from collections import defaultdict
from typing import Dict, List, Optional

from gateway import load_market_data
from order import Order
from order_manager import OrderManager
from strategy import (
    MAStrategy,
    MomentumStrategy,
    StatisticalSignalStrategy,
    Signal,
    MarketDataPoint,
)
from risk_engine import RiskEngine


def run_stream():
    """Iterate over live market datapoints from Alpaca Socket Webstream, run all strategies per symbol, and route to OrderManager."""
    risk_engine = RiskEngine(max_order_size=1000, max_position=2000, cash_balance=10000)
    om = OrderManager(risk_engine, simulated=False)

    strategies: Dict[str, List] = defaultdict(list)

    for mdp in load_market_data(simulated=False):
        # Lazily create a set of strategies for each symbol encountered.
        if not strategies[mdp.symbol]:
            strategies[mdp.symbol] = [
                MAStrategy(symbol=mdp.symbol, short_window=3, long_window=5, position_size=10),
                MomentumStrategy(symbol=mdp.symbol, momentum_window=10, momentum_threshold=0.001, position_size=10),
                StatisticalSignalStrategy(symbol=mdp.symbol, lookback_window=20, zscore_threshold=1.5, position_size=10),
            ]

        for strat in strategies[mdp.symbol]:
            signal: Optional[Signal] = strat.on_new_bar(mdp)  # type: ignore[arg-type]
            if not signal:
                continue

            order = Order(
                side=signal.signal.value,
                symbol=signal.symbol,
                qty=strat.get_position_size(),
                price=signal.price,
            )
            result = om.process_order(order)
            print(f"{mdp.symbol} {strat.__class__.__name__} {signal.timestamp.isoformat()} {signal.signal.value} -> {result}")


if __name__ == "__main__":
    run_stream()