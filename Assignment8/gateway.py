"""

gateway.py

Responsible for Streaming Price & Sentiment data
via TCP. Will be a server that listens on two ports.

1. price stream
2. News sentiment stream

It will generate random prices and produce sentiment values 
as well. It will send these streams out via TCP sockets (price stream and
sentiment stream).

This will be tested independently to ensure that other processes will have a real
data source to consume.

Theoretically 

"""
import random
import socket, random, select
import csv
from datetime import datetime
import time
import pandas as pd


def load_data():
    """
    Gets the datapoints from market_data.csv and formats them.
    Also extracts unique symbols in order of first appearance.
    
    Returns:
        tuple: (data_points list, unique_symbols list)
    """
    data_points = []
    sent_points = []
    unique_symbols = []
    seen_symbols = set()
    
    with open('market_data.csv', newline="") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader)  # Skip header
        
        for row in reader:
            timestamp = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            symbol = row[1]
            price = float(row[2])
            
            # Track unique symbols in order of first appearance
            if symbol not in seen_symbols:
                unique_symbols.append(symbol)
                seen_symbols.add(symbol)
            
            # Format: timestamp*symbol*price
            mdp = f"{timestamp}*{symbol}*{price}".encode()
            sdp = f"{timestamp}*{symbol}*{random.randint(0, 100)}".encode()
            data_points.append(mdp)
            sent_points.append(sdp)
    
    return data_points, unique_symbols, sent_points


def send_symbol_list(client, symbols, delimiter):
    """
    Send the list of symbols to a newly connected client.
    Format: SYMBOLS|AAPL,MSFT,SPY*
    
    Args:
        client: Socket connection
        symbols: List of symbol strings
        delimiter: Message delimiter
    """
    try:
        symbol_message = f"SYMBOLS|{','.join(symbols)}".encode() + delimiter
        client.send(symbol_message)
        print(f"Sent symbol list to client: {symbols}")
        return True
    except Exception as e:
        print(f"Error sending symbol list: {e}")
        return False


def main():
    # Load data and extract unique symbols in one pass
    data_points, unique_symbols, sent_points = load_data()
    n = len(data_points)
    
    print(f"Loaded {n} data points")
    print(f"Unique symbols: {unique_symbols}")
    
    # MESSAGE DELIMITER
    MESSAGE_DELIMITER = b'*'
    
    # ESTABLISH HOSTS AND PORTS
    HOST = '127.0.0.1'
    PRICE_PORT = 9001
    SENT_PORT = 9002
    
    # Create price server
    price_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    price_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    price_server.bind(("localhost", PRICE_PORT))
    price_server.listen()
    price_server.setblocking(False)
    
    # Create sentiment server
    sent_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sent_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sent_server.bind(("localhost", SENT_PORT))
    sent_server.listen()
    sent_server.setblocking(False)
    
    # Track server sockets and clients
    server_sockets = [price_server, sent_server]
    price_clients = []
    price_clients_ready = []  # Track which clients received symbol list
    sent_clients = []
    
    # Data streaming indices
    i = 0  # Price data index
    j = 0  # Sentiment data index
    
    while i < n or j < n:
        print(f"Server running... data index: {i}/{n}")
        
        # Accept new client connections
        readable, _, _ = select.select(server_sockets, [], [], 0.1)
        
        for sock in readable:
            if sock is price_server:
                conn, _ = price_server.accept()
                conn.setblocking(False)
                price_clients.append(conn)
                
                # Send symbol list immediately to new client
                if send_symbol_list(conn, unique_symbols, MESSAGE_DELIMITER):
                    price_clients_ready.append(conn)
                    print("Price client connected and initialized")
                else:
                    price_clients.remove(conn)
                    conn.close()
            
            elif sock is sent_server:
                conn, _ = sent_server.accept()
                conn.setblocking(False)
                sent_clients.append(conn)
                print("Sentiment client connected")
        
        # Stream price data to ready clients
        if i < n and price_clients_ready:
            disconnected = []
            for client in price_clients_ready:
                try:
                    encoded_data = data_points[i] + MESSAGE_DELIMITER
                    client.send(encoded_data)
                    print(f"Price data sent: {encoded_data}")
                except Exception as e:
                    print(f"Error sending to price client: {e}")
                    disconnected.append(client)
            
            # Clean up disconnected clients
            for client in disconnected:
                if client in price_clients_ready:
                    price_clients_ready.remove(client)
                if client in price_clients:
                    price_clients.remove(client)
                client.close()
            
            i += 1
            time.sleep(0.1)
        
        # Stream sentiment data
        if j < n and sent_clients:
            disconnected = []
            for client in sent_clients:
                try:
                    encoded_data = sent_points[i] + MESSAGE_DELIMITER
                    client.send(encoded_data)
                    print(f"Sentiment data sent: {encoded_data}")
                except Exception as e:
                    print(f"Error sending to sentiment client: {e}")
                    disconnected.append(client)
            
            # Clean up disconnected clients
            for client in disconnected:
                sent_clients.remove(client)
                client.close()
            
            j += 1
            time.sleep(0.1)
    
    # All data sent, close connections
    print("All data sent, closing connections")
    for client in price_clients:
        client.close()
    for client in sent_clients:
        client.close()
    price_server.close()
    sent_server.close()


if __name__ == "__main__":
    main()

