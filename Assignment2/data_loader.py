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


def load_data():
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
    # create
    all_data_points = {}
    for _, _, paths in os.walk("data/"):
        for path in paths:
            df = pd.read_parquet(f"data/{path}")
            data_points = []
            for _, row in df.iterrows():
                timestamp, symbol, price = row["timestamp"], row["symbol"], row["price"]
                # create new frozen MarketDataPoint instance
                mdp = MarketDataPoint(timestamp, symbol, price)
                # append data_points with the new MarketDataPoint instance
                data_points.append(mdp)
            name = path.split(".")[0]
            print(name)
            all_data_points[name] = mdp
            print(f"{path} loaded!")
    print(all_data_points)
    return all_data_points

load_data()