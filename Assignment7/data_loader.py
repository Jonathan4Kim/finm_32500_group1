import os
from memory_profiler import profile
import pandas as pd
import polars as pl
import timeit


def load_data_pandas():
    path = os.path.join(os.path.dirname(__file__), "market_data-1.csv")
    return pd.read_csv(path, parse_dates=["timestamp"]).sort_values(["symbol", "timestamp"], ignore_index=True)


def load_data_polars():
    path = os.path.join(os.path.dirname(__file__), "market_data-1.csv")
    return pl.read_csv(path, try_parse_dates=True).sort(["symbol", "timestamp"])


# This function is added because adding profile decorator adds overhead that impacts execution speed
@profile
def load_data_pandas_memory_test():
    path = os.path.join(os.path.dirname(__file__), "market_data-1.csv")
    return pd.read_csv(path, parse_dates=["timestamp"]).sort_values(["symbol", "timestamp"], ignore_index=True)


# This function is added because adding profile decorator adds overhead that impacts execution speed
@profile
def load_data_polars_memory_test():
    path = os.path.join(os.path.dirname(__file__), "market_data-1.csv")
    return pl.read_csv(path, try_parse_dates=True).sort(["symbol", "timestamp"])


if __name__ == '__main__':
    print(f"Pandas data import time = {timeit.timeit(load_data_pandas, number=1)}")
    print(f"Polars data import time = {timeit.timeit(load_data_polars, number=1)}")
    load_data_pandas_memory_test()
    load_data_polars_memory_test()
