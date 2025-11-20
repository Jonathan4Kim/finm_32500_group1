# gateway.py
import csv
from datetime import datetime
from typing import Generator, Iterable

from strategy import MarketDataPoint


def load_market_data(csv_path: str = "market_data_trimmed.csv") -> Generator[MarketDataPoint, None, None]:
    """
    Stream rows from the CSV as MarketDataPoint instances.
    """
    with open(csv_path, newline="") as f:
        reader: Iterable[list[str]] = csv.reader(f)
        header_skipped = False
        for row in reader:
            if not header_skipped:
                header_skipped = True
                continue
            if len(row) < 3:
                continue
            ts_str, symbol, price_str = row[0], row[1], row[2]
            try:
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                price = float(price_str)
            except ValueError:
                continue
            yield MarketDataPoint(timestamp=ts, symbol=symbol, price=price)

