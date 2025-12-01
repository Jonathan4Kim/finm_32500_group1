## https://github.com/alpacahq/alpaca-py/tree/master 

import os
import re
from alpaca.trading.client import TradingClient

def read_key(path):
    with open(path, "r") as f:
        return f.read().strip()
    
class Secret(str):
    """Simple str override for hiding actual values."""
    def __str__(self) -> str:
        """Replace actual string with * when printing to the screen."""
        return re.sub(r"\S", "*", self)

def load_keys():
    api_key = read_key(".alpaca_api_key")
    api_secret = read_key(".alpaca_api_secret")

    print(f"Your key was read: {Secret(api_key)}")
    print(f"Your secret was read: {Secret(api_secret)}")

    return api_key, api_secret

if __name__ == "__main__":

    api_key, api_secret = load_keys()

    try:
        trading_client = TradingClient(api_key, api_secret, paper=True)
        print("Trading client created...")

        acct = trading_client.get_account()
        if acct:
            print("Trading client connected...")
            print(f"{acct.status}")
    except Exception as e:
        print("Error connecting to Alpaca:", e)
