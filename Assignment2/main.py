from engine import MarketSimulation
from benchmark_strategy import BenchmarkStrategy
from moving_average_strategy import MAC
from volatility_breakout_strategy import VolatilityBreakoutStrategy
from macd_strategy import MACDStrategy
from rsi_strategy import RSIStrategy
from reporting import Reporting
import os


def main():
    # create strategy instantiations
    ma_strategy = MAC(20, 50)
    benchmark_strategy = BenchmarkStrategy()
    rsi_strategy = RSIStrategy()
    macd_strategy = MACDStrategy()
    vol_strategy = VolatilityBreakoutStrategy()

    symbols = [f.replace(".parquet", "") for f in os.listdir("data") if f.endswith(".parquet")]
    strategies = (benchmark_strategy, ma_strategy, vol_strategy, macd_strategy, rsi_strategy)
    new_sim = MarketSimulation(1_000_000, strategies, symbols=symbols)

    new_sim.run_simulation()

    reporter = Reporting(new_sim.NAV_series)
    print(f"Final Cash Balance = ${new_sim.cash_balance:,.2f}")
    print(f"Final NAV = ${new_sim.NAV_series.iloc[-1]:,.2f}")
    print(f"P&L = ${reporter.compute_pnl():,.2f}")
    print(f"Total Return: {reporter.compute_total_return():,.2%}")
    print(f"Sharpe Ratio: {reporter.sharpe_ratio():,.2f}")
    print(f"Max Drawdown: {reporter.max_drawdown():,.2%}")
    reporter.plot_equity_curve()  

if __name__ == "__main__":
    main()