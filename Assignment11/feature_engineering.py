from __future__ import annotations

import numpy as np
import pandas as pd


class FeatureEngineer:
    """
    A class that generates technical features, 
    labels, and metadata needed for modeling.
    """

    def __init__(self, features: list[str], label: str) -> None:
        self.features = features
        self.label = label

    @staticmethod
    def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        Computes the Relative Strength Index (RSI) for a price series.

        Process:
            1. Compute price differences.
            2. Separate positive (gain) and negative (loss) moves.
            3. Smooth gains/losses using exponential weighted averages.
            4. Compute the RS ratio = avg_gain / avg_loss.
            5. Convert RS into RSI:
                RSI = 100 - (100 / (1 + RS))

        Args:
            series (pd.Series): _description_
            period (int, optional): _description_. Defaults to 14.

        Returns:
            pd.Series: _description_
        """
        
        # calculate various factors for rsi computation
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        
        # conmpute rsi and return it!
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def _macd(series: pd.Series, fast: int = 12, slow: int = 26) -> pd.Series:
        """
        Computes moving averages for short/long windows

        Args:
            series (pd.Series): _description_
            fast (int, optional): _description_. Defaults to 12.
            slow (int, optional): _description_. Defaults to 26.

        Returns:
            pd.Series: _description_
        """
        # compute slow/fast ema
        fast_ema = series.ewm(span=fast, adjust=False).mean()
        slow_ema = series.ewm(span=slow, adjust=False).mean()

        # compare these averages by subtracting recent from longer window, and return as difference
        return fast_ema - slow_ema

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.sort_values(["ticker", "date"], inplace=True)

        grouped = df.groupby("ticker", group_keys=False)
        df["return_1d"] = grouped["close"].pct_change(periods=1)
        df["return_3d"] = grouped["close"].pct_change(periods=3)
        df["return_5d"] = grouped["close"].pct_change(periods=5)
        df["log_return"] = grouped["close"].apply(lambda x: np.log(x).diff())
        df["sma_5"] = grouped["close"].rolling(window=5).mean().reset_index(level=0, drop=True)
        df["sma_10"] = grouped["close"].rolling(window=10).mean().reset_index(level=0, drop=True)
        df["rsi_14"] = grouped["close"].apply(self._rsi).reset_index(level=0, drop=True)
        df["macd"] = grouped["close"].apply(self._macd).reset_index(level=0, drop=True)

        # Future return/label
        df["next_return"] = grouped["close"].apply(lambda x: x.shift(-1) / x - 1).reset_index(level=0, drop=True)
        df[self.label] = (df["next_return"] > 0).astype(int)

        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(subset=self.features + ["next_return", self.label], inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df


__all__ = ["FeatureEngineer"]
