import timeit
import pandas as pd
import polars as pl
from memory_profiler import profile

def load_data_pandas():
    return pd.read_csv("market_data-1.csv", parse_dates=["timestamp"]).sort_values(["symbol", "timestamp"], ignore_index=True)


def load_data_polars():
    return pl.read_csv("market_data-1.csv", try_parse_dates=True).sort(["symbol", "timestamp"])


# This function is added because adding profile decorator adds overhead that impacts execution speed
@profile
def load_data_pandas_memory():
    return pd.read_csv("market_data-1.csv", parse_dates=["timestamp"])


# This function is added because adding profile decorator adds overhead that impacts execution speed
@profile
def load_data_polars_memory():
    return pl.read_csv("market_data-1.csv", try_parse_dates=True)


if __name__ == '__main__':
    print(f"Pandas data import time = {timeit.timeit(load_data_pandas, number=1)}")
    print(f"Polars data import time = {timeit.timeit(load_data_polars, number=1)}")
    load_data_pandas_memory()
    load_data_polars_memory()
