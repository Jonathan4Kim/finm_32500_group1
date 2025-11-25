# order_manager.py
import time
from csv import DictWriter
import copy
from dataclasses import asdict
from itertools import count
from typing import Optional

from alpaca.trading.client import TradingClient
from alpaca_env_util import load_keys

from order import Order, to_alpaca_order
from risk_engine import RiskEngine
from logger import Logger
from matching_engine import MatchingEngine as ME
from gateway import log_order_event

class OrderManager:
    """
    A simplified single-process, synchronous Order Manager.
    It processes Order objects directly (no socket, no JSON).
    """

    def __init__(self, risk_engine: RiskEngine, simulated: bool = False):
        self._order_id_counter = count(1)
        self._risk_engine = risk_engine
        self._simulated = simulated
        self.orders = []
        self.logger = Logger()


    def process_order(self, order: Order) -> dict:
        """
        Process a fully constructed Order object.

        Example:
            order = Order(side="BUY", symbol="AAPL", qty=10, price=170)
            om.process_order(order)
        """

        # Validate basic fields (optional: remove if you handle in Order class)
        if order.side not in ("BUY", "SELL"):
            return {"ok": False, "msg": "Invalid side (must be BUY or SELL)"}

        if order.qty <= 0:
            return {"ok": False, "msg": "Quantity must be > 0"}

        if order.price <= 0:
            return {"ok": False, "msg": "Price must be > 0"}

        # Assign timestamp if missing
        if order.ts is None:
            order.ts = time.time()

        # Assign server order ID if missing
        if order.id is None:
            order.id = next(self._order_id_counter)

        # Log send
        log_order_event(order, event_type="sent")

        # Run risk checks
        if not self._risk_engine.check(order):
            self.logger.log("OrderManager", {"reason": "Order failed risk checks"})
            log_order_event(order, event_type="rejected", status="risk_check_failed", note="risk_check_failed")
            return {"ok": False, "msg": "risk_check_failed"}

        # Simulate execution via matching engine
        if self._simulated:
            response = ME.simulate_execution(order)
        else:
            api_key, api_secret = load_keys()
            trading_client = TradingClient(api_key, api_secret, paper=True)
            alpaca_order = to_alpaca_order(order)
            submitted = trading_client.submit_order(alpaca_order)

        # Build filled version (deep copy)
        filled_order = copy.deepcopy(order)
        filled_order.qty = response.get("qty", filled_order.qty)
        filled_order.price = response.get("price", filled_order.price)

        # Log based on status
        status = response["status"]

        # Apply risk/cash/position updates only on executed quantity
        if status in ("FILLED", "PARTIAL") and filled_order.qty > 0:
            self._risk_engine.update_position(filled_order, filled_qty=filled_order.qty)

        if status == "CANCELLED":
            self.logger.log(
                "OrderManager",
                {"reason": f"Order Cancelled {order.id}: "
                           f"{order.side} {order.qty} {order.symbol} @ {order.price:.2f}"}
            )
        elif status == "PARTIAL":
            self.orders.append(order)
            self.logger.log(
                "OrderManager",
                {"reason": f"Order Partially Filled {order.id}: "
                           f"{filled_order.side} {filled_order.qty} "
                           f"{filled_order.symbol} @ {filled_order.price:.2f}"}
            )
        elif status == "FILLED":
            self.orders.append(order)
            self.logger.log(
                "OrderManager",
                {"reason": f"Order Filled {order.id}: "
                           f"{filled_order.side} {filled_order.qty} "
                           f"{filled_order.symbol} @ {filled_order.price:.2f}"}
            )

        # Logs the order status
        log_order_event(
            order,
            event_type=status.lower(),
            status=status,
            filled_qty=filled_order.qty,
            filled_price=filled_order.price,
        )

        # Return execution summary
        return {
            "ok": True,
            "status": status,
            "order": asdict(order),
            "filled_qty": filled_order.qty,
            "filled_price": filled_order.price
        }


    def save_orders_to_csv(self, filepath="order_log.csv"):
        fieldnames = ["id", "side", "symbol", "qty", "price", "ts"]

        with open(filepath, "w", newline="") as f:
            writer = DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()

            for order in self.orders:
                writer.writerow({
                    "id": order.id,
                    "side": order.side,
                    "symbol": order.symbol,
                    "qty": order.qty,
                    "price": order.price,
                    "ts": order.ts,
                })
