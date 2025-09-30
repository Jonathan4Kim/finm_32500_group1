"""
order.py
"""

# imports
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime
from dataclasses import dataclass

# make MarketDataPoint frozen using dataclasses import
@dataclass(frozen=True)
class MarketDataPoint:
    # create timestamp, symbol, and price instances with established types
    timestamp: datetime
    symbol: str
    price: float

class Order:
    def __init__(self, symbol, quantity, price, status):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.status = status

    def __str__(self):
        return f"{self.symbol} {self.quantity} {self.price} {self.status}"

    def __repr__(self):
        return f"Order({self.symbol} {self.quantity} {self.price} {self.status})"

class OrderError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ExecutionError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class TestUpdate(unittest.TestCase):
    
    def test_check_order_and_mdp(self):
        order = Order("AAPL", 200, 157.45, "new")
        order.status = "cancelled"
        self.assertEqual(order.status, "cancelled")

    def test_mdp_price(self):
        mdp = MarketDataPoint(datetime(2024, 12, 30, 14, 46), "MSFT", 155.24)
        with self.assertRaises(FrozenInstanceError):
            mdp.timestamp = datetime(2024, 12, 3, 14, 46)

if __name__ == "__main__":
    unittest.main()