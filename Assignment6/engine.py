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

def test_engine_runs_and_executes_orders():
    port = PortfolioGroup(name="test_port", owner="eng")
    strat = MeanReversionStrategy({"lookback_window": 1, "threshold": 0.01})
    engine = Engine(strategy=strat, portfolio=port)
    alert_obs = AlertObserver()
    engine.publisher.attach(alert_obs)
    # feed ticks so MR triggers
    t1 = MarketDataPoint(timestamp=datetime(2025, 10, 26), symbol="AAPL", price=100.0)
    t2 = MarketDataPoint(timestamp=datetime(2025, 10, 27), symbol="AAPL", price=2.0)
    executed = engine.on_tick(t1)
    assert executed == []
    executed2 = engine.on_tick(t2)
    # should have executed one buy of 3 shares
    assert executed2 and port.get_positions()
    # observer should have received the signal (threshold==3 so it will alert)
    # undo via engine
    engine.undo_last()
    assert len(port.get_positions()) == 0
    engine.redo_last()
    assert len(port.get_positions()) == 1