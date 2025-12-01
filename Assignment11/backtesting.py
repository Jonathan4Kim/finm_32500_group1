from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    """
    Just a dataclass that will store the necessary
    metrics, which for each run we will save into reports.
    """
    signals: pd.DataFrame
    equity_curve: pd.DataFrame
    metrics: Dict[str, float]


class Backtester:
    """
    A class that runs a simple long-only backtest on generated signals.
    """

    def __init__(self, initial_capital: float = 100_000.0, position_size: float = 10_000.0) -> None:
        # initialize with starting capital and position size
        self.initial_capital = initial_capital
        self.position_size = position_size

    @staticmethod
    def _max_drawdown(equity: pd.Series) -> float:
        """
        
        Computes maximum drawdown of a pandas series,
        return the minimum value as a float

        Args:
            equity (pd.Series): equity pandas series

        Returns:
            float: maximum drawdown
        """
        
        # get the cumulative maximum
        cumulative_max = equity.cummax()
        
        # get maximum drawdown of whole series
        drawdown = (equity - cumulative_max) / cumulative_max
        return float(drawdown.min())

    def run(self, signals_df: pd.DataFrame) -> BacktestResult:
        """
        
        Backtester Results

        Args:
            signals_df (pd.DataFrame): dataframe of signals from results

        Returns:
            BacktestResult: A Backtest REsult we'll be saving in reports
        """
        
        # calculate pnls
        df = signals_df.copy()
        df["trade_pnl"] = df["signal"] * df["next_return"] * self.position_size
        df["buy_hold_pnl"] = df["next_return"] * self.position_size

        # get daily pnl
        daily = (
            df.groupby("date")[["trade_pnl", "buy_hold_pnl"]]
            .sum()
            .sort_index()
            .reset_index()
        )

        # compute relevant equity metrics for equity curve
        strategy_equity = []
        buy_hold_equity = []
        strat_capital = self.initial_capital
        buy_hold_capital = self.initial_capital

        for _, row in daily.iterrows():
            strat_capital += row["trade_pnl"]
            buy_hold_capital += row["buy_hold_pnl"]
            strategy_equity.append(strat_capital)
            buy_hold_equity.append(buy_hold_capital)

        # save equity curve in dataframe
        equity_curve = pd.DataFrame(
            {
                "date": daily["date"],
                "strategy_equity": strategy_equity,
                "buy_hold_equity": buy_hold_equity,
            }
        )

        # calculate total return, max drawdown, and returns from holding from buying
        total_return = (strategy_equity[-1] / self.initial_capital) - 1 if strategy_equity else 0.0
        buy_hold_return = (buy_hold_equity[-1] / self.initial_capital) - 1 if buy_hold_equity else 0.0
        max_dd = self._max_drawdown(equity_curve["strategy_equity"]) if not equity_curve.empty else 0.0

        # get executed trades and win trate for metrics dataframe.
        executed_trades = df[df["signal"] == 1]
        wins = (executed_trades["next_return"] > 0).sum()
        losses = (executed_trades["next_return"] <= 0).sum()
        win_rate = wins / len(executed_trades) if len(executed_trades) else 0.0

        # create Backtesting Metrics dataframe from what was computed above
        metrics = {
            "total_return": float(total_return),
            "buy_hold_return": float(buy_hold_return),
            "max_drawdown": float(max_dd),
            "win_rate": float(win_rate),
            "trades": int(len(executed_trades)),
            "avg_trade_pnl": float(executed_trades["trade_pnl"].mean()) if len(executed_trades) else 0.0,
        }

        return BacktestResult(signals=df, equity_curve=equity_curve, metrics=metrics)


def save_backtest_outputs(result: BacktestResult, output_dir: Path) -> None:
    """
    
    Saves Backtesting Outputs to directory.

    Args:
        result (BacktestResult): Backtesting Results, contains signals, equity curve, and pandas series for metrics
        output_dir (Path): string of output directory to be created (if necessary) and saved to
    """
    # make the output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # convert results to csvs to be saved in the output directories.
    result.signals.to_csv(output_dir / "signals.csv", index=False)
    result.equity_curve.to_csv(output_dir / "equity_curve.csv", index=False)
    pd.Series(result.metrics).to_csv(output_dir / "metrics.csv")


__all__ = ["Backtester", "BacktestResult", "save_backtest_outputs"]
