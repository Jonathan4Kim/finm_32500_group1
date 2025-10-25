from data_loader import load_data
from broker import Broker
from strategy import VolatilityBreakoutStrategy
from engine import Backtester

def main():
    data = load_data()

    # Run Backtest
    strategy = VolatilityBreakoutStrategy()
    signals = strategy.generate_signals(data)
    broker = Broker()
    bt = Backtester(strategy, broker)
    equity = bt.run(data)

    print(f"Final equity: {equity:.2f}")


if __name__ == "__main__":
    main()