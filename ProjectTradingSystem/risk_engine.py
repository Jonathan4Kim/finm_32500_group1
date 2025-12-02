# risk_engine.py
from threading import Lock
from order import Order
from logger import Logger


class RiskEngineLive:
    _instance = None
    _lock = Lock()


    def __new__(cls, max_order_value, max_asset_percentage):
        """
        Thread-safe Singleton constructor.
        Ensures only one RiskEngine ever exists.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance


    def __init__(self, max_order_value=1000, max_asset_percentage=0.1):
        """
        Guard against repeated initialization.
        """
        if self._initialized:
            return

        self.max_order_value = max_order_value
        self.max_asset_percentage = max_asset_percentage

        self._initialized = True


    def check(self, order: Order, trading_client) -> bool:
        """Return True if order is allowed, False otherwise."""
        print(f"Checking order: {order}")

        # Finds the stats for the asset if portfolio holds any
        asset_stats = None
        for asset in trading_client.get_all_positions():
            if asset.symbol == order.symbol.replace("/", ""):
                asset_stats = asset
        if asset_stats is None:
            print(f"No stats found for {order.symbol}. Continuing risk checks.")

        # Cash constraint
        cash_balance = float(trading_client.get_account().non_marginable_buying_power)
        if order.side == "BUY" and order.qty * order.price > cash_balance:
            Logger().log(
                "OrderFailed",
                {"reason": f"Order value exceeds cash balance {cash_balance}"}
            )
            return False

        # Check enough position to sell
        if order.side =="SELL" and (asset_stats is None or float(asset_stats.qty) < order.qty):
            Logger().log(
                "OrderFailed",
                {"reason": f"Order qty {order.qty} exceeds current position size of {asset_stats.qty if asset_stats else 0}"}
            )
            return False

        # Value constraint
        if order.side == "BUY" and order.qty * order.price > self.max_order_value:
            Logger().log(
                "OrderFailed",
                {"reason": f"Order qty {order.qty} exceeds max order value {self.max_order_value}"}
            )
            return False

        # Relative size constraint
        equity = float(trading_client.get_account().equity)
        if asset_stats:
            if order.side == "BUY" and order.qty * order.price + float(asset_stats.market_value) > equity * self.max_asset_percentage:
                Logger().log(
                    "OrderFailed",
                    {"reason": f"New order causes symbol position to exceed equity share of {equity * self.max_asset_percentage}"}
                )
            return False

        return True


class RiskEngineSim:
    _instance = None
    _lock = Lock()


    def __new__(cls, max_order_size, max_position, cash_balance, max_total_buy=None, max_total_sell=None):
        """
        Thread-safe Singleton constructor.
        Ensures only one RiskEngine ever exists.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance


    def __init__(
        self,
        max_order_size=1000,
        max_position=2000,
        cash_balance=10000,
        max_total_buy=None,
        max_total_sell=None,
    ):
        """
        Guard against repeated initialization.
        """
        if self._initialized:
            return

        self.max_order_size = max_order_size
        self.max_position = max_position
        self.cash_balance = cash_balance
        self.max_total_buy = max_total_buy if max_total_buy is not None else float("inf")
        self.max_total_sell = max_total_sell if max_total_sell is not None else float("inf")

        self.positions = {}  # symbol -> list of orders
        self.buy_totals = {}  # symbol -> cumulative buy qty
        self.sell_totals = {}  # symbol -> cumulative sell qty

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

        # Net position constraint
        current_pos = sum(o.qty if o.side == "BUY" else -o.qty for o in self.positions.get(order.symbol, []))
        prospective_pos = current_pos + (order.qty if order.side == "BUY" else -order.qty)
        if abs(prospective_pos) > self.max_position:
            Logger().log(
                "OrderFailed",
                {"reason": f"Order would exceed max position {self.max_position} (current {current_pos})"}
            )
            return False

        # Total buy/sell limits (per symbol, cumulative)
        if order.side == "BUY":
            current_buy = self.buy_totals.get(order.symbol, 0)
            if current_buy + order.qty > self.max_total_buy:
                Logger().log(
                    "OrderFailed",
                    {"reason": f"Order exceeds max total buy {self.max_total_buy} for {order.symbol}"}
                )
                return False
        else:
            current_sell = self.sell_totals.get(order.symbol, 0)
            if current_sell + order.qty > self.max_total_sell:
                Logger().log(
                    "OrderFailed",
                    {"reason": f"Order exceeds max total sell {self.max_total_sell} for {order.symbol}"}
                )
                return False

        # Cash constraint (buys only)
        if order.side == "BUY" and order.qty * order.price > self.cash_balance:
            Logger().log(
                "OrderFailed",
                {"reason": f"Order value exceeds cash balance {self.cash_balance}"}
            )
            return False

        return True


    def update_position(self, order: Order, filled_qty: int = None):
        """Update internal positions and cash after a (possibly partial) fill."""
        qty = order.qty if filled_qty is None else filled_qty
        if qty <= 0:
            return

        # Update positions storage
        self.positions.setdefault(order.symbol, []).append(
            Order(side=order.side, symbol=order.symbol, qty=qty, price=order.price, ts=order.ts, id=order.id)
        )

        if order.side == "BUY":
            self.buy_totals[order.symbol] = self.buy_totals.get(order.symbol, 0) + qty
            self.cash_balance -= qty * order.price
        else:
            self.sell_totals[order.symbol] = self.sell_totals.get(order.symbol, 0) + qty
            self.cash_balance += qty * order.price
