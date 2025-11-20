import random

from order import Order
from orderbook import OrderBook


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
        # 1) Build synthetic orderbook around order price using new OrderBook
        ob = OrderBook()

        levels = 5
        tick_size = 0.01
        base_price = order.price
        vol_mean = 100
        vol_std = 20

        # populate symmetric levels
        for i in range(1, levels + 1):
            bid_price = base_price - i * tick_size
            ask_price = base_price + i * tick_size
            bid_qty = max(1, int(random.gauss(vol_mean, vol_std)))
            ask_qty = max(1, int(random.gauss(vol_mean, vol_std)))
            ob.add_order({"order_id": 10_000 + i, "side": "BUY", "symbol": order.symbol, "price": bid_price, "qty": bid_qty})
            ob.add_order({"order_id": 20_000 + i, "side": "SELL", "symbol": order.symbol, "price": ask_price, "qty": ask_qty})

        # 2) Insert incoming order to determine best executable price via matching
        trades = ob.add_order({"order_id": 1, "side": order.side, "symbol": order.symbol, "price": order.price, "qty": order.qty})
        fill_price = None
        if trades:
            # use last trade price from simulated matching
            fill_price = trades[-1]["price"]
        else:
            # fallback to top of book if no trade generated (should be rare for marketable)
            fill_price = ob.best_ask() if order.side == "BUY" else ob.best_bid()

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
