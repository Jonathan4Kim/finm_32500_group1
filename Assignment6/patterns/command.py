from abc import ABC, abstractmethod

# Abstract Command
class Command(ABC):
    @abstractmethod
    def execute(self):
        pass
    
    @abstractmethod
    def undo(self):
        pass


# Execute Order Command 
class ExecuteOrderCommand(Command):
    def __init__(self, portfolio, signal: dict):
        self.portfolio = portfolio
        self.signal = signal
    
    def execute(self):
        action = self.signal['action']
        symbol = self.signal['symbol']
        quantity = self.signal['quantity']
        
        if action == "BUY":
            self.portfolio.buy(symbol, quantity)
        elif action == "SELL":
            self.portfolio.sell(symbol, quantity)
    
    def undo(self):
        action = self.signal['action']
        symbol = self.signal['symbol']
        quantity = self.signal['quantity']
        
        # Reverse the action
        if action == "BUY":
            self.portfolio.sell(symbol, quantity)
        elif action == "SELL":
            self.portfolio.buy(symbol, quantity)


# Undo Order Command 
class UndoOrderCommand(Command):
    def __init__(self, original_command: ExecuteOrderCommand):
        self.original_command = original_command
    
    def execute(self):
        # Execute means undoing the original command
        self.original_command.undo()
    
    def undo(self):
        # Undo means re-executing the original command
        self.original_command.execute()


# Command Invoker
class CommandInvoker:
    def __init__(self):
        self.history = []
        self.redo_stack = []
    
    def execute_command(self, command: Command):
        # Execute command, record it in history, clear redo stack
        command.execute()
        self.history.append(command)
        self.redo_stack.clear()
    
    def undo(self):
        # Undo the last command
        if not self.history:
            print("Nothing to undo.")
            return
        command = self.history.pop()
        command.undo()
        self.redo_stack.append(command)
    
    def redo(self):
        # Redo the last undone command
        if not self.redo_stack:
            print("Nothing to redo.")
            return
        command = self.redo_stack.pop()
        command.execute()
        self.history.append(command)


# Portfolio
class Portfolio:
    def __init__(self):
        self.positions = {}
    
    def buy(self, symbol: str, quantity: int):
        if symbol not in self.positions:
            self.positions[symbol] = 0
        self.positions[symbol] += quantity
        print(f"Bought {quantity} shares of {symbol}. Current position: {self.positions[symbol]}")
    
    def sell(self, symbol: str, quantity: int):
        if symbol not in self.positions:
            self.positions[symbol] = 0
        self.positions[symbol] -= quantity
        print(f"Sold {quantity} shares of {symbol}. Current position: {self.positions[symbol]}")
    
    def get_position(self, symbol: str) -> int:
        return self.positions.get(symbol, 0)