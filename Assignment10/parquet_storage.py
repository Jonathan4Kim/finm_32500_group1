import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from data_loader import DataLoader as dl


class ParquetStorage:
    @staticmethod
    def convert_to_parquet(save_root="market_data"):
        df = dl.load_from_csv()
        table = pa.Table.from_pandas(df)

        pq.write_to_dataset(
            table,
            root_path=save_root,
            partition_cols=["ticker"],
            existing_data_behavior="delete_matching"  # replace partitions to avoid duplicates
        )


    @staticmethod
    def load_ticker_parquet(ticker: str, start:str =None , end: str=None, root: str="market_data") -> pd.DataFrame:
        # Load only the partition for this ticker
        path = f"{root}/ticker={ticker}"

        df = pd.read_parquet(path)

        # Optional date filtering
        if start:
            df = df[df["timestamp"] >= pd.to_datetime(start)]
        if end:
            df = df[df["timestamp"] <= pd.to_datetime(end)]

        return df.sort_values("timestamp")


    @staticmethod
    def compute_rolling_volatility(ticker: str) -> pd.DataFrame:
        df = ParquetStorage.load_ticker_parquet(ticker)[["timestamp", "close"]]
        df.sort_values("timestamp", inplace=True)
        df["returns"] = df["close"].pct_change()
        df["vol_5"] = df["returns"].rolling(5, min_periods=0).std()
        return df.drop(columns=["returns"])


    @staticmethod
    def compute_rolling_close_avg(ticker: str) -> pd.DataFrame:
        df = ParquetStorage.load_ticker_parquet(ticker)[["timestamp", "close"]]
        df = df.sort_values("timestamp").set_index("timestamp")
        df["close_5min_avg"] = df["close"].rolling("5min").mean()
        return df.reset_index()


if __name__ == "__main__":
    ParquetStorage.convert_to_parquet()

    print("***Data from AAPL parquet***")
    print(ParquetStorage.load_ticker_parquet("AAPL"))

    print("***Compute 5-Day Rolling Close Price for AAPL***")
    print(ParquetStorage.compute_rolling_close_avg("AAPL"))

    print("***Compute 5-Day Rolling Volatility for AAPL***")
    print(ParquetStorage.compute_rolling_volatility("AAPL"))

    print("***Compute 5-Day Rolling Volatility for All Symbols***")
    for symbol in ["AAPL", "AMZN", "GOOG", "MSFT", "TSLA"]:
        print(f"*Rolling Volatility for {symbol}*")
        print(ParquetStorage.compute_rolling_volatility(symbol).tail())
