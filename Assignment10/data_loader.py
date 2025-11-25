import pandas as pd


class DataLoader:
    @staticmethod
    def load_from_csv(market_data_path: str = "data/market_data_multi.csv", tickers_path: str = "data/tickers.csv") -> pd.DataFrame:
        df = pd.read_csv(market_data_path, parse_dates=["timestamp"]).dropna(subset=["timestamp", "open", "high", "low", "close"])

        # Normalize all columns names
        for column in df.columns:
            df.rename(columns={column: column.strip()}, inplace=True)
            df.rename(columns={column: column.replace(" ", "_")}, inplace=True)
            df.rename(columns={column: column.lower()}, inplace=True)

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
    print(df)