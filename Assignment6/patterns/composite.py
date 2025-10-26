from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import json

# Abstract Component
class PortfolioComponent(ABC):
    @abstractmethod
    def get_value(self) -> float:
        pass

    @abstractmethod
    def get_positions(self) -> List[str]:
        pass


# Leaf Node: Position
@dataclass
class Position(PortfolioComponent):
    symbol: str
    quantity: float
    price: float

    def get_value(self) -> float:
        return self.quantity * self.price

    def get_positions(self) -> List[str]:
        return [self.symbol]


#  Composite Node: PortfolioGroup
class PortfolioGroup(PortfolioComponent):
    def __init__(self, name: str, owner: Optional[str] = None):
        self.name = name
        self.owner = owner
        self.positions: List[Position] = []
        self.sub_portfolios: List["PortfolioGroup"] = []

    def add_position(self, position: Position):
        self.positions.append(position)

    def remove_position(self, symbol: str, quantity: float):
        # Try to sell from current portfolio positions
        for position in list(self.positions):  # copy since we may modify
            if position.symbol == symbol:
                if quantity >= position.quantity:
                    # Sell all — remove the position completely
                    self.positions.remove(position)
                    return True
                else:
                    # Partial sale — reduce quantity
                    position.quantity -= quantity
                    return True

        # Symbol not found anywhere
        return False

    def add_sub_portfolio(self, sub_portfolio: "PortfolioGroup"):
        self.sub_portfolios.append(sub_portfolio)

    def get_value(self) -> float:
        total = sum(p.get_value() for p in self.positions)
        total += sum(s.get_value() for s in self.sub_portfolios)
        return total

    def get_positions(self) -> List[str]:
        pos = [p.symbol for p in self.positions]
        for s in self.sub_portfolios:
            pos.extend(s.get_positions())
        return pos


def build_portfolio(data) -> PortfolioGroup:
    group = PortfolioGroup(name=data["name"], owner=data.get("owner"))

    # Add positions
    for p in data.get("positions", []):
        group.add_position(Position(symbol=p["symbol"], quantity=p["quantity"], price=p["price"]))

    # Add sub-portfolios
    for sp in data.get("sub_portfolios", []):
        group.add_sub_portfolio(build_portfolio(sp))

    return group


if __name__ == "__main__":
    with open("portfolio_structure.json") as f:
        data = json.load(f)

    portfolio = build_portfolio(data)

    print("Total portfolio value:", portfolio.get_value())
    print("All positions:", portfolio.get_positions())
