import random

from order import Order


class MatchingEngine:
    @staticmethod
    def simulate_execution(order: Order):
        """
        Random fill logic:
        - 10% cancel
        - 60% partial fill
        - 30% full fill
        """
        # Case 1: Cancel before fill
        if random.random() < 0.1:
            return {"status": "CANCELLED"}

        # Case 2: Partial Fill
        elif random.random() < 0.7 and order.qty > 1:
            filled_qty = random.randint(1, order.qty - 1)
            return {"status": "PARTIAL", "qty": filled_qty}

        # Case 3: Full Fill
        else:
            return {"status": "FILLED", "qty": order.qty}