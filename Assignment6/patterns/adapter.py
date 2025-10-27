import json
import xml.etree.ElementTree as ET
from datetime import datetime
from Assignment6.models import MarketDataPoint

class YahooFinanceAdapter:
    def __init__(self, json_file):
        with open(json_file, "r") as f:
            self.data = json.load(f)

    def get_data(self, symbol: str) -> MarketDataPoint:
        if self.data is None:
            raise ValueError(f"Data is not valid")
        return MarketDataPoint(
            symbol=symbol,
            price=float(self.data.get("last_price")),
            timestamp=datetime.fromisoformat(self.data.get("timestamp")),
        )

class BloombergXMLAdapter:
    def __init__(self, xml_file):
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()

    def get_data(self, symbol: str) -> MarketDataPoint:
        instrument = self.root
        ticker = instrument.find("symbol").text
        if ticker == symbol:
            price = float(instrument.find("price").text)
            time = datetime.fromisoformat(
                instrument.find("timestamp").text.replace("Z", "+00:00")
            )
            return MarketDataPoint(symbol=symbol, price=price, timestamp=time)
        raise ValueError(f"Symbol {symbol} not found in Bloomberg data")