"""
Download intraday data with yfinance for multiple tickers and combine into a single market_data.csv.
Output columns: Datetime, Open, High, Low, Close, Volume, Symbol.
"""
from pathlib import Path
from typing import List

import pandas as pd
import yfinance as yf


DATA_DIR = Path(__file__).parent
OUTPUT_FILE = DATA_DIR / "market_data.csv"
REQUIRED_COLS = ["Open", "High", "Low", "Close", "Volume"]
TICKERS = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'AVGO', 'META', 'TSM', 'BRK-B']
PERIOD = "8d"
INTERVAL = "1m"


def download_ticker(ticker: str) -> pd.DataFrame:
    df = yf.download(
        tickers=ticker,
        period=PERIOD,
        interval=INTERVAL,
        progress=False,
        auto_adjust=True
    )

    # Flatten MultiIndex columns if present.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    # Keep only required columns.
    missing = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing:
        raise ValueError(f"{ticker} missing columns: {missing}")

    df = df[REQUIRED_COLS].copy()
    df.reset_index(inplace=True)
    if "Datetime" not in df.columns:
        # yfinance can name the index column differently after reset_index
        first_col = df.columns[0]
        df.rename(columns={first_col: "Datetime"}, inplace=True)
    df["Symbol"] = ticker
    return df


def build_market_data() -> Path:
    frames: List[pd.DataFrame] = []

    for ticker in TICKERS:
        try:
            frames.append(download_ticker(ticker))
            print(f"Downloaded {ticker}")
        except Exception as exc:
            print(f"Skip {ticker}: {exc}")

    if not frames:
        raise RuntimeError("No data downloaded.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined[["Datetime", "Open", "High", "Low", "Close", "Volume", "Symbol"]]
    combined["Datetime"] = pd.to_datetime(combined["Datetime"])
    combined.set_index('Datetime', inplace=True)
    combined.dropna(inplace=True)
    combined.sort_index(inplace=True)
    combined.to_csv(OUTPUT_FILE, index=True)
    return OUTPUT_FILE


if __name__ == "__main__":
    out_path = build_market_data()
    print(f"Wrote combined market data to {out_path}")
