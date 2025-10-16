import logging


class Broker:
    def __init__(self, cash: float = 1_000_000):
        self.cash = cash
        self.position = 0

    def market_order(self, side: str, qty: int, price: float):
        if side == "buy":
            if self.cash < qty * price:
                logging.info("Cannot make trade, insufficient funds")
                return
            self.position += 1
            self.cash -= qty * price
        elif side == "sell":
            if self.position <=0:
                logging.info("Cannot make trade, no position to sell")
                return
            self.position -= 1
            self.cash += qty * price
        else:
            logging.warning("Engine tried to execute invalid side value")