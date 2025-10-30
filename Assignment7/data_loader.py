import cProfile
import pandas as pd
import polars as pl
from memory_profiler import profile

def load_data_pandas():
    df = pd.read_csv("market_data-1.csv", parse_dates=["timestamp"])
    return df

def load_data_polars():
    df = pl.read_csv("market_data-1.csv", try_parse_dates=True)
    return df

# This function is added because adding profile decorator adds overhead that impacts execution speed
@profile
def load_data_pandas_memory():
    df = pd.read_csv("market_data-1.csv", parse_dates=["timestamp"])
    return df

# This function is added because adding profile decorator adds overhead that impacts execution speed
@profile
def load_data_polars_memory():
    df = pl.read_csv("market_data-1.csv", try_parse_dates=True)
    return df


if __name__ == '__main__':
    cProfile.run("load_data_pandas()")
    cProfile.run("load_data_polars()")
    load_data_pandas_memory()
    load_data_polars_memory()
