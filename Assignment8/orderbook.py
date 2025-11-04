"""TODO: Implement OrderBook process for Assignment 8."""
import socket, select
import asyncio
from datetime import datetime
from dataclasses import dataclass

@dataclass(frozen=True)
class MarketDataPoint:
    # create timestamp, symbol, and price instances with established types
    timestamp: datetime
    symbol: str
    price: float


def get_datapoint_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 9001))
    data_points = []
    while True:
        try:
            response = client.recv(1024)
            if not response:
                break
            # convert data points
            response = response.decode().split("*")[:-1]
            print('response occurring')
            print(response)
            mdp = MarketDataPoint(datetime.strptime(response[0], "%Y-%m-%d %H:%M:%S"), response[1], float(response[2]))
            data_points.append(mdp)
            print('data point added!')
        except:
            break
    print(data_points)
    return data_points

def get_sentiments():
    client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client2.connect(("localhost", 9002))
    sent_points = []
    
    while True:
        try:
            response2 = client2.recv(1024)
            if not response2:
                break
            
            # Decode and add to buffer
            value = response2.decode()[:-1]
            sentiment = int(value)
            sent_points.append(sentiment)
            print(f'Sentiment received: {sentiment}')
        except Exception as e:
            print(f"Error: {e}")
            break

    client2.close()
    return sent_points

def both():
    # create client 1 for price sockets
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 9001))
    data_points = []
    # create client 2 for sentiment sockets
    client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client2.connect(("localhost", 9002))
    sent_points = []
    while True:
        try:
            response = client.recv(1024)
            # convert data points
            response = response.decode().split("*")[:-1]
            print('response occurring')
            print(response)
            mdp = MarketDataPoint(datetime.strptime(response[0], "%Y-%m-%d %H:%M:%S"), response[1], float(response[2]))
            data_points.append(mdp)
            print('data point added!')
            response2 = client2.recv(1024)
            if not response and response2:
                break
            
            # Decode and add to buffer
            value = response2.decode()[:-1]
            sentiment = int(value)
            sent_points.append(sentiment)
            print(f'Sentiment received: {sentiment}')
        except:
            break
    return data_points, sent_points
    


def main():
    data_points, sentiments = both()
    print(data_points)
    print(sentiments)
    print(len(data_points))
    print(len(sentiments))


if __name__ == '__main__':
    main()