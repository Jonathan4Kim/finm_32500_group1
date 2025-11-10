"""
Shared Memory Utilities for Trading System
Provides thread-safe shared memory access for market price data across processes.
"""

import numpy as np
from multiprocessing import shared_memory, Lock
import pickle
import struct

import numpy as np
import struct
from multiprocessing import shared_memory, Lock

SYMBOL_MAX_LEN = 16    # Max characters per symbol (e.g., 'MSFT')
MAX_SYMBOLS = 20       # Maximum number of symbols the book can hold
PRICE_SIZE = 8         # Size of a float64 (8 bytes)

# Structure of the price array: (symbol string, price float)
DTYPE = np.dtype([
    ('symbol', f'S{SYMBOL_MAX_LEN}'), # Byte string for symbol
    ('price', 'f8')                    # Float64 for price
])
DATA_ARRAY_SIZE = DTYPE.itemsize * MAX_SYMBOLS 
SHM_SIZE = DATA_ARRAY_SIZE


class SharedPriceBook:
    """
    A thread-safe shared memory interface for storing and retrieving market prices.
    
    Uses a NumPy structured array stored in shared memory, allowing multiple processes
    to read and write price data efficiently with minimal serialization overhead.
    
    Attributes:
        symbols (list): List of trading symbols (e.g., ['AAPL', 'MSFT'])
        name (str): Name of the shared memory block
        shm (SharedMemory): Underlying shared memory object
        lock (Lock): Multiprocessing lock for synchronization
    """

    def __init__(self, symbols: list = None, name: str = 'price_book', create: bool = False):
        
        self.name = name
        self.shm = None
        self.symbols = None
        self.num_symbols = 0
        self.symbol_to_index = {}
        
        # --- 1. CREATION LOGIC (OrderBook/Server) ---
        if create:
            if symbols is None:
                 raise ValueError("Symbols list required when create=True")
                 
            self.symbols = symbols
            self.num_symbols = len(symbols)
            
            # 1. Create the shared memory block
            self.shm = shared_memory.SharedMemory(name=name, create=True, size=SHM_SIZE)
            
            # 2. Initialize the NumPy array on top of the shared memory buffer
            self.data_array = np.ndarray(
                shape=(MAX_SYMBOLS,), 
                dtype=DTYPE, 
                buffer=self.shm.buf
            )

            # 3. Write symbols and initial prices (CRITICAL STEP)
            for i, symbol in enumerate(symbols):
                if i < MAX_SYMBOLS:
                    # Write symbol string (encoded) and initialize price
                    self.data_array[i] = (symbol.encode('utf-8'), 0.0)
                
            self.symbol_to_index = {s: i for i, s in enumerate(self.symbols)}
            
            # Optional: Initialize a Lock in shared memory or a separate file
            self.lock = Lock() 
            print(f"SharedPriceBook '{name}' created and initialized with {self.num_symbols} symbols.")

        # --- 2. CONNECTION LOGIC (Strategy/Client) ---
        else:
            try:
                # 1. Connect to the existing shared memory block
                self.shm = shared_memory.SharedMemory(name=name, create=False)
                
                # 2. Map the existing NumPy array
                self.data_array = np.ndarray(
                    shape=(MAX_SYMBOLS,), 
                    dtype=DTYPE, 
                    buffer=self.shm.buf
                )
                
                # 3. Read symbols from memory
                self.symbols = self._read_symbols_from_memory()
                
                # 4. Initialize internal attributes
                if self.symbols:
                    self.num_symbols = len(self.symbols)
                    self.symbol_to_index = {s: i for i, s in enumerate(self.symbols)}
                    print(f"Connected to SharedPriceBook '{name}' with {self.num_symbols} symbols.")
                else:
                    self.symbols = []
                    self.num_symbols = 0
                    print(f"Connected to SharedPriceBook '{name}' but found no symbols.")
                    
            except FileNotFoundError:
                print(f"Error: SharedPriceBook '{name}' does not exist. Ensure OrderBook is running.")
                self.symbols = [] # Must be an empty list, not None, for the strategy polling loop to work.
                self.num_symbols = 0
                return # Exit constructor early

    def _read_symbols_from_memory(self) -> list:
        """
        Reads the list of symbols from the shared memory buffer by accessing the 
        symbol column of the NumPy array.
        """
        if self.data_array is None:
            return []

        # Access the 'symbol' column of the structured NumPy array
        # Get the non-empty, decoded list of symbols
        raw_symbols = self.data_array['symbol']
        
        decoded_symbols = []
        for sym_bytes in raw_symbols:
            # Decode the symbol byte string and strip any trailing null bytes
            symbol = sym_bytes.decode('utf-8').rstrip('\x00')
            if symbol:
                decoded_symbols.append(symbol)
            else:
                # Stop when we hit the first empty slot (the end of the data)
                break 
                
        return decoded_symbols
    
    def update(self, symbol: str, price: float):
        """Update the price for a given symbol in shared memory."""
        if not self.symbols:
            # Cannot update if symbols haven't been loaded/created
            return

        try:
            index = self.symbol_to_index[symbol]
            
            # Access the price field in the NumPy structured array and update it
            self.data_array[index]['price'] = price
            
        except KeyError:
            print(f"Warning: Attempted to update price for unknown symbol: {symbol}")
        except Exception as e:
            print(f"Error updating shared memory price: {e}")
    
    def read(self, symbol):
        """
        Read the current price for a given symbol.
        
        Args:
            symbol (str): Trading symbol (e.g., 'AAPL')
            
        Returns:
            float: Current price for the symbol
            
        Raises:
            KeyError: If symbol is not in the price book
        """
        if symbol not in self.symbol_to_index:
            raise KeyError(f"Symbol '{symbol}' not found in price book")
        
        with self.lock:
            idx = self.symbol_to_index[symbol]
            return float(self.prices[idx]['price'])
    
    def read_all(self):
        """
        Read all current prices as a dictionary.
        
        Returns:
            dict: Dictionary mapping symbols to prices {symbol: price}
        """
        with self.lock:
            result = {}
            for idx, symbol in enumerate(self.symbols):
                result[symbol] = float(self.prices[idx]['price'])
            return result
    
    def update_multiple(self, price_dict):
        """
        Update multiple prices atomically.
        
        Args:
            price_dict (dict): Dictionary of {symbol: price} pairs
        """
        with self.lock:
            for symbol, price in price_dict.items():
                if symbol in self.symbol_to_index:
                    idx = self.symbol_to_index[symbol]
                    self.prices[idx]['price'] = price
    
    def _read_symbols_from_memory(self) -> list:
        """
        Connects to the shared memory buffer and reads the list of symbols.
        
        NOTE: You must use the same format (offsets, length, encoding) 
        that the OrderBook used to WRITE the symbols.
        """
        if self.shm is None:
            return [] 

        try:
            return [] # Placeholder until implementation is complete
        
        except Exception as e:
            print(f"Error reading symbols from shared memory: {e}")
            return []

    def get_symbols(self):
        """
        Get the list of all symbols in the price book.
        
        Returns:
            list: List of symbol strings
        """
        return self.symbols.copy()
    
    def close(self):
        """
        Close the shared memory connection.
        Should be called by processes that attach to existing memory.
        """
        self.shm.close()
    
    def unlink(self):
        """
        Unlink (delete) the shared memory block.
        Should only be called by the process that created the memory.
        """
        self.shm.unlink()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically closes shared memory."""
        self.close()
    
    def __repr__(self):
        """String representation of the price book."""
        return f"SharedPriceBook(name='{self.name}', symbols={self.symbols})"


class SharedMemoryMetadata:
    """
    Helper class to share metadata (like shared memory name) between processes.
    Uses a small shared memory block to store serialized metadata.
    """
    
    METADATA_SIZE = 1024  # 1KB should be enough for metadata
    
    def __init__(self, name="trading_metadata", create=True):
        """
        Initialize metadata storage.
        
        Args:
            name (str): Name of the metadata shared memory block
            create (bool): If True, create new memory. If False, attach to existing.
        """
        self.name = name
        
        if create:
            self.shm = shared_memory.SharedMemory(
                create=True,
                size=self.METADATA_SIZE,
                name=name
            )
        else:
            self.shm = shared_memory.SharedMemory(name=name)
    
    def write(self, data):
        """
        Write metadata dictionary to shared memory.
        
        Args:
            data (dict): Metadata to store
        """
        serialized = pickle.dumps(data)
        size = len(serialized)
        
        if size > self.METADATA_SIZE - 4:
            raise ValueError(f"Metadata too large: {size} bytes (max: {self.METADATA_SIZE - 4})")
        
        # Write size header (4 bytes) followed by data
        self.shm.buf[0:4] = struct.pack('I', size)
        self.shm.buf[4:4+size] = serialized
    
    def read(self):
        """
        Read metadata dictionary from shared memory.
        
        Returns:
            dict: Stored metadata
        """
        # Read size header
        size = struct.unpack('I', bytes(self.shm.buf[0:4]))[0]
        
        if size == 0:
            return {}
        
        # Read and deserialize data
        serialized = bytes(self.shm.buf[4:4+size])
        return pickle.loads(serialized)
    
    def close(self):
        """Close the shared memory connection."""
        self.shm.close()
    
    def unlink(self):
        """Unlink (delete) the shared memory block."""
        self.shm.unlink()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()