"""
Shared Memory Utilities for Trading System
Provides thread-safe shared memory access for market price data across processes.
"""

import numpy as np
from multiprocessing import shared_memory, Lock
import pickle
import struct


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
    
    def __init__(self, symbols, name=None, create=True):
        """
        Initialize the shared price book.
        
        Args:
            symbols (list): List of symbol strings (e.g., ['AAPL', 'MSFT', 'GOOGL'])
            name (str, optional): Name for the shared memory block. If None, auto-generated.
            create (bool): If True, create new shared memory. If False, attach to existing.
        """
        self.symbols = symbols
        self.symbol_to_index = {symbol: idx for idx, symbol in enumerate(symbols)}
        self.num_symbols = len(symbols)
        
        # Define structured dtype: symbol (fixed string) and price (float)
        # Using S10 for symbol names (up to 10 characters)
        self.dtype = np.dtype([('symbol', 'S10'), ('price', 'f8')])
        self.array_size = self.dtype.itemsize * self.num_symbols
        
        self.lock = Lock()
        
        if create:
            # Create new shared memory block
            self.shm = shared_memory.SharedMemory(
                create=True,
                size=self.array_size,
                name=name
            )
            self.name = self.shm.name
            
            # Initialize the numpy array in shared memory
            self._initialize_array()
        else:
            # Attach to existing shared memory
            if name is None:
                raise ValueError("Must provide name when create=False")
            self.name = name
            self.shm = shared_memory.SharedMemory(name=name)
        
        # Create numpy array view of shared memory
        self.prices = np.ndarray(
            shape=(self.num_symbols,),
            dtype=self.dtype,
            buffer=self.shm.buf
        )
    
    def _initialize_array(self):
        """Initialize the shared memory array with default values."""
        temp_array = np.ndarray(
            shape=(self.num_symbols,),
            dtype=self.dtype,
            buffer=self.shm.buf
        )
        
        for idx, symbol in enumerate(self.symbols):
            temp_array[idx]['symbol'] = symbol.encode('utf-8')
            temp_array[idx]['price'] = 0.0
    
    def update(self, symbol, price):
        """
        Update the price for a given symbol in shared memory.
        
        Args:
            symbol (str): Trading symbol (e.g., 'AAPL')
            price (float): New price value
            
        Raises:
            KeyError: If symbol is not in the price book
        """
        if symbol not in self.symbol_to_index:
            raise KeyError(f"Symbol '{symbol}' not found in price book")
        
        with self.lock:
            idx = self.symbol_to_index[symbol]
            self.prices[idx]['price'] = price
    
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