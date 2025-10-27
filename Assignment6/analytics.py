# analytics.py
from abc import ABC, abstractmethod
import numpy as np
from typing import List, Optional
from Assignment6.patterns.factory import Stock, Bond, ETF, Instrument

# -------------------------------
# Decorator Base Class
# -------------------------------
class InstrumentDecorator(Instrument):
    """Abstract decorator wrapping an Instrument object."""

    def __init__(self, instrument: Instrument):
        # We intentionally do NOT call Instrument.__init__ because we delegate attributes.
        self._instrument = instrument

    # Delegate attribute access to the wrapped instrument so decorators behave like the instrument.
    def __getattr__(self, name):
        # Called only if attribute not found on self; forward to wrapped instrument.
        return getattr(self._instrument, name)

    # Optionally expose common attributes explicitly to avoid magic for linters/tests:
    @property
    def symbol(self):
        return self._instrument.symbol

    @property
    def prices(self):
        return self._instrument.prices

    @abstractmethod
    def get_metrics(self) -> dict:
        pass


# -------------------------------
# Concrete Decorators
# -------------------------------
class VolatilityDecorator(InstrumentDecorator):
    """Adds historical volatility metric."""
    def get_metrics(self) -> dict:
        metrics = self._instrument.get_metrics()
        prices = np.asarray(self.prices, dtype=float)
        if len(prices) > 1:
            returns = np.diff(prices) / prices[:-1]
            # annualize assuming 252 trading days
            volatility = float(np.std(returns, ddof=0) * np.sqrt(252))
        else:
            volatility = 0.0
        metrics["volatility"] = round(volatility, 6)
        return metrics


class BetaDecorator(InstrumentDecorator):
    """Adds beta metric relative to a benchmark."""
    def __init__(self, instrument: Instrument, benchmark_prices: Optional[List[float]] = None):
        super().__init__(instrument)
        self.benchmark_prices = benchmark_prices

    def get_metrics(self) -> dict:
        metrics = self._instrument.get_metrics()
        if self.benchmark_prices is None:
            metrics["beta"] = "N/A"
            return metrics

        # Align lengths (use the shortest common window)
        inst_prices = np.asarray(self.prices, dtype=float)
        bench_prices = np.asarray(self.benchmark_prices, dtype=float)
        n = min(len(inst_prices), len(bench_prices))
        if n <= 1:
            metrics["beta"] = "N/A"
            return metrics

        inst_returns = np.diff(inst_prices[-n:]) / inst_prices[-n:-1]
        bench_returns = np.diff(bench_prices[-n:]) / bench_prices[-n:-1]

        # If bench_returns variance is zero, beta undefined
        var_bench = np.var(bench_returns, ddof=0)
        if var_bench == 0:
            metrics["beta"] = "N/A"
            return metrics

        cov = np.cov(inst_returns, bench_returns, ddof=0)[0, 1]
        beta = float(cov / var_bench)
        metrics["beta"] = round(beta, 6)
        return metrics


class DrawdownDecorator(InstrumentDecorator):
    """Adds maximum drawdown metric."""
    def get_metrics(self) -> dict:
        metrics = self._instrument.get_metrics()
        prices = np.asarray(self.prices, dtype=float)
        if prices.size == 0:
            metrics["max_drawdown"] = 0.0
            return metrics

        running_max = np.maximum.accumulate(prices)
        drawdowns = (prices - running_max) / running_max
        max_drawdown = float(np.min(drawdowns))
        metrics["max_drawdown"] = round(max_drawdown, 6)
        return metrics


# -------------------------------
# Demonstration of Stacked Decorators
# -------------------------------
if __name__ == "__main__":
    np.random.seed(0)
    stock_prices = 100 + np.cumsum(np.random.randn(252))  # Simulated daily prices
    benchmark_prices = 100 + np.cumsum(np.random.randn(252))

    stock = Stock("AAPL", stock_prices.tolist())

    # Stack decorators dynamically (Volatility -> Beta -> Drawdown)
    decorated = DrawdownDecorator(
        BetaDecorator(
            VolatilityDecorator(stock),
            benchmark_prices=benchmark_prices.tolist()
        )
    )

    print("Instrument Analytics:")
    print(decorated.get_metrics())
