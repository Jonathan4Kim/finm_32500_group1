"""
Threaded OrderBook client — simplest working version
Keeps your original work untouched.
"""

import socket, select
from datetime import datetime
from dataclasses import dataclass
import threading

@dataclass(frozen=True)
class MarketDataPoint:
    timestamp: datetime
    symbol: str
    price: float


# storage for price points and sentiment points
price_points = []
sentiment_points = []
price_done = False
sentiment_done = False

def price_reader():
    global price_done
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 9001))
    buffer = ""

    while True:
        data = client.recv(1024)
        if not data:
            break
        buffer += data.decode()

        # Extract complete messages ending with "*"
        while "*" in buffer:
            msg, buffer = buffer.split("*", 1)
            if not msg.strip():
                continue
            parts = msg.split("*")
            if len(parts) == 3:
                ts, sym, price = parts
                try:
                    mdp = MarketDataPoint(
                        datetime.strptime(ts, "%Y-%m-%d %H:%M:%S"),
                        sym,
                        float(price)
                    )
                    price_points.append(mdp)
                    print(f"[PRICE] {mdp}")
                except Exception as e:
                    print(f"[PRICE PARSE ERROR] {e}")

    price_done = True
    client.close()


def sentiment_reader():
    global sentiment_done
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 9002))
    buffer = ""

    while True:
        data = client.recv(1024)
        if not data:
            break
        buffer += data.decode()

        while "*" in buffer:
            msg, buffer = buffer.split("*", 1)
            if msg.strip():
                try:
                    val = int(msg.strip())
                    sentiment_points.append(val)
                    print(f"[SENTIMENT] {val}")
                except Exception as e:
                    print(f"[SENT PARSE ERROR] {e}")

    sentiment_done = True
    client.close()
    
def both():
    # create client 1 for price sockets
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 9001))
    client.setblocking(False)
    
    # create client 2 for sentiment socket
    client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client2.connect(("localhost", 9002))
    client2.setblocking(False)
    
    # store the data points and sentiment points here
    data_points = []
    sent_points = []
    
    # buff
    price_buffer = ""
    sent_buffer = ""
    MESSAGE_DELIMITER = '*'
    
    price_done = False
    sent_done = False
    
    import time
    
    while not (price_done and sent_done):
        # Use select to handle both sockets
        readable = []
        writable = []
        
        if not price_done:
            writable.append(client)
            readable.append(client)
        if not sent_done:
            writable.append(client2)
            readable.append(client2)
        
        r, w, _ = select.select(readable, writable, [], 0.1)
        
        # Send requests to servers that are ready
        if client in w and not price_done:
            try:
                client.send(b"READY")
            except:
                pass
                
        if client2 in w and not sent_done:
            try:
                client2.send(b"READY")
            except:
                pass
        
        # Receive from servers that have data
        if client in r and not price_done:
            try:
                response = client.recv(1024)
                if not response:
                    price_done = True
                    print("Price stream complete")
                else:
                    price_buffer += response.decode()
                    
                    # Process complete messages
                    while MESSAGE_DELIMITER in price_buffer:
                        message, price_buffer = price_buffer.split(MESSAGE_DELIMITER, 1)
                        if message:
                            parts = message.split("*")
                            mdp = MarketDataPoint(
                                datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S"),
                                parts[1],
                                float(parts[2])
                            )
                            data_points.append(mdp)
                            print(f'Data point added: {mdp.symbol} @ {mdp.price}')
            except BlockingIOError:
                pass
            except Exception as e:
                print(f"Price error: {e}")
                price_done = True
        
        if client2 in r and not sent_done:
            try:
                response2 = client2.recv(1024)
                if not response2:
                    sent_done = True
                    print("Sentiment stream complete")
                else:
                    sent_buffer += response2.decode()
                    
                    # Process complete messages
                    while MESSAGE_DELIMITER in sent_buffer:
                        message, sent_buffer = sent_buffer.split(MESSAGE_DELIMITER, 1)
                        if message:
                            sentiment = int(message)
                            sent_points.append(sentiment)
                            print(f'Sentiment received: {sentiment}')
            except BlockingIOError:
                pass
            except Exception as e:
                print(f"Sentiment error: {e}")
                sent_done = True
        
        time.sleep(0.05)  # Small delay to avoid busy waiting
    
    client.close()
    client2.close()
    return data_points, sent_points


def main():
    data_points, sentiments = both()
    print(data_points)
    print(sentiments)
    print(len(data_points))
    print(len(sentiments))


if __name__ == "__main__":
    main()