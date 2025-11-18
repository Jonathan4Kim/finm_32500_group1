import random

from order import Order
from orderbook import OrderBook, DualIndexBook


class MatchingEngine:

    @staticmethod
    def simulate_execution(order: Order):
        """
        Simulates trade execution using a synthetic orderbook.
        Returns the price and quantity the order is filled at.

        Fill logic:
        - 10% cancel
        - 60% partial
        - 30% full
        """
        # 1) Build synthetic orderbook around price
        bids, asks = OrderBook.generate_orderbook(
            reference_price=order.price,
            levels=5,         # adjustable
            tick_size=0.01,
            vol_mean=100,
            vol_std=20
        )

        # 2) Determine fill price based on side
        if order.side == "BUY":
            # BUY marketable (hits best ask)
            fill_price = asks.best_ask()
        else:
            # SELL marketable (hits best bid)
            fill_price = bids.best_bid()

        # 3) Apply random execution outcome
        u = random.random()

        # Case 1: Cancel
        if u < 0.1:
            return {
                "status": "CANCELLED",
                "qty": 0,
                "price": None
            }

        # Case 2: Partial fill
        elif u < 0.7 and order.qty > 1:
            filled_qty = random.randint(1, order.qty - 1)
            return {
                "status": "PARTIAL",
                "qty": filled_qty,
                "price": fill_price
            }

        # Case 3: Full fill
        else:
            return {
                "status": "FILLED",
                "qty": order.qty,
                "price": fill_price
            }
