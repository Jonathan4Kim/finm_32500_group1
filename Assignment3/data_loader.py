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
    
    Runtime Complexity: O(n)
    
    Space Complexity: O(n): with n MarketDataPoints being created (O(1) time to create each object with 3 attributes)
    from n rows. We add it to data points list, which takes O(1) time amortized in Python.
    """
    # create data point storage  O(1)
    data_points = []

    # open the csv file O(1)
    with open('market_data.csv', newline="") as csvfile:
        # create a reader using csv import for iteration O(1)
        reader = csv.reader(csvfile)
        # move to the next line to avoid column headers (which should be ignored) O(1)
        header = next(reader)

        # for each non-header row O(n)
        for row in reader:
            # convert strings of timestamp, symbol, price O(1)a initialization and saving to memory
            timestamp, symbol, price = datetime.strptime(row[0], "%Y-%m-%dT%H:%M:%S.%f"), row[1], float(row[2])
            # create new frozen MarketDataPoint instance
            mdp = MarketDataPoint(timestamp, symbol, price)
            # append data_points with the new MarketDataPoint instance O(1) time amortized
            data_points.append(mdp)

        # total runtime: O(n) for the big iteration.
        return data_points