"""

data_loader.py

Responsible for loading the datapoints using the
get_datapoints() method. Utilizes frozen class
MarketDataPoint to store each row of each ticker from the data/ file
into its own instance, conglomerating them into 
a list to be returned by the function

"""

# imports
import csv
from datetime import datetime
from models import MarketDataPoint
import os
import pandas as pd


def load_data(tickers=None):
    """
    Gets the datapoints from a pa
    and for each row,
    converts each part of the row into its respective 
    datatype for the MarketDataPoint object.
    stores all of those instances into the 
    data_points array to be returned
l
    Returns:
        _type_: _description_
    """
    # create market dataframe
    # print("Loading data...")
    # market_data_df = pd.DataFrame()
    # for _, _, paths in os.walk("data/"):
    #     for path in paths:
    #         if tickers is not None and path.replace(".parquet", "") not in tickers:
    #             continue
    #         df = pd.read_parquet(f"data/{path}")
    #         market_data_df = market_data_df.join(df, how="outer")
    # print("Data loaded...")
    # return

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