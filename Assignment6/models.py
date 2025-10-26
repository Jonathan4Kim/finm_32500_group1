from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketDataPoint:
    # create timestamp, symbol, and price instances with established types
    timestamp: datetime
    symbol: str
    price: float
