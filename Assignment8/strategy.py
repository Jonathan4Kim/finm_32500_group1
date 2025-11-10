from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime
from dataclasses import dataclass
import socket
import threading
import json
import time
from typing import List, Dict, Any, Optional

from shared_memory_utils import SharedPriceBook, SharedMemoryMetadata
from order_manager import OrderManagerServer, MESSAGE_DELIMITER


@dataclass(frozen=True)
class MarketDataPoint:
    # create timestamp, symbol, and price instances with established types
    timestamp: datetime
    symbol: str
    price: float

@dataclass(frozen=True)
class SentimentDataPoint:
    # create timestamp, symbol, and price instances with established types
    timestamp: datetime
    symbol: str
    sentiment: int

# --- Configuration for gateway.py Sentiment Stream ---
SENTIMENT_HOST = '127.0.0.1'
SENTIMENT_PORT = 9002
SENTIMENT_DELIMITER = b'*'

# --- Configuration for order_manager.py ---
ORDER_HOST = '127.0.0.1'
ORDER_PORT = 62000
ORDER_DELIMITER = b'*'


class Strategy(ABC):
    pass


class _SymbolState:
    """
    Holds the independent state for a single symbol's Moving Average calculation.
    """
    def __init__(self, s: int, l: int):
        self.dq_long = deque([])   # deque for long window
        self.dq_short = deque([])  # deque for short window
        self.size = 0
        self.short_sum = 0.0
        self.long_sum = 0.0
        self.short_window = s
        self.long_window = l


class WindowedMovingAverageStrategy(Strategy):
    """
    Initializes Windowed Moving Average Strategy, managing state per symbol.
    """
    def __init__(self, s: int, l: int):
        """
        Initializes the strategy with fixed short (s) and long (l) window sizes.
        
        Args:
            s (int): short window length
            l (int): long window length
        """
        if s >= l:
            raise ValueError("Short window (s) must be less than long window (l).")
            
        # These are now config parameters, not state.
        self.__short_window = s
        self.__long_window = l
        
        # Dictionary to store the unique state for each symbol.
        # Key: Symbol (str) -> Value: _SymbolState
        self.__symbol_states: Dict[str, _SymbolState] = {}


    def __get_or_init_state(self, symbol: str) -> _SymbolState:
        """
        Retrieves the state for a symbol, initializing it if not present.
        """
        if symbol not in self.__symbol_states:
            self.__symbol_states[symbol] = _SymbolState(
                self.__short_window, 
                self.__long_window
            )
        return self.__symbol_states[symbol]


    def generate_signals(self, tick: MarketDataPoint) -> List[str]:
        """
        Computes the moving average and generates signals for the given symbol.

        Args:
            tick (MarketDataPoint): A single MarketDataPoint, with 
            timestamp, price, and symbol attributes

        Returns:
            list[str]: a signal denoting whether to buy, sell, or hold
        """
        
        # 1. Retrieve or initialize the state specific to this symbol
        state = self.__get_or_init_state(tick.symbol)
        
        # Use state attributes instead of instance attributes (self.__...)
        price = tick.price
        
        # 2. Initial Filling of Deques
        if state.size < state.long_window:
            
            # If we have enough values for the short window (or more)
            if state.size >= state.long_window - state.short_window:
                state.short_sum += price
                state.dq_short.append(price)

            # Always add to the long window
            state.long_sum += price
            state.dq_long.append(price)

            state.size += 1
            
            # Hold until the long window is full
            return ["HOLD"]

        # 3. Moving Average Calculation (O(1) updates)
        
        # Compute current averages
        short_avg = state.short_sum / state.short_window
        long_avg = state.long_sum / state.long_window
        
        # Remove oldest elements from sums and deques
        # The long deque is guaranteed to be full here
        state.long_sum -= state.dq_long.popleft()
        
        # The short deque will be full if the long window is full, but we need
        # to ensure we only remove from it if it has reached its capacity.
        # Note: Given the fill logic, dq_short's size should be state.short_window here.
        state.short_sum -= state.dq_short.popleft()

        # Add the new price to both deques and sums
        state.dq_long.append(price)
        state.long_sum += price

        state.dq_short.append(price)
        state.short_sum += price

        # 4. Signal Generation (O(1) comparison)
        if short_avg > long_avg:
            return "BUY"
        elif short_avg < long_avg:
            return "SELL"
        else:
            return "HOLD"
        

