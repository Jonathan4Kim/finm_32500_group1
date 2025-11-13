# risk_engine.py
from order import Order
from logger import Logger


class RiskEngine:
    def __init__(self, max_order_size=1000, max_position=2000):
        self.max_order_size = max_order_size
        self.max_position = max_position
        self.positions = {}

    def check(self, order: Order) -> bool:
        if order.qty > self.max_order_size:
            Logger.log("OrderFailed", f"Order quantity of {order.qty} exceeds max order size {self.max_order_size}")
            return False
        if order.qty + sum(exist_order.qty for exist_order in self.positions.get(order.symbol, [])) > self.max_position:
            Logger.log("OrderFailed", f"Order quantity of {order.qty} would exceed max position size {self.max_position}")
            return False
        return True


    def update_position(self, order: Order):
        if self.check(order):
            self.positions[order.symbol] = self.positions.get(order.symbol, []) + [order]