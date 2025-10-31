import timeit
from data_loader import load_data_pandas, load_data_polars
import matplotlib.pyplot as plt
import polars as pl

NUMBER = 20


def add_rolling_mean_pandas(df = load_data_pandas()):
    if df is None or "symbol" not in df.columns or "price" not in df.columns:
        raise ValueError(f"Missing required columns for rolling mean: symbol, price")
    df["rolling_mean_20"] = df.groupby("symbol").rolling(20)["price"].mean().reset_index(drop=True)
    return df


def add_rolling_mean_polars(df = load_data_polars()):
    if df is None or "symbol" not in df.columns or "price" not in df.columns:
        raise ValueError(f"Missing required columns for rolling mean: symbol, price")
    df = df.with_columns(
        pl.col("price")
        .rolling_mean(window_size=20)
        .over("symbol")
        .alias("rolling_mean_20")
    )
    return df


def add_rolling_std_pandas(df = load_data_pandas()):
    if df is None or "symbol" not in df.columns or "price" not in df.columns:
        raise ValueError(f"Missing required columns for rolling std: symbol, price")
    df["rolling_std_20"] = (
        df.groupby("symbol")["price"]
        .rolling(20)
        .std()
        .reset_index(level=0, drop=True)
    )
    return df


def add_rolling_std_polars(df = load_data_polars()):
    if df is None or "symbol" not in df.columns or "price" not in df.columns:
        raise ValueError(f"Missing required columns for rolling std: symbol, price")
    df = df.with_columns(
            pl.col("price")
            .rolling_std(window_size=20)
            .over("symbol")
            .alias("rolling_std_20")
        )
    return df


def add_rolling_sharpe_pandas(df = load_data_pandas()):
    if df is None or "symbol" not in df.columns or "price" not in df.columns:
        raise ValueError(f"Missing required columns for rolling Sharpe: symbol, price")

    grouped_prices = df.groupby("symbol")["price"]
    df[f"rolling_sharpe_20"] = grouped_prices.transform(
        lambda x: (
                (x.pct_change())
                .rolling(20)
                .mean()
                /
                (x.pct_change())
                .rolling(20)
                .std()
        )
    )
    return df


def add_rolling_sharpe_polars(df = load_data_polars()):
    if df is None or "symbol" not in df.columns or "price" not in df.columns:
        raise ValueError(f"Missing required columns for rolling Sharpe: symbol, price")
    df = (
        df.group_by("symbol", maintain_order=True)
        .map_groups(
            lambda group: group.with_columns([
                ((group["price"] / group["price"].shift(1) - 1)
                 .rolling_mean(20)
                 / (group["price"] / group["price"].shift(1) - 1)
                 .rolling_std(20))
                .alias(f"rolling_sharpe_20")
            ])
        )
    )
    return df

def benchmark_functions():
    results = {
        "Rolling Mean": {
            "Pandas": timeit.timeit(add_rolling_mean_pandas, number=NUMBER),
            "Polars": timeit.timeit(add_rolling_mean_polars, number=NUMBER),
        },
        "Rolling Std": {
            "Pandas": timeit.timeit(add_rolling_std_pandas, number=NUMBER),
            "Polars": timeit.timeit(add_rolling_std_polars, number=NUMBER),
        },
        "Rolling Sharpe": {
            "Pandas": timeit.timeit(add_rolling_sharpe_pandas, number=NUMBER),
            "Polars": timeit.timeit(add_rolling_sharpe_polars, number=NUMBER),
        },
    }
    return results


def plot_benchmark(results):
    # Extract data for plotting
    metrics = list(results.keys())
    pandas_times = [results[m]["Pandas"] for m in metrics]
    polars_times = [results[m]["Polars"] for m in metrics]

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(metrics))
    width = 0.35

    # Bars
    ax.bar([i - width/2 for i in x], pandas_times, width, label="Pandas", color="#1f77b4")
    ax.bar([i + width/2 for i in x], polars_times, width, label="Polars", color="#ff7f0e")

    # Labels
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=12)
    ax.set_ylabel("Execution Time (seconds)", fontsize=12)
    ax.set_title(f"Pandas vs Polars Rolling Computation Performance (trails={NUMBER})", fontsize=14, pad=10)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.6)

    # Annotate bars
    for i, v in enumerate(pandas_times):
        ax.text(i - width/2, v + 0.001, f"{v:.3f}", ha="center", fontsize=10)
    for i, v in enumerate(polars_times):
        ax.text(i + width/2, v + 0.001, f"{v:.3f}", ha="center", fontsize=10)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    results = benchmark_functions()
    print(f"\n*** Benchmark Results (trails={NUMBER})***")
    for metric, vals in results.items():
        print(f"{metric}: Pandas={vals['Pandas']:.6f}s, Polars={vals['Polars']:.6f}s")

    # Plot the results
    plot_benchmark(results)