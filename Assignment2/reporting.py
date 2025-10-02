"""
reporting.py

This module defines the `Reporting` class, which provides a suite of performance analytics
tools for analyzing the equity curve (cumulative portfolio value over time) of a trading strategy
or investment portfolio.

The class accepts a pandas Series `equity_curve` indexed by datetime, and includes methods to compute:

- Total profit and loss (PnL)
- Total return over the period
- Periodic returns (e.g., daily, monthly)
- Sharpe ratio (risk-adjusted return)
- Maximum drawdown (largest peak-to-trough decline)
- Equity curve plotting

Typical usage:

    from reporting import Reporting

    report = Reporting(equity_curve)
    print("PnL:", report.compute_pnl())
    print("Sharpe Ratio:", report.sharpe_ratio())
    report.plot_equity_curve()

Methods:
    - compute_pnl(): Return total profit/loss over the equity curve.
    - compute_total_return(): Return cumulative return as a percentage.
    - periodic_return(period='D'): Return periodic percentage changes (daily, monthly, etc.).
    - sharpe_ratio(risk_free_rate=0.0, periods_per_year=252): Return annualized Sharpe ratio.
    - max_drawdown(): Return the largest observed drawdown.
    - plot_equity_curve(title="Equity Curve"): Display a matplotlib plot of the equity curve.

"""

import numpy as np
import matplotlib.pyplot as plt


class Reporting:
    def __init__(self, equity_curve):
        self.equity_curve = equity_curve

    def compute_pnl(self):
        return self.equity_curve.iloc[-1] - self.equity_curve.iloc[0] if not self.equity_curve.empty else 0
    
    def compute_total_return(self):
        return (self.equity_curve.iloc[-1] / self.equity_curve.iloc[0]) - 1 if not self.equity_curve.empty else 0
        
    def periodic_return(self, period='D'):
        # returns resampled periodic returns, e.g., daily ('D') or monthly ('M')
        return self.equity_curve.resample(period).last().pct_change()

    def sharpe_ratio(self, risk_free_rate=0.0, periods_per_year=252):
        returns = self.equity_curve.pct_change().dropna()
        if len(returns) == 0:
            return 0.0
        excess_returns = returns - risk_free_rate / periods_per_year
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(periods_per_year)

    def max_drawdown(self):
        cum_max = self.equity_curve.cummax()
        drawdown = (self.equity_curve - cum_max) / cum_max
        return drawdown.min()

    def plot_equity_curve(self, title="Equity Curve"):
        plt.figure(figsize=(10, 6))
        plt.plot(self.equity_curve.index, self.equity_curve.values, label="Equity Curve")
        plt.title(title)
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value")
        plt.legend()
        plt.grid(True)
        plt.show()