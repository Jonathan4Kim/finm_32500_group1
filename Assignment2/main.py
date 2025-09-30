from engine import MarketSimulation
from BenchmarkStrategy import BenchmarkStrategy
from MovingAverageStrategy import MAC
from VolatilityBreakoutStrategy import VolatilityBreakoutStrategy
from MACDStrategy import MACDStrategy
from RSIStrategy import RSIStrategy
from reporting import Reporting
import pprint

def main():
    # create strategy instantiations
    ma_strategy = MAC(20, 50)
    benchmark_strategy = BenchmarkStrategy()
    rsi_strategy = RSIStrategy()
    macd_strategy = MACDStrategy()
    vol_strategy = VolatilityBreakoutStrategy()
    
    
    strategies = (benchmark_strategy, ma_strategy, vol_strategy, macd_strategy, rsi_strategy)
    new_sim = MarketSimulation(1_000_000, strategies)

    nav_series = new_sim.run_simulation()
    pprint.pprint(new_sim.portfolio)
    print(f"P&L = {new_sim.cash_balance}")
    # TOTAL TIME: 0.250867

    reporter = Reporting(nav_series)  # <-- pass it here
    print("Total Return:", reporter.compute_total_return())
    print("Sharpe Ratio:", reporter.sharpe_ratio())
    print("Max Drawdown:", reporter.max_drawdown())

    reporter.plot_equity_curve()  

if __name__ == "__main__":
    main()