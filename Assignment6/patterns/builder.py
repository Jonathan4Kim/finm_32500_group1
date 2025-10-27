import json

class Portfolio:
    def __init__(self, name, positions, sub_portfolios=None, owner=""):
        self.name = name
        self.positions = positions
        self.sub_portfolios = sub_portfolios if sub_portfolios else []
        self.owner = owner

class PortfolioBuilder:
    def __init__(self, name):
        self.positions = []
        self.subportfolios = []
        self.name = name
        self.owner = ""

    def add_position(self, symbol, quantity, price):
        self.positions.append({"symbol": symbol, "quantity": quantity, "price": price})

    def set_owner(self, name):
        self.owner = name
    
    def add_subportfolio(self, builder):
        self.subportfolios.append(builder)
    
    def build(self):
        built_subs = [builder.build() for builder in self.subportfolios]
        return Portfolio(self.name, self.positions, built_subs, self.owner)

# if __name__ == "__main__":
#     with open("portfolio_structure.json", "r") as f:
#         data = json.load(f)
#
#     pb = PortfolioBuilder(data["name"])
#     for pos in data["positions"]:
#         pb.add_position(pos["symbol"], pos["quantity"], pos["price"])
#     pb.set_owner(data["owner"])
#
#     for sub in data["sub_portfolios"]:
#         sub_builder = PortfolioBuilder(sub["name"])
#         for pos in sub["positions"]:
#             sub_builder.add_position(pos["symbol"], pos["quantity"], pos["price"])
#         pb.add_subportfolio(sub_builder)
#
#     portfolio = pb.build()