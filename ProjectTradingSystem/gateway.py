# gateway.py
import csv
from datetime import datetime
from typing import Generator, Optional

from strategy import MarketDataPoint


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse Datetime values from market_data.csv (handles timezone offsets)."""
    ts_str = ts_str.strip()
    try:
        # yfinance writes ISO-like strings; allow either space or 'T' separator.
        return datetime.fromisoformat(ts_str.replace(" ", "T"))
    except ValueError:
        return None


def load_market_data(csv_path: str = "data/market_data.csv") -> Generator[MarketDataPoint, None, None]:
    """
    Stream rows from market_data.csv as MarketDataPoint instances.
    Expects columns: Datetime, Open, High, Low, Close, Volume, Symbol.
    """
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_str = row.get("Datetime")
            symbol = row.get("Symbol")
            price_str = row.get("Close")
            if not ts_str or not symbol or price_str is None:
                continue

            ts = _parse_timestamp(ts_str)
            if ts is None:
                continue

            try:
                price = float(price_str)
            except ValueError:
                continue

            yield MarketDataPoint(timestamp=ts, symbol=symbol, price=price)
