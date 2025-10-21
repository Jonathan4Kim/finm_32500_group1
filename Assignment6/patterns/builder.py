import json
class Portfolio:
    def __init__(self):
        self.name 
        self.sub_portf

class PortfolioBuilder:
    def __init__(self):
        self.positions = []
        self.subportfolios = []
    
    def add_position(self, symbol, quantity, price):
        if not self.positions:
            self.positions = []
        self.positions.append({"symbol": symbol, "quantity": quantity, "price": price})

    def set_owner(self, name):
        self.owner = name
    
    def add_subportfolio(self, name, builder):
        self.subportfolios.append()
    
    def build():
        return Portfolio()

if __name__ == "__main__":
    with open("portfolio_structure.json", "r") as f:
        data = f.load(f)
    pb = PortfolioBuilder()