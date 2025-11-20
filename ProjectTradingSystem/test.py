import os
import pandas as pd
from strategy import MAStrategy, MomentumStrategy, StatisticalSignalStrategy


def run_test(strategy_class, name, symbol, filepath):
    print(f"\nTesting {name}...")

    if not os.path.exists(filepath):
        print(f"  Error: file not found -> {filepath}")
        print(f"  Current directory: {os.getcwd()}")
        return False

    try:
        # Load data
        data = pd.read_csv(filepath, index_col=0, parse_dates=True)
        print(f"  Loaded {len(data)} rows")

        # Instantiate strategy
        strategy = strategy_class(symbol=symbol, position_size=100)

        # Stream data through strategy bar-by-bar
        signals = []
        for idx, row in data.iterrows():
            signal = strategy.on_new_bar(
                timestamp=idx,
                open_p=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row['Volume']
            )
            if signal:
                signals.append(signal)

        print(f"  Generated {len(signals)} signals")

        # Summary
        buy_count = sum(1 for s in signals if s.signal.value == "BUY")
        sell_count = sum(1 for s in signals if s.signal.value == "SELL")
        summary = {
            "symbol": symbol,
            "strategy": name,
            "total_signals": len(signals),
            "buy_signals": buy_count,
            "sell_signals": sell_count,
        }
        print(f"  Summary: {summary}")

        if signals:
            first = signals[0]
            print(f"  First signal: {first.timestamp} | {first.signal.value} @ {first.price:.2f}")

        return True

    except Exception as e:
        print(f"  Error while running {name}: {e}")
        import traceback
        traceback.print_exc()
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