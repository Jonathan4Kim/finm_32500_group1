# gateway.py
import csv
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, Optional
from queue import Queue
from threading import Thread

from alpaca.data.live import StockDataStream
from alpaca.data.enums import DataFeed

from alpaca_env_util import load_keys

from data_client import LiveMarketDataSource

from order import Order

from strategy import MarketDataPoint


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """
    
    Parses Datetime values from market_data.csv (handles timezone offsets).

    Args:
        ts_str (str): timestamp string in 
        iso-like format from yfinance that is to be converted to
        datetime object.

    Returns:
        Optional[datetime]: a datetime object that replaces the iso-like strings into proper formatting.
    """
    ts_str = ts_str.strip()
    try:
        # yfinance writes ISO-like strings; allow either space or 'T' separator.
        return datetime.fromisoformat(ts_str.replace(" ", "T"))
    except ValueError:
        return None


# Each run/session shares the same audit file; next run uses a new timestamped file.
_RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
def _default_audit_path() -> Path:
    """
    Ensures our output directory exists first,
    creates it otherwise.
    Then returns the full path to a csv file where order audit data
    should actually be saved.

    Returns:
        Path: file path that is in output directory
    """
    # create the order_adits directory if needed
    out_dir = Path("order_audits")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # construct a unique file_path in output directory using run_id
    return out_dir / f"order_audit_{_RUN_ID}.csv"


def load_market_data(simulated: bool = False) -> Generator[MarketDataPoint, None, None]:
    """
    Stream rows from market_data.csv as MarketDataPoint instances.
    Expects columns: Datetime, Open, High, Low, Close, Volume, Symbol.

    Args:
        csv_path (str, optional): path to market data csv to be parsed. Defaults to "data/market_data.csv".
        Assumes a certain structure that will be converted to market data points (date, symbol, price)

    Yields:
        Generator[MarketDataPoint, None, None]: We yield MarketDataPoints concurrently instead
        of saving them into a list so processing can happen optimally.
    """
    if simulated:
        csv_path: str = "data/market_data.csv"

        # open the csv file
        with open(csv_path, newline="") as f:
            
            # use a dictreader so for each row we access column by key
            reader = csv.DictReader(f)
            
            # iterate through each row
            for row in reader:
                
                # access datetime, symbol, and closing price
                ts_str = row.get("Datetime")
                symbol = row.get("Symbol")
                price_str = row.get("Close")
                
                # ensure that all these values are non-null
                if not ts_str or not symbol or price_str is None:
                    continue
                
                # parse the timestamp properly (it's in iso-string mode)
                ts = _parse_timestamp(ts_str)
                
                # if that timestamp doesn't have parsing ability/couldn't become datetime, move to next datapoint
                if ts is None:
                    continue
                
                # convert the price from string to float, if possible
                try:
                    price = float(price_str)
                except ValueError:
                    continue
                
                # yield the actual MarketDataPoint
                yield MarketDataPoint(timestamp=ts, symbol=symbol, price=price)
    else:
        # --- LIVE MARKET DATA MODE ---
        api_key, api_secret = load_keys()
        source = LiveMarketDataSource(api_key, api_secret,
                                      symbol="AAPL",
                                      csv_path="streamed_data.csv")

        # yield streaming datapoints (infinite generator)
        yield from source.stream()

def _order_as_dict(order) -> Dict:
    """
    Coerce an Order or mapping into a flat dictionary for logging.

    Args:
        order (Order/dict): the Order object or dictionary
        that is to be converted to a proper value

    Raises:
        TypeError: Ensures that what we're passing as an input
        is an Order or dictionary

    Returns:
        Dict: a flat dictionary we can use for logging!
    """
    
    # order instance conversion
    if isinstance(order, Order):
        return {
            "id": order.id,
            "side": order.side,
            "symbol": order.symbol,
            "qty": order.qty,
            "price": order.price,
            "ts": order.ts,
        }
    
    # dictionary instance conversion
    if isinstance(order, dict):
        return {
            "id": order.get("id") or order.get("order_id"),
            "side": order.get("side"),
            "symbol": order.get("symbol"),
            "qty": order.get("qty"),
            "price": order.get("price"),
            "ts": order.get("ts"),
        }
    
    # any other type conversion
    raise TypeError("order must be Order or dict-like")


def log_order_event(
    order,
    event_type: str,
    filepath: Optional[str] = None,
    status: Optional[str] = None,
    filled_qty: Optional[int] = None,
    filled_price: Optional[float] = None,
    note: Optional[str] = None,
) -> None:
    """
    Append an order event (send/modify/cancel/fill) to an audit CSV.
    Defaults to a per-run file under order_audits/order_audit_<timestamp>.csv so each
    simulation run gets its own log. Override filepath to direct logs elsewhere.

    Args:
        order (Order): Order
        event_type (str): updated event type to be logged
        filepath (Optional[str], optional): path to save log to. Defaults to None.
        status (Optional[str], optional): event status. Defaults to None.
        filled_qty (Optional[int], optional): what quantity was filled. Defaults to None.
        filled_price (Optional[float], optional): price that was filled/to be logged. Defaults to None.
        note (Optional[str], optional): Any additional things that are seen. Defaults to None.
    """
    
    # convert into flat dictionary using _order_as_dict for loggin gpurposes
    row = _order_as_dict(order)
    
    # update the row
    row.update(
        {
            "event_time": datetime.now().isoformat(),
            "event_type": event_type,
            "status": status,
            "filled_qty": filled_qty,
            "filled_price": filled_price,
            "note": note,
        }
    )

    # get the filepath if necessary using default_audit path
    path = Path(filepath) if filepath else _default_audit_path()
    
    # boolean to tell us if a pth exists
    exists = path.exists()
    fieldnames = [
        "event_time",
        "event_type",
        "id",
        "side",
        "symbol",
        "qty",
        "price",
        "ts",
        "status",
        "filled_qty",
        "filled_price",
        "note",
    ]
    # write into file 
    with path.open("a", newline="") as f:
        
        # create a writer for our file
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # write the header of the file if it hasn't been created
        if not exists:
            writer.writeheader()
        
        # write the row we want to log
        writer.writerow(row)
