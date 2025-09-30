from engine import MarketSimulation
from benchmark_strategy import BenchmarkStrategy
from moving_average_strategy import MAC
from volatility_breakout_strategy import VolatilityBreakoutStrategy
from macd_strategy import MACDStrategy
from rsi_strategy import RSIStrategy
from reporting import Reporting
import pprint

def main():
    # create strategy instantiations
    ma_strategy = MAC(20, 50)
    benchmark_strategy = BenchmarkStrategy()
    rsi_strategy = RSIStrategy()
    macd_strategy = MACDStrategy()
    vol_strategy = VolatilityBreakoutStrategy()
    
    
    # strategies = (benchmark_strategy, ma_strategy, vol_strategy, macd_strategy, rsi_strategy)
    strategies = [ma_strategy]
    new_sim = MarketSimulation(1_000_000, strategies, symbols=["AAPL", "NVDA"])

    new_sim.run_simulation()

    reporter = Reporting(new_sim.NAV_series)
    print(f"Final Cash Balance = {new_sim.cash_balance}")
    print(f"P&L = {reporter.compute_pnl()}")
    print("Total Return:", reporter.compute_total_return())
    print("Sharpe Ratio:", reporter.sharpe_ratio())
    print("Max Drawdown:", reporter.max_drawdown())

    reporter.plot_equity_curve()  

if __name__ == "__main__":
    main()