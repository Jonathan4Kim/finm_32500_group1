import timeit
from data_loader import load_data_pandas, load_data_polars
import polars as pl


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


def add_rolling_sharpe_pandas(df = add_rolling_std_pandas(add_rolling_mean_pandas(load_data_pandas()))):
    if df is None or "rolling_mean_20" not in df.columns or "rolling_std_20" not in df.columns:
        raise ValueError(f"Missing required columns for rolling Sharpe: rolling_mean_20, rolling_std_20")
    df["rolling_sharpe_20"] = df["rolling_mean_20"] / df["rolling_std_20"]
    return df


def add_rolling_sharpe_polars(df = add_rolling_std_polars(add_rolling_mean_polars(load_data_polars()))):
    if df is None or "rolling_mean_20" not in df.columns or "rolling_std_20" not in df.columns:
        raise ValueError(f"Missing required columns for rolling Sharpe: rolling_mean_20, rolling_std_20")
    df = df.with_columns(
        (pl.col("rolling_mean_20") / pl.col("rolling_std_20"))
        .alias("rolling_sharpe_20")
    )
    return df


if __name__ == "__main__":
    NUMBER = 10
    print("***Means***")
    print(f"Pandas rolling average time = {timeit.timeit(add_rolling_mean_pandas, number=NUMBER)}")
    print(f"Polars rolling average time = {timeit.timeit(add_rolling_mean_polars, number=NUMBER)}")
    print("***Stds***")
    print(f"Pandas rolling stds time = {timeit.timeit(add_rolling_std_pandas, number=NUMBER)}")
    print(f"Polars rolling stds time = {timeit.timeit(add_rolling_std_polars, number=NUMBER)}")
    print("***Sharp Ratios***")
    print(f"Pandas rolling Sharpe ratios time = {timeit.timeit(add_rolling_sharpe_pandas, number=NUMBER)}")
    print(f"Polars rolling Sharpe ratios time = {timeit.timeit(add_rolling_sharpe_polars, number=NUMBER)}")