from abc import ABC, abstractmethod
from datetime import datetime

# Abstract Observer
class Observer(ABC):
    """Abstract base class for observers"""
    
    @abstractmethod
    def update(self, signal: dict):
        """
        Called when a signal is generated
        
        Args:
            signal: Dictionary containing signal data
                   e.g., {"action": "BUY", "symbol": "AAPL", "quantity": 100}
        """
        pass


# Signal Publisher
class SignalPublisher:
    """Manages observers and notifies them of signals"""
    
    def __init__(self):
        # Initialize list to store observers
        self._observers = []
    
    def attach(self, observer: Observer):
        """
        Register an observer to receive notifications
        
        Args:
            observer: Observer instance to add
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Observer):
        """
        Unregister an observer
        
        Args:
            observer: Observer instance to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, signal: dict):
        """
        Notify all observers about a new signal
        
        Args:
            signal: Signal dictionary to send to observers
        """
        for observer in self._observers:
            observer.update(signal)


# Logger 
class LoggerObserver(Observer):
    """Logs all signals to console or file"""
    
    def __init__(self, log_file: str = None):
        """
        Args:
            log_file: Optional file path to write logs. If None, prints to console
        """
        self.log_file = log_file
        self.logs = []
    
    def update(self, signal: dict):
        """
        Log the signal
        
        Args:
            signal: Signal dictionary
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] SIGNAL: {signal['action']} {signal['quantity']} shares of {signal['symbol']}"
        
        if self.log_file:
            self.logs.append(message)
            with open(self.log_file, "a") as f:
                f.write(message + "\n")
        else:
            print(message)
            self.logs.append(message)


# Alert
class AlertObserver(Observer):
    """Alerts when trade size exceeds threshold"""
    
    def __init__(self, quantity_threshold: int = 500):
        """
        Args:
            quantity_threshold: Alert if quantity exceeds this value
        """
        self.quantity_threshold = quantity_threshold
        self.alerts = []
    
    def update(self, signal: dict):
        """
        Check if signal quantity exceeds threshold and alert
        
        Args:
            signal: Signal dictionary
        """
        quantity = signal.get("quantity", 0)
        
        if quantity > self.quantity_threshold:
            message = f"Large Trade Alert: {signal['action']} {quantity} shares of {signal['symbol']}"
            print(message)
            self.alerts.append(message)