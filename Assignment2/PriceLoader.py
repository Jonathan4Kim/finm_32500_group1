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
import requests
import io


class PriceLoader:

    def __init__(self):
        # log start time
        start = time.time()
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
            
        # TODO: Batching
        def yield_batches(tickers, batch_size):
            """
            
            """
            # yield yfinance data by batches
            for i in range(0, len(tickers), batch_size):
                yield tickers[i: min(i + batch_size, len(tickers))]

        # batch number for logging
        batch_num = 0
        # list of batched S&P dataframes that will be appended during batching
        snp_dfs = []


        for batch in yield_batches(tickers, 25):
            print(f"Downloading batch {batch_num}")
            
            # get only the closing prices (This is really adjusted close)
            df = yf.download(tickers=batch, )["Close"]
            
            # add dataframe to the to-be concatenated dataframe
            snp_dfs.append(df)
            
            print(f"batch {batch_num} complete!")

            batch_num += 1
        print(f"total_batches: {batch_num}")
        snp_dfs = pd.concat(snp_dfs, axis=1)


        # send dataframe to respective parquets
        for ticker in tickers:
            # separate df into its own data file as parquets
            ticker_df = snp_dfs.loc[[ticker]]
            # use ticker for the name
            ticker_df.to_parquet(f"data/{ticker}.parquet")

        # log end time
        end = time.time()

        # see how long batching took
        print(f"total batching and data loading time took {end - start:0.2f} seconds")

pl = PriceLoader()