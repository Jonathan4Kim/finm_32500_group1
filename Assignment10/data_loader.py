import pandas as pd
from matplotlib.style.core import available


class DataLoader:
    @staticmethod
    def load_from_csv(market_data_path: str = "data/market_data_multi.csv", tickers_path: str = "data/tickers.csv") -> pd.DataFrame:
        df = pd.read_csv(market_data_path, parse_dates=["timestamp"]).dropna()


        # Check if all tickers listed in tickers.csv are present
        tickers_df = pd.read_csv(tickers_path)
        tickers = tickers_df["symbol"].to_list()
        available_tickers = set(df["ticker"].to_list())
        for ticker in tickers:
            if ticker not in available_tickers:
                raise ValueError(f"Ticker \"{ticker}\" is not available in this dataset.")



        return df

if __name__ == "__main__":
    df = DataLoader.load_from_csv()