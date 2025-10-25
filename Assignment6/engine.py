import logging

class Backtester:
    def __init__(self, strategy, broker):
        self.strategy = strategy
        self.broker = broker

    def run(self, data):
        if data is None or len(data) == 0:
            raise ValueError("Market data is required but was empty or None.")

        if getattr(self.strategy, "signals", None) is None:
            raise ValueError("Strategy signals are required but were None.")

        prices = [d.price for d in data]
        delayed_signals = self.strategy.signals.shift(1).fillna(0)

        if len(delayed_signals) != len(prices):
            raise ValueError("Signal length does not match data length.")

        logging.info("Starting backtest...")
        for signal, point in zip(delayed_signals, data):
            if signal == 1:
                self.broker.market_order(side="buy", qty=1, price=point.price)
                logging.debug(f"BUY {point.symbol} @ {point.price}")
            elif signal == -1:
                self.broker.market_order(side="sell", qty=1, price=point.price)
                logging.debug(f"SELL {point.symbol} @ {point.price}")
            elif signal == 0:
                continue
            else:
                raise ValueError(f"Invalid signal value: {signal}")

        logging.info("Backtest completed.")
        return self.broker.get_equity(prices[-1])