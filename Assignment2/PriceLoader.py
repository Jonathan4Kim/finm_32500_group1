"""
PriceLoader.py

Responsible for using yfinance to to download 
daily adjusted close prices for all S&P 500 tickers 
(use the list of S&P 500 tickers from today, do not go back point-in-time. 
i.e some of the tickers you have today won't be 
the same as the real ones from 2015 - it doesn't matter)

Time range: January 1, 2005 to January 1, 2025

Data will be:
1. stored locally using parquets
2. implemented using PriceLoader class to manage access
3. API limits with batching
4. Tickers will be dropped with sparse or missing data

Libraries used: TODO
"""
import pandas as pd
import yfinance as yf
import time


class PriceLoader:
    
    def __init__(self):
        # start time
        start = time.time()
        # get all S&P tickers from today (how do we do that?)
        # we can get the S&P using ^GSPC, but we need each of their tickers
            # get each of their tickers, if they're sparse/not a lot of data, drop ticker
            # save to a directory, data
        # download data from historial price data, getting only adj Close
        data = yf.download(tickers="", start="2005-01-01", end="2025-01-01", keepna=False, )["Close"]
        # calculate end time to understand batching time
        end = time.time()
        
        # send dataframe to parquet
        data.to_parquet(engine="pyarrow")
        # see how long batching took
        print(f"total batching and data loading time took {end - start:0.2f} seconds")
        pass