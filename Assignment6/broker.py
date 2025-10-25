import logging


class Broker:
    def __init__(self, cash: float = 1_000_000):
        self.cash = cash
        self.position = 0

    def market_order(self, side: str, qty: int, price: float):
        if qty == 0 or qty is None or int(qty) != qty:
            raise ValueError("Quantity is invalid.")

        if side == "buy":
            if self.cash < qty * price:
                raise ValueError("Cannot make trade, insufficient funds")
            self.position += qty
            self.cash -= qty * price
        elif side == "sell":
            if self.position <=0:
                raise ValueError("Cannot make trade, no position to sell")
            self.position -= qty
            self.cash += qty * price
        else:
            raise ValueError("Invalid side.")