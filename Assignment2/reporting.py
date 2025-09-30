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