from abc import ABC, abstractmethod
# TODO: CHANGE IF WE MOVE MARKETDATAPOINT CLASS TO MODELS.PY
from data_loader import MarketDataPoint
from data_loader import load_data
from collections import deque

class Strategy(ABC):
    # TODO: remove list return
    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> list:
        pass
