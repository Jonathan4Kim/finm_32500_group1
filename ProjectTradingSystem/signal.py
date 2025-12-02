import datetime
from dataclasses import dataclass
from enum import Enum

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    timestamp: datetime
    signal: SignalType
    symbol: str
    price: float
    reason: str