class SentimentStrategy(Strategy):
    
    def __init__(self):
        super().__init__()

    def generate_signal(self, tick: SentimentDataPoint):
        if tick.sentiment > 50:
            return "BUY"
        elif tick.sentiment < 50:
            return "SELL"
        else:
            return "HOLD"


def initialize_strategy_book():
    # 1. Attach to the Metadata Shared Memory
    try:
        metadata_book = SharedMemoryMetadata(name="trading_metadata", create=False)
        metadata = metadata_book.read()
        metadata_book.close()
        
        # Extract the necessary data
        symbols = metadata.get('symbols')
        price_book_name = metadata.get('price_book_name')
        
        if not symbols or not price_book_name:
            raise ValueError("Metadata is incomplete or missing.")

        print(f"Symbols retrieved from metadata: {symbols}")
        
        # 2. Use the retrieved symbols to attach to the main SharedPriceBook
        strategy_book = SharedPriceBook(
            symbols=symbols,
            name=price_book_name,
            create=False  # Attach to existing
        )
        print("Strategy successfully attached to SharedPriceBook.")
        return strategy_book
        
    except FileNotFoundError:
        print("Error: Required shared memory segment not found. Check if the OrderBook process is running.")
        return None
    except Exception as e:
        print(f"Initialization error: {e}")
        return None
    

def send_order(order_dict):
    """Utility: send a single order and return the server's ACK."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ORDER_HOST, ORDER_PORT))
        payload = json.dumps(order_dict).encode("utf-8") + MESSAGE_DELIMITER
        s.sendall(payload)

        # Receive until delimiter
        data = b""
        while MESSAGE_DELIMITER not in data:
            chunk = s.recv(1024)
            if not chunk:
                break
            data += chunk
        frame, *_ = data.split(MESSAGE_DELIMITER, 1)
        return json.loads(frame.decode("utf-8"))

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", SENTIMENT_PORT))
    sent_points = []

    price_book = initialize_strategy_book()

    sent_strategy = SentimentStrategy()
    ma_strategy = WindowedMovingAverageStrategy(s=5, l=20)
    
    while True:
        try:
            response = client.recv(1024)
            if not response:
                break
            
            # Decode and split response
            response = response.decode().split("*")[:-1]
            print('response occurring')
            print(response)
            # Parse market data point
            sdp = SentimentDataPoint(
                datetime.strptime(response[0], "%Y-%m-%d %H:%M:%S"), 
                response[1], 
                float(response[2])
            )
            symbol = response[1]
            sent_points.append(sdp)
            print('sentiment point added!')

            sent_signal = sent_strategy.generate_signal(sdp)

            if price_book:
                price = price_book.read(symbol)
                tick = MarketDataPoint(
                    datetime.strptime(response[0], "%Y-%m-%d %H:%M:%S"), 
                    symbol, 
                    price
                )

            ma_signal = ma_strategy.generate_signals(tick)

            if sent_signal == ma_signal:
                signal = sent_signal
                my_order = {
                    "side": signal,
                    "symbol": symbol,
                    "qty": 10,
                    "price": price
                }

                try:
                    print(f"Attempting to send order: {my_order}")
                    
                    # Call the utility function
                    acknowledgment = send_order(my_order)
                    
                    # 3. Print the Server's Acknowledgment
                    if acknowledgment.get("ok"):
                        print("\nOrder successfully acknowledged by the server!")
                        print(f"Server-assigned ID: {acknowledgment['order']['id']}")
                        print(f"Full ACK details: {acknowledgment}")
                    else:
                        print("\nOrder rejected by the server.")
                        print(f"Rejection details: {acknowledgment.get('error', 'No error message provided')}")

                except ConnectionRefusedError:
                    print("\nConnection Error: Could not connect to the order manager.")
                    print(f"Please ensure the order manager server is running on {ORDER_HOST}:{ORDER_PORT}.")
                except Exception as e:
                    print(f"\nFatal error during order transmission: {e}")

        except Exception as e:
            print(f'Error: {e}')
            break

if __name__ == "__main__":
    main()