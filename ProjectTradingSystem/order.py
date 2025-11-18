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

        side = str(d["side"]).upper()
        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")

        symbol = str(d["symbol"]).upper().strip()
        if not symbol:
            raise ValueError("symbol must be non-empty")

        try:
            qty = int(d["qty"])
        except Exception:
            raise ValueError("qty must be an integer")
        if qty <= 0:
            raise ValueError("qty must be > 0")

        try:
            price = float(d["price"])
        except Exception:
            raise ValueError("price must be a float")
        if price <= 0.0:
            raise ValueError("price must be > 0")

        ts = None if "ts" not in d else float(d["ts"])
        oid = None if "id" not in d else int(d["id"])
        return Order(side=side, symbol=symbol, qty=qty, price=price, ts=ts, id=oid)