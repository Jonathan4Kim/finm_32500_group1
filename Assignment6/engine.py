from datetime import datetime

from Assignment6.patterns.strategy import Strategy, MeanReversionStrategy
from Assignment6.patterns.observer import SignalPublisher, AlertObserver
from Assignment6.patterns.command import CommandInvoker, ExecuteOrderCommand
from Assignment6.models import PortfolioGroup
from Assignment6.models import MarketDataPoint


class Engine:
    def __init__(self, strategy: Strategy, portfolio: PortfolioGroup):
        self.strategy = strategy
        self.portfolio = portfolio
        self.publisher = SignalPublisher()
        self.invoker = CommandInvoker()
        # observers can attach to publisher externally

    def on_tick(self, tick):
        """Process a single tick: generate signals, notify observers, and execute orders."""
        signals = self.strategy.generate_signals(tick)
        for sig in signals:
            # Normalize/augment the signal
            sig = dict(sig)
            sig.setdefault("reason", type(self.strategy).__name__)
            # notify observers about the generated signal
            self.publisher.notify(sig)
            # create a command to execute the trade
            cmd = ExecuteOrderCommand(portfolio=self.portfolio, signal=sig)
            self.invoker.execute_command(cmd)
        return self.invoker.history

    def undo_last(self):
        return self.invoker.undo()

    def redo_last(self):
        return self.invoker.redo()