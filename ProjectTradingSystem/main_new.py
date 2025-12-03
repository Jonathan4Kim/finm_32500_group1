# main_simulated.py
from collections import defaultdict
from typing import Dict, List, Optional

from alpaca.trading.client import TradingClient
from alpaca_env_util import load_keys

from gateway import load_market_data
from order import OrderBuilder
from order_manager import OrderManager
from strategy import MarketDataPoint
from risk_engine import RiskEngineLive
from symbol_state import SymbolState
from config.stocks import STOCKS
from config.crypto import CRYPTO

SYMBOLS = STOCKS + CRYPTO

# Create all symbol states from config file
symbol_states = {
    sym: SymbolState(sym)
    for sym in SYMBOLS
}

def on_market_data(mdp: MarketDataPoint):
    if mdp.symbol not in symbol_states:
        return None

    state = symbol_states[mdp.symbol]
    regime, signal = state.update_state(mdp.price, mdp.timestamp)

    if regime == "WARMING":
        if state.bars_seen % 5 == 0:  # only log every 5 bars to reduce spam
            print(f"[{mdp.symbol}] Warming up: {state.bars_seen}/{state.warmup_bars}")
    else:
        print(f"Regime: {regime} detected for {mdp.symbol} at {mdp.timestamp}")
        print(f"Signal: {signal}")

    return signal

def run_stream():
    """Iterate over live market datapoints from Alpaca Socket Webstream, run all strategies per symbol, and route to OrderManager."""
    api_key, api_secret = load_keys()
    trading_client = TradingClient(api_key, api_secret, paper=True)
    
    risk_engine = RiskEngineLive(max_order_value=10000 , max_asset_percentage=0.10)
    om = OrderManager(trading_client, risk_engine, simulated=False)

    ob = OrderBuilder(trading_client)

    for mdp in load_market_data(simulated=False):
        signal = on_market_data(mdp)
        
        if signal is None:
            continue

        order = ob.build_order(signal)
        if order is None:
            continue

        result = om.process_order(order)
        print(result)


if __name__ == "__main__":
    run_stream()