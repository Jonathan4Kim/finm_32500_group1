import timeit
from data_loader import load_data_pandas, load_data_polars
import polars as pl


def add_rolling_mean_pandas():
    # return load_data_pandas().groupby("symbol").rolling(20)["price"].mean()
    df = load_data_pandas()
    df["rolling_mean_20"] = df.groupby("symbol").rolling(20)["price"].mean().reset_index(drop=True)
    return df


def add_rolling_mean_polars():
    df = load_data_polars()
    df = df.with_columns(
        pl.col("price")
        .rolling_mean(window_size=20)
        .over("symbol")
        .alias("rolling_mean_20")
    )
    return df


if __name__ == "__main__":
    print(f"Pandas rolling average time = {timeit.timeit(add_rolling_mean_pandas, number=1)}")
    print(f"Polars rolling average time = {timeit.timeit(add_rolling_mean_polars, number=1)}")