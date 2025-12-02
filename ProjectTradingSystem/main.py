# main_simulated.py
from collections import defaultdict
from typing import Dict, List, Optional

from alpaca.trading.client import TradingClient
from alpaca_env_util import load_keys

from gateway import load_market_data
from order import OrderBuilder
from order_manager import OrderManager
from strategy import (
    MAStrategy,
    MomentumStrategy,
    StatisticalSignalStrategy,
    Signal,
    MarketDataPoint,
)
from risk_engine import RiskEngineLive


def run_stream():
    """Iterate over live market datapoints from Alpaca Socket Webstream, run all strategies per symbol, and route to OrderManager."""
    api_key, api_secret = load_keys()
    trading_client = TradingClient(api_key, api_secret, paper=True)
    
    risk_engine = RiskEngineLive(max_order_value=10000 , max_asset_percentage=0.10)
    om = OrderManager(trading_client, risk_engine, simulated=False)

    ob = OrderBuilder(trading_client)

    strategies: Dict[str, List] = defaultdict(list)

    for mdp in load_market_data(simulated=False):
        # Lazily create a set of strategies for each symbol encountered.
        if not strategies[mdp.symbol]:
            strategies[mdp.symbol] = [
                MAStrategy(symbol=mdp.symbol, short_window=5, long_window=10),
                MomentumStrategy(symbol=mdp.symbol, momentum_window=10, momentum_threshold=0.001),
                StatisticalSignalStrategy(symbol=mdp.symbol, lookback_window=10, zscore_threshold=1.5),
            ]

        # Checks the signal for each strategy given the new data
        signals = []
        for strat in strategies[mdp.symbol]:
            signal = strat.on_new_bar(mdp)
            if signal:
                signals.append(signal)
                print(f"New signal: {mdp.symbol} {strat.__class__.__name__} {signal.signal.value}")

        # Ensures all signals match direction
        signals_match = True
        for i in range(len(signals) - 1):
            if signals[i].signal.value != signals[i+1].signal.value:
                signals_match = False
                break
        if not signals_match:
            print("Signals do not all match")
            continue

        # Gets the agreed signal if possible
        if signals:
            agreed_signal = signals[0]
        else:
            continue

        print(f"New agreed signal: {mdp.symbol} {agreed_signal.timestamp.isoformat()} {agreed_signal.signal.value}")
        order = ob.build_order(agreed_signal)

        result = om.process_order(order)
        print(f"{mdp.symbol} {agreed_signal.timestamp.isoformat()} {agreed_signal.signal.value} -> {result}")


if __name__ == "__main__":
    run_stream()