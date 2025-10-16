import pandas as pd
import logging

class Backtester:
    def __init__(self, strategy, broker):
        self.strategy = strategy
        self.broker = broker

    def run(self, prices: pd.Series):
        delayed_signals = self.strategy.signals.shift(1)
        for signal, price in zip(delayed_signals, prices):
            if signal == 1:
                self.broker.market_order(side="buy" , qty=1, price=price)
            elif signal == 0:
                continue
            elif signal == -1:
                self.broker.market_order(side="sell", qty=1, price=price)
            else:
                logging.warning("Engine tried to execute invalid signal value")
