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

def load_data():
    """
    Gets the datapoints from market_data.csv,
    and for each row,
    converts each part of the row into its respective 
    datatype for the MarketDataPoint object.
    stores all of those instances into the 
    data_points array to be returned

    Returns:
        _type_: _description_
    
    Runtime Complexity: O(n)
    
    Space Complexity: O(n): with n MarketDataPoints being created (O(1) time to create each object with 3 attributes)
    from n rows. We add it to data points list, which takes O(1) time amortized in Python.
    """
    # create data point storage  O(1)
    data_points = []

    # open the csv file O(1)
    with open('market_data.csv', newline="") as csv_file:
        # create a reader using csv import for iteration O(1)
        reader = csv.reader(csv_file)
        # move to the next line to avoid column headers (which should be ignored) O(1)
        header = next(reader)

        # for each non-header row O(n)
        for row in reader:
            # convert strings of timestamp, symbol, price O(1)a initialization and saving to memory
            timestamp, symbol, price = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"), row[1], float(row[2])
            # create new Market Data Point string, encoding it so that it can be passed
            mdp = f"{timestamp}*{symbol}*{price}".encode()
            # append data_points with the new MarketDataPoint instance O(1) time amortized
            data_points.append(mdp)
        return data_points

def main():
    
    # load the datapoints and get the length for iterations
    data_points = load_data()
    n = len(data_points)
    
    # MESSAGE DELIMITER 
    MESSAGE_DELIMITER = b'*'

    # ESTABLISH HOSTS AND PORT
    HOST = '127.0.0.1'
    PRICE_PORT = 9001
    SENT_PORT = 9002

    # create price server with proper port, reusable address (to avoid socket issue)
    price_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    price_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    price_server.bind(("localhost", PRICE_PORT))
    price_server.listen()
    price_server.setblocking(False)

    
    # create separate server with proper port, reusable address (to avoid socket issue)
    sent_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sent_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sent_server.bind(("localhost", SENT_PORT))
    sent_server.listen()
    sent_server.setblocking(False)

    # initialize server sockets to use via select, and price/sent client tracker
    server_sockets = [price_server, sent_server]
    price_clients = []
    sent_clients = []
    
    
    # i: 
    i = 0
    j = 0
    
    while i < n or j < n:
        print(f"server running... data index: {i}/{n}")
        # Only use select to accept new client connections
        readable, _, _ = select.select(server_sockets, [], [], 0.1)

        for sock in readable:
            # add any new price server client to the proper list to keep track
            if sock is price_server:
                conn, _ = price_server.accept()
                price_clients.append(conn)
                conn.setblocking(False)
                print("Price client connected")
            
            # add any new sent server client to the proper list to keep track
            elif sock is sent_server:
                conn, _ = sent_server.accept()
                conn.setblocking(False)
                sent_clients.append(conn)
                print("Sentiment client connected")

        # Proactively stream data to all connected clients if there is data left
        if i < n and price_clients:
            # Send price data to all price clients, handling exceptions where needed
            for client in price_clients:
                try:
                    encoded_data = data_points[i] + MESSAGE_DELIMITER
                    client.send(encoded_data)
                    print(f"Price data sent: {encoded_data}")
                except Exception as e:
                    print(f"Error sending to price client: {e}")
                    price_clients.remove(client)
                    client.close()
            # increment i consistently
            i += 1
            time.sleep(0.1)
        if j < n and sent_clients:
            # Send random sentiment to sentiment client
            for client in sent_clients:
                try:
                    
                    sentiment = f"{random.randint(0, 100)}"
                    client.send(sentiment.encode() + MESSAGE_DELIMITER)
                    print(f"Sentiment sent: {sentiment}")
                except Exception as e:
                    print(f"Error sending to sentiment client: {e}")
                    sent_clients.remove(client)
                    client.close()
            j += 1
            time.sleep(0.1)
        elif i >= n and j >= n:
            # Here, we close the connections once we've passed through all data
            print("All data sent, closing connections")
            for client in price_clients:
                client.close()
            for client in sent_clients:
                client.close()
            price_server.close()
            sent_server.close()
            break

if __name__ == "__main__":
    main()

