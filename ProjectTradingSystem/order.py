# order.py
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


# Order model and validation
@dataclass
class Order:
    side: str                   # "BUY" or "SELL"
    symbol: str                 # e.g., "AAPL"
    qty: int                    # positive integer
    price: float                # positive float
    ts: Optional[float] = None  # client timestamp (epoch seconds), optional
    id: Optional[int] = None    # client-supplied id, optional

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Order":
        # Basic required fields
        for field in ("side", "symbol", "qty", "price"):
            if field not in d:
                raise ValueError(f"Missing field '{field}' in order payload")

        # convert side to uppercase for strategies
        side = str(d["side"]).upper()
        
        # ensure an actual workable signal is created
        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")

        # extract only symbol in uppercase, raise error if empty
        symbol = str(d["symbol"]).upper().strip()
        if not symbol:
            raise ValueError("symbol must be non-empty")

        # get quantity value, which must be integer and positive (even if SELL)
        try:
            qty = int(d["qty"])
        except Exception:
            raise ValueError("qty must be an integer")
        if qty <= 0:
            raise ValueError("qty must be > 0")

        # get the price, which obviously must be a positive float
        try:
            price = float(d["price"])
        except Exception:
            raise ValueError("price must be a float")
        if price <= 0.0:
            raise ValueError("price must be > 0")

        # get timestamp and id if these keys exist in the dictionary
        ts = None if "ts" not in d else float(d["ts"])
        oid = None if "id" not in d else int(d["id"])
        
        # create the order object
        return Order(side=side, symbol=symbol, qty=qty, price=price, ts=ts, id=oid)