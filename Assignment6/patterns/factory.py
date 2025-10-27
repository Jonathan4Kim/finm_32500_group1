import pandas as pd
import json
from abc import ABC, abstractmethod

class Instrument(ABC):
    
    def __init__(self, symbol, inst_type, prices, sector, issuer):
        self.symbol = symbol
        self.inst_ttype = inst_type
        self.prices = prices
        self.sector = sector
        self.issuer = issuer

    @abstractmethod
    def get_metrics(self) -> dict:
        pass

class ETF(Instrument):
    
    def __init__(self, symbol, inst_type, prices, sector, issuer):
        super().__init__(symbol, inst_type, prices, sector, issuer)

    def get_metrics(self) -> dict:
        """Return basic price information."""
        return {
            "symbol": self.symbol,
            "last_price": float(self.prices[-1]) if len(self.prices) > 0 else None,
            "num_observations": len(self.prices)
        }

class Bond(Instrument):
    def __init__(self, symbol, inst_type, prices, sector, issuer, maturity):
        super().__init__(symbol, inst_type, prices, sector, issuer)
        self.maturity = maturity

    def get_metrics(self) -> dict:
        """Return basic price information."""
        return {
            "symbol": self.symbol,
            "last_price": float(self.prices[-1]) if len(self.prices) > 0 else None,
            "num_observations": len(self.prices)
        }

class Stock(Instrument):
    def __init__(self, symbol, inst_type, prices, sector, issuer):
        super().__init__(symbol, inst_type, prices, sector, issuer)

    def get_metrics(self) -> dict:
        """Return basic price information."""
        return {
            "symbol": self.symbol,
            "last_price": float(self.prices[-1]) if len(self.prices) > 0 else None,
            "num_observations": len(self.prices)
        }


class InstrumentFactory:
    
    def __init__(self):
        pass
    
    def create_instrument(self, data: dict) -> Instrument:
        # I think this will a single row of the pandas dataframe, and we call pd.to_dict()
        # when we do that, we'll get the columns in a nes
        symbol = data["symbol"]
        inst_type = data["type"]
        prices = data["prices"]
        sector = data["sector"]
        issuer = data["issuer"]
        if inst_type == "Stock":
            return Stock(symbol, inst_type, prices, sector, issuer)
        if inst_type == "Bond":
            maturity = data["maturity"]
            return Bond(symbol, inst_type, prices, sector, issuer, maturity)
        if inst_type == "ETF":
            return ETF(symbol, inst_type, prices, sector, issuer)

        raise ValueError("Unknown Instrument Type")
    

if __name__ == "__main__":
    # read the dictionary
    instruments = pd.read_csv("instruments.csv").to_dict(orient="records")
    inst_factory = InstrumentFactory()
    arr = []
    for instrument in instruments:
        arr.append(inst_factory.create_instrument(instrument))
    print(len(arr))
    