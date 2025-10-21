import pandas as pd
import json
from abc import ABC

class Instrument(ABC):
    
    def __init__(self, symbol, inst_type, price, sector, issuer):
        self.symbol = symbol
        self.inst_ttype = inst_type
        self.price = price
        self.sector = sector
        self.issuer = issuer

class ETF(Instrument):
    
    def __init__(self, symbol, inst_type, price, sector, issuer):
        super().__init__(symbol, inst_type, price, sector, issuer)

class Bond(Instrument):
    def __init__(self, symbol, inst_type, price, sector, issuer, maturity):
        super().__init__(symbol, inst_type, price, sector, issuer)
        self.maturity = maturity

class Stock(Instrument):
    def __init__(self, symbol, inst_type, price, sector, issuer):
        super().__init__(symbol, inst_type, price, sector, issuer)

class InstrumentFactory:
    
    def __init__(self):
        pass
    
    def create_instrument(self, data: dict) -> Instrument:
        # I think this will a single row of the pandas dataframe, and we call pd.to_dict()
        # when we do that, we'll get the columns in a nes
        symbol = data["symbol"]
        inst_type = data["type"]
        price = data["price"]
        sector = data["sector"]
        issuer = data["issuer"]
        if type == "Stock":
            return Stock(symbol, inst_type, price, sector, issuer)
        if type == "Bond":
            maturity = maturity = data["maturity"]
            return Bond(symbol, inst_type, price, sector, issuer, maturity)
        if type == "ETF":
            return ETF(symbol, inst_type, price, sector, issuer)
    

if __name__ == "__main__":
    # read the dictionary
    instruments = pd.read_csv("instruments.csv").to_dict(orient="records")
    inst_factory = InstrumentFactory()
    arr = []
    for instrument in instruments:
        arr.append(inst_factory.create_instrument(instrument))
    print(len(arr))
    