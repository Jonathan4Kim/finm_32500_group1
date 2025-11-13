# order.py
from enum import Enum, auto

from logger import Logger

class OrderState(Enum):
    NEW = auto()
    ACKED = auto()
    FILLED = auto()
    CANCELED = auto()
    REJECTED = auto()

class Order:
    allowed = {
        OrderState.NEW: {OrderState.ACKED, OrderState.REJECTED},
        OrderState.ACKED: {OrderState.FILLED, OrderState.CANCELED},
    }

    def __init__(self, symbol, qty, side):
        self.state = OrderState.NEW
        self.symbol = symbol
        self.qty = qty
        self.side = side


    def transition(self, new_state):
        if new_state in Order.allowed[self.state]:
            self.state = new_state
        else:
            Logger.log("OrderTransFailed", f"Cannot transition to {new_state} from {self.state.name}")
