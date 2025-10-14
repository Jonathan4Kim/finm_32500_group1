import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, prices: pd.Series) -> pd.Series:
        pass

class VolatilityBreakoutStrategy(Strategy):
    def __init__(self, window=20):
        self.name = "volatility"
        self.window = window

    def generate_signals(self, prices: pd.Series) -> pd.Series:
        """
        Generates signals using a volatility breakout strategy,
        where
        
        
        prices: pd.Series of prices indexed by date (or sequential index)

        Returns:
            pd.Series of signals ("BUY", "SELL", "HOLD")
        """

        # Daily returns by percentage change
        returns = prices.pct_change()

        # Rolling volatility (population std, like your tick version) by getting percent changes' standard deviation
        rolling_vol = returns.rolling(self.window).std(ddof=0)

        # Conditions for buy signal and sell signal, dependent on the returns themselve and the rolling vol we cal in prev line
        buy_signal = returns > rolling_vol
        sell_signal = returns < -rolling_vol

        # Default to HOLD when necessary, creating a new dataframe
        signals = pd.Series("HOLD", index=prices.index)

        # Assign BUY/SELL by using booleans on the signals series
        signals[buy_signal] = "BUY"
        signals[sell_signal] = "SELL"

        # The first `window` periods have insufficient history
        signals[:self.window] = "HOLD"

        return signals