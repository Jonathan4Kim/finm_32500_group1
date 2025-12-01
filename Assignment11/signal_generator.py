from __future__ import annotations

import pandas as pd


def generate_signals(
    test_df: pd.DataFrame,
    predictions,
    probabilities=None,
    prob_threshold: float = 0.55,
) -> pd.DataFrame:
    """
    Convert model predictions into trading signals.

    Args:
        test_df: Holdout dataframe containing at least date/ticker/next_return.
        predictions: Array-like class predictions (0/1).
        probabilities: Optional probability of class 1.
        prob_threshold: Probability threshold to issue a long signal.
    """
    
    # obtain the predictions column from signals/test df
    signals = test_df[["date", "ticker", "close", "next_return"]].copy()
    signals["prediction"] = predictions
    
    # if we have probabilities, we generate proper signals using the probabilities we got!
    if probabilities is not None:
        signals["probability_long"] = probabilities
        signals["signal"] = (signals["probability_long"] >= prob_threshold).astype(int)
    else:
        signals["probability_long"] = None
        signals["signal"] = predictions

    # get the expected returns of what we would get, and sort the final signsl dataframe as sorted values
    signals["expected_return"] = signals["next_return"]
    signals.sort_values(["date", "ticker"], inplace=True)
    signals.reset_index(drop=True, inplace=True)
    
    # returnt eh signals dataframe
    return signals


__all__ = ["generate_signals"]
