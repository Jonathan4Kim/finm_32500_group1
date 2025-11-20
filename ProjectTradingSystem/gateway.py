# gateway.py
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, Optional

from order import Order

from strategy import MarketDataPoint


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse Datetime values from market_data.csv (handles timezone offsets)."""
    ts_str = ts_str.strip()
    try:
        # yfinance writes ISO-like strings; allow either space or 'T' separator.
        return datetime.fromisoformat(ts_str.replace(" ", "T"))
    except ValueError:
        return None


# Each run/session shares the same audit file; next run uses a new timestamped file.
_RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
def _default_audit_path() -> Path:
    out_dir = Path("order_audits")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"order_audit_{_RUN_ID}.csv"


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


def _order_as_dict(order) -> Dict:
    """Coerce an Order or mapping into a flat dictionary for logging."""
    if isinstance(order, Order):
        return {
            "id": order.id,
            "side": order.side,
            "symbol": order.symbol,
            "qty": order.qty,
            "price": order.price,
            "ts": order.ts,
        }
    if isinstance(order, dict):
        return {
            "id": order.get("id") or order.get("order_id"),
            "side": order.get("side"),
            "symbol": order.get("symbol"),
            "qty": order.get("qty"),
            "price": order.get("price"),
            "ts": order.get("ts"),
        }
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
    """
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

    path = Path(filepath) if filepath else _default_audit_path()
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
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
