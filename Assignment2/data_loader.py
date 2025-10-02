"""
data_loader.py

This module provides functionality for loading individual stock data files (in Parquet format)
from the "data/" directory and combining them into a single pandas DataFrame with a MultiIndex
column structure.

Each file is expected to contain time-indexed data for a single ticker, with columns such as
"Close", "Volume", etc. The columns are re-labeled during loading so that the final DataFrame
has a MultiIndex with two levels:
    - Level 0: Data field (e.g., "Close", "Volume")
    - Level 1: Ticker symbol (e.g., "AAPL", "MSFT")

Example column structure:
    ('Close', 'AAPL'), ('Volume', 'AAPL'), ('Close', 'MSFT'), ...

Function:
    load_data(tickers=None)
        Loads data for the specified tickers (or all if None), merges into a single DataFrame,
        and returns it.

Example usage:
    df = load_data(tickers=["AAPL", "NVDA"])
    prices = df["Close"]
    volumes = df["Volume"]
"""

import os
import pandas as pd


def load_data(tickers=None):
    print("Loading data...")
    data_frames = []
    for _, _, paths in os.walk("data/"):
        for path in paths:
            if not path.endswith(".parquet"):
                continue

            ticker = path.replace(".parquet", "")

            # Skip if tickers are specified and this one isn't in the list
            if tickers is not None and ticker not in tickers:
                continue

            df = pd.read_parquet(os.path.join("data/", path))

            # Add a MultiIndex to columns: (field, ticker)
            df.columns = pd.MultiIndex.from_product([df.columns, [ticker]])

            data_frames.append(df)

    # Combine all the DataFrames on the index
    if data_frames:
        market_data_df = pd.concat(data_frames, axis=1)
    else:
        market_data_df = pd.DataFrame()

    print("Data loaded...")
    return market_data_df

if __name__ == "__main__":
    print(load_data(tickers=["AAPL", "NVDA"]))