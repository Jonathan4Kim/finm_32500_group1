import os
from strategy import MAStrategy, MomentumStrategy, StatisticalSignalStrategy


def run_test(strategy_class, name, symbol, filepath):
    print(f"\nTesting {name}...")

    if not os.path.exists(filepath):
        print(f"  Error: file not found -> {filepath}")
        print(f"  Current directory: {os.getcwd()}")
        return False

    try:
        strategy = strategy_class(symbol=symbol, position_size=100)

        data = strategy.load_data(filepath)
        print(f"  Loaded {len(data)} rows")

        signals = strategy.generate_signals()
        print(f"  Generated {len(signals)} signals")

        summary = strategy.summary()
        print(f"  Summary: {summary}")

        if signals:
            first = signals[0]
            print(f"  First signal: {first.timestamp} | {first.signal.value} @ {first.price}")

        return True

    except Exception as e:
        print(f"  Error while running {name}: {e}")
        return False


def main():
    data_path = "ProjectTradingSystem/data"
    symbol = "AAPL"
    csv_path = f"{data_path}/{symbol}.csv"

    tests = [
        (MAStrategy, "MA Crossover", symbol, csv_path),
        (MomentumStrategy, "Momentum", symbol, csv_path),
        (StatisticalSignalStrategy, "Statistical", symbol, csv_path),
    ]

    for strat, name, sym, path in tests:
        run_test(strat, name, sym, path)


if __name__ == "__main__":
    main()
