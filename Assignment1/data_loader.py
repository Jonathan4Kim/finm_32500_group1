"""

data_loader.py

Responsible for loading the datapoints using the
get_datapoints() method. Utilizes frozen class
MarketDataPoint to store each row of the market_data.csv
into its own instance, conglomerating them into 
a list to be returned by the function

"""

# imports
import csv
from datetime import datetime
from models import MarketDataPoint


def load_data():
    """
    Gets the datapoints from market_data.csv,
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
    data_points = []

    # open the csv file
    with open('market_data.csv', newline="") as csvfile:
        # create a reader using csv import for iteration
        reader = csv.reader(csvfile)
        # move to the next line to avoid column headers (which should be ignored)
        header = next(reader)

        # for each non-header row
        for row in reader:
            # convert strings of timestamp, symbol, price
            timestamp, symbol, price = datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%S.%f"), row[1], float(row[2])
            # create new frozen MarketDataPoint instance
            mdp = MarketDataPoint(timestamp, symbol, price)
            # append data_points with the new MarketDataPoint instance
            data_points.append(mdp)
        return data_points