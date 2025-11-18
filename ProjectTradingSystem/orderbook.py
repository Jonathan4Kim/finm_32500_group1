import time

import numpy as np
from sortedcontainers import SortedDict


class OrderBook:
    @staticmethod
    def generate_orderbook(
            reference_price: float,
            levels: int = 10,
            tick_size: float = 0.01,
            vol_mean: float = 100,
            vol_std: float = 20,
            start_order_id: int = 1,
    ):
        """
        Generate a synthetic orderbook using DualIndexBook.

        Returns:
            bids_book, asks_book  (both are DualIndexBook instances)
        """

        bids = DualIndexBook()
        asks = DualIndexBook()

        order_id = start_order_id

        for i in range(1, levels + 1):
            # Bid Side
            bid_price = reference_price - i * tick_size
            bid_vol = max(1, int(np.random.normal(vol_mean, vol_std)))

            bid_order = {
                "order_id": order_id,
                "side": "BUY",
                "symbol": "SYNTH",
                "price": bid_price,
                "qty": bid_vol,
                "ts": time.time(),
            }
            bids.insert(bid_order)
            order_id += 1

            # Ask Side
            ask_price = reference_price + i * tick_size
            ask_vol = max(1, int(np.random.normal(vol_mean, vol_std)))

            ask_order = {
                "order_id": order_id,
                "side": "SELL",
                "symbol": "SYNTH",
                "price": ask_price,
                "qty": ask_vol,
                "ts": time.time(),
            }
            asks.insert(ask_order)
            order_id += 1

        return bids, asks


class DualIndexBook:
    def __init__(self):
        self.price_tree = SortedDict()
        self.order_id_index = {}

    def insert(self, order):
        price = order['price']
        if price not in self.price_tree:
            self.price_tree[price] = []
        self.price_tree[price].append(order)

        # save index into the tree
        self.order_id_index[order['order_id']] = (price, len(self.price_tree[price]) - 1)

    def lookup(self, order_id):
        price, idx = self.order_id_index[order_id]
        return self.price_tree[price][idx]

    def best_bid(self):
        # highest price
        return self.price_tree.peekitem(-1)[0]

    def best_ask(self):
        # lowest price
        return self.price_tree.peekitem(0)[0]

    def orders_at_price(self, price):
        return self.price_tree[price]
