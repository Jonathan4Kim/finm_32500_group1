"""TODO: Implement OrderBook process for Assignment 8."""
import socket, select
import asyncio
from datetime import datetime
from dataclasses import dataclass
from shared_memory_utils import SharedPriceBook

@dataclass(frozen=True)
class MarketDataPoint:
    # create timestamp, symbol, and price instances with established types
    timestamp: datetime
    symbol: str
    price: float


def get_price_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 9001))
    data_points = []
    book = None  # Will initialize after receiving symbols
    
    while True:
        try:
            response = client.recv(1024)
            if not response:
                break
            
            # Decode and split response
            response = response.decode().split("*")[:-1]
            print('response occurring')
            print(response)
            
            # First message: symbol list
            if response[0].startswith('SYMBOLS|'):
                symbols_str = response[0].split('|')[1]
                unique_symbols = symbols_str.split(',')
                print(f'Received symbols: {unique_symbols}')
                
                try:
                    SharedPriceBook.unlink() 
                    print(f"Cleaned up old shared memory segment")
                except FileNotFoundError:
                    # Ignore if the file didn't exist
                    pass
                except Exception as cleanup_e:
                    # Catch other potential errors during cleanup
                    print(f"Warning during cleanup: {cleanup_e}")
                
                # Initialize SharedPriceBook with the symbol list
                book = SharedPriceBook(symbols=unique_symbols, name='price_book', create=True)
                print('SharedPriceBook initialized!')
                continue
            
            # Subsequent messages: price data
            if book is None:
                print('Warning: Received price data before symbol list')
                continue
            
            # Parse market data point
            mdp = MarketDataPoint(
                datetime.strptime(response[0], "%Y-%m-%d %H:%M:%S"), 
                response[1], 
                float(response[2])
            )
            data_points.append(mdp)
            print('data point added!')
            
            # Update SharedPriceBook
            book.update(response[1], float(response[2]))
            print('Shared Price Book updated!')
            
        except Exception as e:
            print(f'Error: {e}')
            break
    
    # Cleanup
    if book:
        book.close()
    client.close()
    
    print(data_points)
    return data_points
    

def main():
    data_points = get_price_client()
    print(data_points)
    print(len(data_points))


if __name__ == '__main__':
    main()