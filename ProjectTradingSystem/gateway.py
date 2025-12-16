# gateway.py
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, Optional
from queue import Queue
from threading import Thread
import time

from alpaca_env_util import load_keys
from data_client import LiveMarketDataSource
from order import Order
from strategy import MarketDataPoint
from config.stocks import STOCKS
from config.crypto import CRYPTO

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
        return datetime.fromisoformat(ts_str.replace(" ", "T"))
    except ValueError:
        return None


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
    out_dir = Path("order_audits")
    out_dir.mkdir(parents=True, exist_ok=True)
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
    
    else:
        # --- LIVE MARKET DATA MODE ---
        api_key, api_secret = load_keys()

        # Create equity source for multiple stock symbols
        equity_source = LiveMarketDataSource(
            api_key, api_secret,
            symbols = STOCKS,
            csv_path="data/streamed_stock_data.csv",
            stream_type="stock"
        )

        # Create crypto source for multiple crypto symbols
        crypto_source = LiveMarketDataSource(
            api_key, api_secret,
            symbols = CRYPTO,
            csv_path="data/streamed_crypto_data.csv",
            stream_type="crypto"
        )

        print("Starting live market data streams...")
        print(f"Equity symbols: {equity_source.symbols}")
        print(f"Crypto symbols: {crypto_source.symbols}")

        # Create a shared queue that both streams will feed into
        shared_queue = Queue()

        def stream_to_queue(source, queue):
            """Helper to push stream data into shared queue"""
            try:
                for mdp in source.stream():
                    queue.put(mdp)
            except Exception as e:
                print(f"Stream error for {source.stream_type}: {e}")
                # Stream will automatically reconnect via Alpaca's WebSocket

        # Start both streams in separate threads so they run independently
        equity_thread = Thread(target=stream_to_queue, args=(equity_source, shared_queue), daemon=True)
        crypto_thread = Thread(target=stream_to_queue, args=(crypto_source, shared_queue), daemon=True)
        
        equity_thread.start()
        # crypto_thread.start()

        print("Both streams running independently...")
        print("- Crypto: 24/7")
        print("- Equities: During market hours")
        
        # Yield from shared queue (merges both streams)
        while True:
            mdp = shared_queue.get()  # Blocking call
            yield mdp


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
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)