# order.py
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

from strategy import Signal, SignalType

from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest


# Order model and validation
@dataclass
class Order:
    side: str                   # "BUY" or "SELL"
    symbol: str                 # e.g., "AAPL"
    qty: int                    # positive integer
    price: float                # positive float
    ts: Optional[float] = None  # client timestamp (epoch seconds), optional
    id: Optional[int] = None    # client-supplied id, optional

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Order":
        # Basic required fields
        for field in ("side", "symbol", "qty", "price"):
            if field not in d:
                raise ValueError(f"Missing field '{field}' in order payload")

        # convert side to uppercase for strategies
        side = str(d["side"]).upper()
        
        # ensure an actual workable signal is created
        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")

        # extract only symbol in uppercase, raise error if empty
        symbol = str(d["symbol"]).upper().strip()
        if not symbol:
            raise ValueError("symbol must be non-empty")

        # get quantity value, which must be integer and positive (even if SELL)
        try:
            qty = int(d["qty"])
        except Exception:
            raise ValueError("qty must be an integer")
        if qty <= 0:
            raise ValueError("qty must be > 0")

        # get the price, which obviously must be a positive float
        try:
            price = float(d["price"])
        except Exception:
            raise ValueError("price must be a float")
        if price <= 0.0:
            raise ValueError("price must be > 0")

        # get timestamp and id if these keys exist in the dictionary
        ts = None if "ts" not in d else float(d["ts"])
        oid = None if "id" not in d else int(d["id"])
        
        # create the order object
        return Order(side=side, symbol=symbol, qty=qty, price=price, ts=ts, id=oid)

class OrderBuilder():

    def __init__(self, trading_client, signal: Signal):
        
        self.trading_client = trading_client
        self.signal = signal
    
    def get_order_size(self):
        
        if self.signal.signal == SignalType.SELL:
            position = self.trading_client.get_open_position(self.symbol)
            qty = abs(float(position.qty))  # Ensure numeric size

            if qty == 0:
                print("No open position to close.")
                return
            
            return qty
        
        if self.signal.signal == SignalType.BUY:
            account = self.trading_client.get_account()
            cash = float(account.cash)

            allocation = cash * 0.01   # 1% of total cash

            if allocation < self.signal.price:
                print("Not enough cash to buy even 1 share.")
                return 0

            qty = int(allocation // self.signal.price)
            return qty


    def build_order(self) -> Order:

        order = Order(
            side = self.signal.signal.value,
            symbol = self.signal.symbol,
            qty = self.get_order_size(),
            price = self.signal.price
        )

        return order        


def to_alpaca_order(order):
    side = OrderSide.BUY if order.side.upper() == "BUY" else OrderSide.SELL
    price = round(order.price, 2)

    # CRYPTO ORDER
    if "/" in order.symbol:
        return LimitOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            side=side,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.FOK,
            limit_price=price,
        )

    # LIMIT ORDER
    if order.price is not None:
        return LimitOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            side=side,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.FOK,
            limit_price=price,
        )

    # MARKET ORDER
    return MarketOrderRequest(
        symbol=order.symbol,
        qty=order.qty,
        side=side,
        type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY
    )