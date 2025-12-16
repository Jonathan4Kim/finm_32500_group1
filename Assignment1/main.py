from engine import MarketSimulation
from strategies import *
from reporting import Reporting
import pprint

def main():
    mac_strategy = MAC(2, 5)
    momentum_strategy = Momentum()
    strategies = (mac_strategy, momentum_strategy)
    new_sim = MarketSimulation(10_000, strategies)

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