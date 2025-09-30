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

Libraries used: pandas (parquetting, dataframe), yfinance ()
"""

import pandas as pd
import yfinance as yf
import time
import requests
import io
import os

class PriceLoader:
    
    @staticmethod
    def get_tickers() -> list[str]:
        """
        Uses requests module to scrape
        tickers for all S&P 500 tickers
        from Wikipedia's website

        Returns:
            list[str]: a list of capital letter tickers
            as stirngs (Ex: "AAPL")
        """
        # get all S&P tickers from today, use headers to avoid 403 Forbidden Errors
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

        # Use Wikipedia's S&P 500 list to get all relevant S&P 500 companies
        response = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", headers=headers)

        # ensure response was successful
        if response.status_code == 200:
            # wrap response's text in io (deprecation issue), then get nested pandas df (index 0), ticker column only
            tickers = pd.read_html(io.StringIO(response.text))[0]["Symbol"].tolist()
        else:
            print(f"Request failed with status code: {response.status_code}")
        print(type(tickers))
        return tickers

    @staticmethod
    def yield_batches(tickers, batch_size=25):
        """
        Generator function that yields tickers
        in batch sizes of 25 (typically) for 
        batching. Will be used for yfinance.
        """
        # yield yfinance data by batches
        for i in range(0, len(tickers), batch_size):
            yield tickers[i: min(i + batch_size, len(tickers))]
    
    
    def save_to_parquet(self):
        """
        Uses ticker values from 
        get_tickers() and then batches
        the tickers from yfinance. Then
        saves it from parquet.
        """
        # create directory
        if not os.path.exists("data/"):
            os.makedirs("data")
        
        # get tickers
        tickers = self.get_tickers()
        
        # create list of concatenated S&P dataframes
        snp_dfs = []

        # batch number for logging
        batch_num = 0
        
        for batch in self.yield_batches(tickers, 25):
            print(f"Downloading batch {batch_num}")
            
            try:
                # get only the closing prices (This is really adjusted close)
                df = yf.download(tickers=batch, start="2005-01-01", end="2025-01-01")["Close"]
                
                # add dataframe to the to-be concatenated dataframe
                snp_dfs.append(df)

                # logging
                print(f"batch {batch_num} complete!")
            except Exception:
                print(f"issue with downloading one of the following tickers: {tickers}")

            batch_num += 1
        print(f"total_batches: {batch_num}")
        snp_dfs = pd.concat(snp_dfs, axis=1)

        # send dataframe to respective parquets
        for ticker in tickers:

            # ensure that there is in fact data for ticker during 2005-2025 before putting into a parquet
            if ticker in snp_dfs.columns:
                # separate df into its own data file as parquets
                ticker_df = snp_dfs.loc[:, [ticker]]
                ticker_df["timestamp"] = ticker_df.index
                ticker_df["symbol"] = ticker
                ticker_df = ticker_df.rename(columns={f"{ticker}": "price"})
                # use ticker for the name
                ticker_df.to_parquet(f"data/{ticker}.parquet")
                print(f"{ticker} parquet created!")

    def __init__(self):
        # log start time
        start = time.time()

        self.save_to_parquet()

        # log end time
        end = time.time()

        # see how long batching took
        print(f"total batching and data loading time took {end - start:0.2f} seconds")

pl = PriceLoader()