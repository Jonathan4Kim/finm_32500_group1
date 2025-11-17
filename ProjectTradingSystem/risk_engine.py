# risk_engine.py
from threading import Lock
from order import Order
from logger import Logger


class RiskEngine:
    _instance = None
    _lock = Lock()


    def __new__(cls, max_order_size=1000, max_position=2000, cash_balance=10000):
        """
        Thread-safe Singleton constructor.
        Ensures only one RiskEngine ever exists.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance


    def __init__(self, max_order_size=1000, max_position=2000, cash_balance=10000):
        """
        Guard against repeated initialization.
        """
        if self._initialized:
            return

        self.max_order_size = max_order_size
        self.max_position = max_position
        self.cash_balance = cash_balance
        self.positions = {}

        self._initialized = True


    def check(self, order: Order) -> bool:
        """Return True if order is allowed, False otherwise."""

        # Size constraint
        if order.qty > self.max_order_size:
            Logger().log(
                "OrderFailed",
                {"reason": f"Order qty {order.qty} exceeds max order size {self.max_order_size}"}
            )
            return False

        # Position constraint
        current_pos = sum(o.qty for o in self.positions.get(order.symbol, []))
        if order.qty + current_pos > self.max_position:
            Logger().log(
                "OrderFailed",
                {"reason": f"Order qty {order.qty} exceeds max position {self.max_position}"}
            )
            return False

        # Cash constraint
        if order.qty * order.price > self.cash_balance:
            Logger().log(
                "OrderFailed",
                {"reason": f"Order value exceeds cash balance {self.cash_balance}"}
            )
            return False

        return True


    def update_position(self, order: Order):
        """Update internal positions if risk check passes."""
        if self.check(order):
            self.positions.setdefault(order.symbol, []).append(order)
