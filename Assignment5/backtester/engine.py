import pandas as pd
import logging

class Backtester:
    def __init__(self, strategy, broker):
        self.strategy = strategy
        self.broker = broker

    def run(self, prices: pd.Series):
        if prices is None:
            raise ValueError("Price DataFrame is required but was None.")

        if  self.strategy.signals is None:
            raise ValueError("Strategy signals are required but was None.")

        delayed_signals = self.strategy.signals.shift(1).fillna(0)
        for signal, price in zip(delayed_signals, prices):
            if signal == 1:
                self.broker.market_order(side="buy" , qty=1, price=price)
            elif signal == 0:
                continue
            elif signal == -1:
                self.broker.market_order(side="sell", qty=1, price=price)
            else:
                raise ValueError("Invalid signal.")
