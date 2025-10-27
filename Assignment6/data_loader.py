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
from Assignment6.patterns.adapter import YahooFinanceAdapter, BloombergXMLAdapter


def load_data():
    yahoo_adapter = YahooFinanceAdapter("external_data_yahoo.json")
    bloomberg_adapter = BloombergXMLAdapter("external_data_bloomberg.xml")

    # Example: Ingest both
    yahoo_data = yahoo_adapter.get_data("AAPL")
    bloomberg_data = bloomberg_adapter.get_data("MSFT")

    data_points = [yahoo_data] + [bloomberg_data]
    return data_points