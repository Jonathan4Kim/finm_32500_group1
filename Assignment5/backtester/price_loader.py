import numpy as np
import pandas as pd

def generate_price_series(start_price=100.0, n=50, trend="flat", noise_level=0.01, seed=42) -> pd.Series:
    """
    Generate synthetic price series for testing.
    
    Args:
        start_price (float): initial price
        n (int): number of data points
        trend (str): "flat", "up", "down", "volatile"
        noise_level (float): standard deviation of random noise
        seed (int): random seed for reproducibility

    Returns:
        pd.Series of synthetic prices
    """
    
    # first, just create that generator and begin at a price of your choosing
    np.random.seed(seed)
    prices = [start_price]

    # depending on trend, change the drift so the prices tend towards that level
    for i in range(1, n):
        if trend == "flat":
            drift = 0.0
        elif trend == "up":
            drift = 0.002
        elif trend == "down":
            drift = -0.002 
        elif trend == "volatile":
            drift = 0.0
            noise_level = 0.05
        else:
            raise ValueError("trend must be one of: flat, up, down, volatile")

        # draw random sample based on the noise level and drift; usually not too volatile
        shock = np.random.normal(drift, noise_level)
        # Then, append drifted price to prices by multiplying the previous price by the shock
        prices.append(prices[-1] * (1 + shock))

    return pd.Series(prices, name="price")