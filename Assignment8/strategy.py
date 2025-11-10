from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime
from dataclasses import dataclass
from shared_memory_utils import SharedPriceBook
import socket
import threading
import json
import time
from typing import List, Dict, Any, Optional

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

BOOK_NAME = 'price_book'

# Strategy Parameters
SHORT_WINDOW = 5
LONG_WINDOW = 20
ORDER_QTY = 100


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
            return ["BUY"]
        elif short_avg < long_avg:
            return ["SELL"]
        else:
            return ["HOLD"]


class SentimentStrategy(Strategy):
    
    def __init__(self):
        super().__init__()
    
    
    def generate_signals(self, tick):

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", SENTIMENT_PORT))
        sent_points = []
        
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
                sent_points.append(sdp)
                print('sentiment point added!')

            except Exception as e:
                print(f'Error: {e}')
                break

        return super().generate_signals(tick)
    
class MAStrategyRunner:
    def __init__(self, book):
        self.book = book
        self.strategy = WindowedMovingAverageStrategy(SHORT_WINDOW, LONG_WINDOW)
        self.order_sock: Optional[socket.socket] = None
        self._stop_event = threading.Event()
        # Tracks the last processed timestamp to only run the strategy on new ticks
        self.last_processed_ts: Dict[str, str] = {}
        
    def connect_ordermanager(self):
        """Connects to the Order Manager server."""
        self.order_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.order_sock.connect((ORDER_HOST, ORDER_PORT))
        self.order_sock.settimeout(2.0)
        print(f"Order Manager Connected at {ORDER_HOST}:{ORDER_PORT}.")

    def send_order(self, symbol: str, side: str, price: float):
        """Formats and sends an order request to the Order Manager."""
        if not self.order_sock: return
        
        order_payload = {
            "side": side,
            "symbol": symbol,
            "qty": ORDER_QTY,
            "price": price,
            "ts": time.time(),
        }
        try:
            # Order Manager expects JSON object + delimiter
            json_order = json.dumps(order_payload).encode('utf-8')
            self.order_sock.sendall(json_order + ORDER_DELIMITER)
            print(f"  [ORDER SENT] {side} {ORDER_QTY} {symbol} @ {price:.2f}")
        except Exception as e:
            print(f"Error sending order: {e}")
            self._stop_event.set()

    def run_strategy_cycle(self):
        """
        Iterates over all symbols in the price book and runs the strategy
        if the price has updated since the last run.
        """
        symbols = self.book.get_all_symbols()
        
        for symbol in symbols:
            latest_point = self.book.get_price(symbol)
            if not latest_point:
                continue

            # Check if this tick is newer than the last one processed
            if latest_point.timestamp != self.last_processed_ts.get(symbol):
                
                # 1. Generate Signal
                signals = self.strategy.generate_signals(latest_point)
                
                # 2. Execute on Signal
                signal = signals[0]
                
                if signal != "HOLD":
                    self.send_order(latest_point.symbol, signal, latest_point.price)
                
                # 3. Update the last processed timestamp
                self.last_processed_ts[symbol] = latest_point.timestamp

    def _run_ack_listener(self):
        """Listens for and processes ACKs from the Order Manager."""
        ack_buffer = b''
        try:
            while not self._stop_event.is_set():
                chunk = self.order_sock.recv(RECV_BYTES)
                if not chunk: break
                ack_buffer += chunk
                while ORDER_DELIMITER in ack_buffer:
                    ack_frame, ack_buffer = ack_buffer.split(ORDER_DELIMITER, 1)
                    ack = json.loads(ack_frame.decode('utf-8'))
                    ok = ack.get('ok')
                    order_id = ack.get('order', {}).get('id', 'N/A')
                    msg = ack.get('msg', 'N/A')
                    if ok:
                        print(f"  [ACK] Order {order_id} OK.")
                    else:
                        print(f"  [REJECT] Order {order_id} Failed: {msg}")
        except Exception:
            pass
        self._stop_event.set()


    def start(self):
        """Establishes connections and starts the strategy cycle."""
        try:
            self.connect_ordermanager()
            
            # Start ACK listener thread
            threading.Thread(target=self._run_ack_listener, daemon=True).start()
            
            print(f"\n--- Strategy Runner Started ({SHORT_WINDOW}/{LONG_WINDOW} MA) ---")
            
            # Main strategy loop
            while not self._stop_event.is_set():
                self.run_strategy_cycle()
                time.sleep(0.01) # Poll the book frequently
                
        except Exception as e:
            print(f"\nStrategy Runner failed: {e}")
        finally:
            self.stop()

    def stop(self):
        self._stop_event.set()
        if self.order_sock:
            self.order_sock.close()
        print("\nStrategy Runner Stopped.")


if __name__ == "__main__":
    try:
        # Attempt to access a globally available object named 'price_book'
        book = SharedPriceBook(name='price_book', create=False)
    except KeyError:
        # Create a mock book if running standalone for testing the MA logic
        print("WARNING: 'price_book' not found in globals.")

    runner = MAStrategyRunner(book)
    try:
        runner.start()
    except KeyboardInterrupt:
        runner.stop()