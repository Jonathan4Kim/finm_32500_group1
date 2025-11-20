# orderbook.py
import heapq
import time
from typing import Dict, List, Optional, Tuple


class OrderBook:
    """
    Heap-backed order book enforcing price-time priority.

    - Internally maintains min-heap asks and max-heap bids (via negated price) using
      (price_key, seq, order_id, version) tuples so newer versions supersede stale ones.
    - Supports add_order (auto-matching), modify_order (re-prices/updates qty), and cancel_order.
    - Matching occurs against the opposite side with standard crossing logic and records trade fills.
    """

    def __init__(self):
        # Heaps store (price_key, seq, order_id, version); price_key negated for bids.
        self.bids: List[Tuple[float, int, int, int]] = []
        self.asks: List[Tuple[float, int, int, int]] = []
        self.orders: Dict[int, Dict] = {}
        self._seq = 0

    def _next_seq(self) -> int:
        """Monotonic sequence for time-priority tie breaking."""
        self._seq += 1
        return self._seq

    def _normalize(self, order) -> Dict:
        """Normalize dict/Order-like input into internal record with versioning."""
        oid = getattr(order, "id", None)
        if isinstance(order, dict):
            oid = order.get("order_id", oid)
        if oid is None:
            raise ValueError("order_id is required")

        side = getattr(order, "side", None) if not isinstance(order, dict) else order.get("side")
        symbol = getattr(order, "symbol", None) if not isinstance(order, dict) else order.get("symbol")
        price = getattr(order, "price", None) if not isinstance(order, dict) else order.get("price")
        qty = getattr(order, "qty", None) if not isinstance(order, dict) else order.get("qty")
        ts = getattr(order, "ts", None) if not isinstance(order, dict) else order.get("ts")

        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if price is None or qty is None:
            raise ValueError("price and qty are required")

        base = self.orders.get(oid, {})
        version = base.get("version", 0) + 1

        return {
            "order_id": oid,
            "side": side,
            "symbol": symbol,
            "price": float(price),
            "qty": int(qty),
            "ts": float(ts) if ts is not None else time.time(),
            "active": True,
            "seq": self._next_seq(),
            "version": version,
        }

    def _push(self, rec: Dict):
        """Push the record to the appropriate heap using price-time priority."""
        entry = (
            -rec["price"] if rec["side"] == "BUY" else rec["price"],
            rec["seq"],
            rec["order_id"],
            rec["version"],
        )
        heapq.heappush(self.bids if rec["side"] == "BUY" else self.asks, entry)

    def _best(self, side: str) -> Tuple[Optional[float], Optional[Dict]]:
        """Return best price and live order for the given side, skipping stale entries."""
        heap = self.bids if side == "BUY" else self.asks
        while heap:
            _, _, oid, ver = heap[0]
            rec = self.orders.get(oid)
            if not rec or not rec["active"] or rec["qty"] <= 0 or rec["version"] != ver or rec["side"] != side:
                heapq.heappop(heap)
                continue
            return rec["price"], rec
        return None, None

    def _crosses(self, incoming: Dict, resting_price: float) -> bool:
        """Check if incoming crosses resting price."""
        if incoming["side"] == "BUY":
            return incoming["price"] >= resting_price
        return incoming["price"] <= resting_price

    def _record_trade(self, buy_id: int, sell_id: int, price: float, qty: int) -> Dict:
        """Build a trade record dictionary."""
        return {
            "buy_id": buy_id,
            "sell_id": sell_id,
            "price": price,
            "qty": qty,
            "ts": time.time(),
        }

    def _match(self, incoming: Dict) -> List[Dict]:
        """Match incoming order against the opposite book, producing trade records."""
        trades: List[Dict] = []
        counter_side = "SELL" if incoming["side"] == "BUY" else "BUY"

        while incoming["qty"] > 0:
            best_price, resting = self._best(counter_side)
            if not resting or best_price is None:
                break
            if not self._crosses(incoming, best_price):
                break

            trade_qty = min(incoming["qty"], resting["qty"])
            trade_price = resting["price"]
            incoming["qty"] -= trade_qty
            resting["qty"] -= trade_qty
            trades.append(
                self._record_trade(
                    buy_id=incoming["order_id"] if incoming["side"] == "BUY" else resting["order_id"],
                    sell_id=incoming["order_id"] if incoming["side"] == "SELL" else resting["order_id"],
                    price=trade_price,
                    qty=trade_qty,
                )
            )

            if resting["qty"] <= 0:
                resting["active"] = False

        if incoming["qty"] <= 0:
            incoming["active"] = False

        return trades

    def add_order(self, order) -> List[Dict]:
        """Add an order and immediately attempt matching. Returns list of trades."""
        rec = self._normalize(order)
        self.orders[rec["order_id"]] = rec
        self._push(rec)
        trades = self._match(rec)
        return trades

    def modify_order(self, order_id: int, new_qty: Optional[int] = None, new_price: Optional[float] = None) -> List[Dict]:
        """Modify an existing active order; reprices with new seq/version and re-matches."""
        rec = self.orders.get(order_id)
        if not rec or not rec["active"]:
            return []

        if new_qty is not None:
            rec["qty"] = int(new_qty)
        if new_price is not None:
            rec["price"] = float(new_price)
        rec["ts"] = time.time()
        rec["seq"] = self._next_seq()
        rec["version"] += 1
        self._push(rec)
        return self._match(rec)

    def cancel_order(self, order_id: int) -> bool:
        """Cancel an active order."""
        rec = self.orders.get(order_id)
        if not rec or not rec["active"]:
            return False
        rec["active"] = False
        rec["qty"] = 0
        rec["version"] += 1
        return True

    def best_bid(self) -> Optional[float]:
        """Return current best bid price, if any."""
        price, _ = self._best("BUY")
        return price

    def best_ask(self) -> Optional[float]:
        """Return current best ask price, if any."""
        price, _ = self._best("SELL")
        return price

    def depth(self) -> Dict[str, List[Tuple[float, int]]]:
        """Aggregate visible depth by price level for bids/asks."""
        bids: Dict[float, int] = {}
        asks: Dict[float, int] = {}
        for rec in self.orders.values():
            if not rec["active"] or rec["qty"] <= 0:
                continue
            book = bids if rec["side"] == "BUY" else asks
            book[rec["price"]] = book.get(rec["price"], 0) + rec["qty"]
        return {
            "bids": sorted([(p, q) for p, q in bids.items()], key=lambda x: -x[0]),
            "asks": sorted([(p, q) for p, q in asks.items()], key=lambda x: x[0]),
        }
