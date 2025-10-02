from abc import ABC, abstractmethod
from models import MarketDataPoint

class Strategy(ABC):
    # TODO: remove list return
    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> list:
        pass
