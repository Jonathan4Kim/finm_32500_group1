from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

import math
import numpy as np

from gateway import load_market_data
from order import Order
from order_manager import OrderManager
from risk_engine import RiskEngine
from strategy import (
    MAStrategy,
    MomentumStrategy,
    StatisticalSignalStrategy,
    SentimentStrategy,
    MarketDataPoint,
    Signal,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = BASE_DIR / "data" / "market_data.csv"


@dataclass
class StrategyConfig:
    """
    Helper container for parameter sweeps.
    Just a way to properly configure our strategies for late usage
    """
    name: str
    factory: Callable[..., Any]
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeRecord:
    """
    Will be used to keep track of what's happening
    for reporting/backtesting.
    """
    entry_time: datetime
    exit_time: datetime
    qty: int
    entry_price: float
    exit_price: float
    pnl: float


class Backtester:
    """
    Streams historical prices through a strategy, simulates order routing via the
    existing OrderManager/MatchingEngine stack, and records analytics.
    """

    def __init__(
        self,
        
        # initial strategy will be MAStrategy by default.
        strategy_factory: Callable[..., Any] = MAStrategy,
        strategy_params: Optional[Dict[str, Any]] = None,
        # we're using the market data we generated in part 1 by default
        market_data_path: str = str(DEFAULT_DATA_PATH),
        
        # random capital for backtesting, just did 100k
        initial_capital: float = 100_000.0,
        risk_limits: Optional[Dict[str, Any]] = None,
    ):
        # ensure that we have proper strategy params for at least moving average
        if strategy_params is None:
            strategy_params = {"symbol": "AAPL", "short_window": 5, "long_window": 20, "position_size": 10}
        
        # we need to guarantee a symbol for this backtesting to work
        if "symbol" not in strategy_params:
            raise ValueError("strategy_params must include a 'symbol'")

        # initialization of values
        self.strategy_factory = strategy_factory
        self.strategy_params = strategy_params
        self.market_data_path = market_data_path
        self.initial_capital = float(initial_capital)

        self.risk_engine = RiskEngine(**(risk_limits or {}))
        self.order_manager = OrderManager(self.risk_engine, simulated=True)
        self._risk_initial_cash = getattr(self.risk_engine, "cash_balance", 0.0)
        self.data_loader: Callable[[str], Iterable[MarketDataPoint]] = load_market_data

        self.trade_log: List[Dict[str, Any]] = []
        self.completed_trades: List[TradeRecord] = []
        self.equity_curve: List[Dict[str, Any]] = []
        
        
        # initial constraints, and last price
        self._cash = self.initial_capital
        self._position = 0
        self._avg_entry_price = 0.0
        self._realized_pnl = 0.0
        self._open_trade_start: Optional[datetime] = None
        self._last_price: Optional[float] = None

    def _reset_state(self):
        """
        Re-initializes values for another strategy,
        does what is done in __init__, but just in another
        case
        """
        self.trade_log.clear()
        self.completed_trades.clear()
        self.equity_curve.clear()
        self._cash = self.initial_capital
        self._position = 0
        self._avg_entry_price = 0.0
        self._realized_pnl = 0.0
        self._open_trade_start = None
        self._last_price = None
        self.risk_engine.positions = {}
        self.risk_engine.buy_totals = {}
        self.risk_engine.sell_totals = {}
        self.risk_engine.cash_balance = self._risk_initial_cash

    def _mark_to_market(self, timestamp: datetime, price: float):
        """
        
        Adds a timestamp and current equity to a list
        of dictionaries, self.equity_curve

        Args:
            timestamp (datetime): _description_
            price (float): _description_
        """
        # set new last price accordingly
        self._last_price = price
        
        # get cash and right equity to append to equity curve list
        equity = self._cash + self._position * price
        self.equity_curve.append({"timestamp": timestamp, "equity": equity})

    def _record_trade_event(
        self,
        timestamp: datetime,
        signal: Signal,
        status: str,
        filled_qty: int,
        filled_price: Optional[float],
        order_payload: Optional[Dict[str, Any]],
    ):
        # add new trade log to trade log list for reporting
        self.trade_log.append(
            {
                "timestamp": timestamp,
                "signal": signal.signal.value,
                "symbol": signal.symbol,
                "status": status,
                "qty": filled_qty,
                "price": filled_price,
                "reason": signal.reason,
                "order_id": (order_payload or {}).get("id"),
            }
        )

    def _handle_fill(self, timestamp: datetime, side: str, qty: int, price: float):
        """
        Handles a fill order and according side

        Args:
            timestamp (datetime): timestamp for trade log
            side (str): BUY or SELL signal
            qty (int): trade quantity to be used
            price (float): price of trade
        """
        
        # ensure quantity is positive, nonzero
        if qty <= 0:
            return
        
        # BUY case
        if side == "BUY":
            # new open trade happens when our position reaches 0 
            if self._position == 0:
                self._open_trade_start = timestamp
            total_qty = self._position + qty
            if total_qty > 0:
                weighted_cost = self._avg_entry_price * self._position + price * qty
                self._avg_entry_price = weighted_cost / total_qty
            self._position = total_qty
            self._cash -= qty * price
        else:
            close_qty = min(qty, self._position)
            if close_qty == 0:
                return
            self._cash += close_qty * price
            pnl = (price - self._avg_entry_price) * close_qty
            self._realized_pnl += pnl
            self._position -= close_qty
            trade = TradeRecord(
                entry_time=self._open_trade_start or timestamp,
                exit_time=timestamp,
                qty=close_qty,
                entry_price=self._avg_entry_price,
                exit_price=price,
                pnl=pnl,
            )
            self.completed_trades.append(trade)
            if self._position == 0:
                self._avg_entry_price = 0.0
                self._open_trade_start = None

    def run(
        self,
        strategy_factory: Optional[Callable[..., Any]] = None,
        strategy_params: Optional[Dict[str, Any]] = None,
        data_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a full backtest for the provided strategy factory/params.
        Returns the computed performance metrics for convenience.
        """
        self._reset_state()

        params = dict(self.strategy_params)
        if strategy_params:
            params.update(strategy_params)
        factory = strategy_factory or self.strategy_factory

        strategy = factory(**params)
        symbol_filter = params.get("symbol")
        if not symbol_filter:
            raise ValueError("strategy params must define a target symbol")

        data_source = data_path or self.market_data_path
        for mdp in self.data_loader(data_source):
            if mdp.symbol != symbol_filter:
                continue
            self._mark_to_market(mdp.timestamp, mdp.price)
            signal = strategy.on_new_bar(mdp)
            if not signal:
                continue

            qty = strategy.get_position_size() if hasattr(strategy, "get_position_size") else params.get("position_size", 1)
            order = Order(
                side=signal.signal.value,
                symbol=signal.symbol,
                qty=qty,
                price=signal.price,
            )
            result = self.order_manager.process_order(order)
            status = result.get("status") or result.get("msg", "FAILED")
            filled_qty = result.get("filled_qty", 0)
            filled_price = result.get("filled_price")
            self._record_trade_event(signal.timestamp, signal, status, filled_qty, filled_price, result.get("order"))

            if not result.get("ok"):
                continue
            if status == "CANCELLED":
                continue
            if status in ("FILLED", "PARTIAL"):
                price = filled_price if filled_price is not None else signal.price
                self._handle_fill(signal.timestamp, signal.signal.value, filled_qty, price)

        return self.compute_performance_metrics()


    """
    Reporting/Metrics functions
    We have Reporting and Metric functions Below!
    """
    def compute_performance_metrics(self) -> Dict[str, Any]:
        if not self.equity_curve:
            return {}
        equity_values = np.array([row["equity"] for row in self.equity_curve], dtype=float)
        timestamps = [row["timestamp"] for row in self.equity_curve]

        returns = np.diff(equity_values) / np.where(equity_values[:-1] == 0, 1.0, equity_values[:-1])
        avg_return = returns.mean() if returns.size else 0.0
        return_vol = returns.std(ddof=1) if returns.size > 1 else 0.0
        sharpe = (avg_return / return_vol) * math.sqrt(252) if return_vol > 0 else 0.0

        running_max = np.maximum.accumulate(equity_values)
        drawdowns = (equity_values - running_max) / np.where(running_max == 0, 1.0, running_max)
        max_drawdown = drawdowns.min() if drawdowns.size else 0.0

        wins = [t.pnl for t in self.completed_trades if t.pnl > 0]
        losses = [t.pnl for t in self.completed_trades if t.pnl < 0]
        win_rate = len(wins) / len(self.completed_trades) if self.completed_trades else 0.0
        profit_factor = (sum(wins) / abs(sum(losses))) if losses else (float("inf") if wins else 0.0)
        win_loss_ratio = (len(wins) / len(losses)) if losses else (float("inf") if wins else 0.0)

        final_equity = float(equity_values[-1])
        total_return = (final_equity - self.initial_capital) / self.initial_capital

        return {
            "start": timestamps[0],
            "end": timestamps[-1],
            "final_equity": final_equity,
            "total_pnl": final_equity - self.initial_capital,
            "total_return": total_return,
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown * -100.0,
            "win_rate": win_rate,
            "win_loss_ratio": win_loss_ratio,
            "profit_factor": profit_factor,
            "num_trades": len(self.completed_trades),
            "realized_pnl": self._realized_pnl,
        }

    def plot_equity_curve(self, output_path: str = "reports/equity_curve.png") -> Path:
        if not self.equity_curve:
            raise ValueError("No equity data to plot")
        try:
            import matplotlib.pyplot as plt
        except ModuleNotFoundError as exc:
            raise RuntimeError("matplotlib is required for plotting") from exc

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        times = [row["timestamp"] for row in self.equity_curve]
        equity = [row["equity"] for row in self.equity_curve]

        plt.figure(figsize=(10, 4))
        plt.plot(times, equity, label="Equity")
        plt.title("Equity Curve")
        plt.xlabel("Time")
        plt.ylabel("Equity ($)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return Path(output_path)

    def plot_trade_distribution(self, output_path: str = "reports/trade_distribution.png") -> Path:
        if not self.completed_trades:
            raise ValueError("No trades to visualize")
        try:
            import matplotlib.pyplot as plt
        except ModuleNotFoundError as exc:
            raise RuntimeError("matplotlib is required for plotting") from exc

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        pnls = [trade.pnl for trade in self.completed_trades]

        plt.figure(figsize=(8, 4))
        plt.hist(pnls, bins=20, edgecolor="black")
        plt.title("Trade P&L Distribution")
        plt.xlabel("P&L per Trade")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return Path(output_path)

    def run_parameter_sweep(self, configs: Sequence[StrategyConfig]) -> List[Dict[str, Any]]:
        """
        Execute a series of parameter sets and return their metrics sorted by P&L.
        """
        results: List[Dict[str, Any]] = []
        for cfg in configs:
            summary = self.run(strategy_factory=cfg.factory, strategy_params=cfg.params)
            results.append(
                {
                    "name": cfg.name,
                    "params": cfg.params,
                    "metrics": summary,
                }
            )
        results.sort(key=lambda item: item["metrics"].get("total_pnl", 0.0), reverse=True)
        return results

    # Convenience presets ------------------------------------------------ #
    @staticmethod
    def default_strategy_configs(symbol: str) -> List[StrategyConfig]:
        """
        Build a representative list of strategy presets for the provided symbol.

        Args:
            symbol (str): Symbol shared by all default strategy instances.

        Returns:
            List[StrategyConfig]: Strategy definitions ready to be fed into the runner.
        """
        return [
            StrategyConfig(
                name="MA Fast",
                factory=MAStrategy,
                params={"symbol": symbol, "short_window": 5, "long_window": 20, "position_size": 10},
            ),
            StrategyConfig(
                name="Momentum",
                factory=MomentumStrategy,
                params={"symbol": symbol, "momentum_window": 12, "momentum_threshold": 0.0015, "position_size": 10},
            ),
            StrategyConfig(
                name="ZScore",
                factory=StatisticalSignalStrategy,
                params={"symbol": symbol, "lookback_window": 30, "zscore_threshold": 1.0, "position_size": 10},
            ),
            StrategyConfig(
                name="Sentiment",
                factory=SentimentStrategy,
                params={
                    "symbol": symbol,
                    "positive_threshold": 0.35,
                    "negative_threshold": -0.25,
                    "cooldown_bars": 4,
                    "position_size": 10,
                },
            ),
        ]


def _sanitize_label(name: str) -> str:
    """
    Convert a strategy label into a filesystem-friendly identifier.

    Args:
        name (str): Original label (can include spaces or punctuation).

    Returns:
        str: Lowercase token safe for filenames.
    """
    sanitized = "".join(ch.lower() if ch.isalnum() else "_" for ch in name)
    sanitized = "_".join(filter(None, sanitized.split("_")))
    return sanitized or "strategy"


def _strategy_factory_from_name(name: str) -> Callable[..., Any]:
    """
    Map a CLI-friendly strategy name to its concrete class.

    Args:
        name (str): Identifier supplied by the user (case-insensitive).

    Raises:
        ValueError: If the name does not correspond to a known strategy.

    Returns:
        Callable[..., Any]: Strategy constructor.
    """
    normalized = name.lower()
    mapping = {
        "ma": MAStrategy,
        "mastrategy": MAStrategy,
        "momentum": MomentumStrategy,
        "momentumstrategy": MomentumStrategy,
        "zscore": StatisticalSignalStrategy,
        "statistical": StatisticalSignalStrategy,
        "statisticalsignalstrategy": StatisticalSignalStrategy,
        "sentiment": SentimentStrategy,
        "sentimentstrategy": SentimentStrategy,
    }
    if normalized not in mapping:
        raise ValueError(f"Unknown strategy '{name}'")
    return mapping[normalized]


def _strategy_params_from_args(strategy_name: str, args: argparse.Namespace) -> Dict[str, Any]:
    """
    Build strategy parameter dictionaries from parsed CLI arguments.

    Args:
        strategy_name (str): Name specified via --strategy.
        args (argparse.Namespace): Parsed CLI arguments.

    Returns:
        Dict[str, Any]: Parameters ready to initialize the strategy.
    """
    base = {"symbol": args.symbol, "position_size": args.position_size}
    key = strategy_name.lower()
    if key in ("ma", "mastrategy"):
        base.update({"short_window": args.short_window, "long_window": args.long_window})
    elif key in ("momentum", "momentumstrategy"):
        base.update({"momentum_window": args.momentum_window, "momentum_threshold": args.momentum_threshold})
    elif key in ("zscore", "statistical", "statisticalsignalstrategy"):
        base.update({"lookback_window": args.lookback_window, "zscore_threshold": args.zscore_threshold})
    elif key in ("sentiment", "sentimentstrategy"):
        base.update(
            {
                "positive_threshold": args.sentiment_positive,
                "negative_threshold": args.sentiment_negative,
                "cooldown_bars": args.sentiment_cooldown,
            }
        )
    else:
        raise ValueError(f"Unsupported strategy '{strategy_name}'")
    return base


def _write_json(path: Path, payload: Any) -> Path:
    """
    Persist arbitrary payloads to JSON for reporting/inspection.

    Args:
        path (Path): Output location.
        payload (Any): Serializable object, metrics dict, etc.

    Returns:
        Path: The written file path for convenience.
    """
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    return path


def _write_trade_log(path: Path, trade_log: List[Dict[str, Any]]) -> Path:
    """
    Persist the trade log to CSV for further analytics.

    Args:
        path (Path): Output CSV path.
        trade_log (List[Dict[str, Any]]): Chronological trade ledger.

    Returns:
        Path: Where the log was stored.
    """
    fieldnames = ["timestamp", "signal", "symbol", "status", "qty", "price", "reason", "order_id"]
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in trade_log:
            writer.writerow(row)
    return path


def _write_completed_trades(path: Path, trades: List[TradeRecord]) -> Path:
    """
    Save completed trade summaries as CSV for easier downstream reporting.

    Args:
        path (Path): Output CSV destination.
        trades (List[TradeRecord]): Collection of completed trades.

    Returns:
        Path: Destination path.
    """
    fieldnames = ["entry_time", "exit_time", "qty", "entry_price", "exit_price", "pnl"]
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for trade in trades:
            writer.writerow(asdict(trade))
    return path


def _run_and_save(
    bt: Backtester,
    factory: Callable[..., Any],
    strategy_params: Dict[str, Any],
    data_path: str,
    label: str,
    output_dir: Path,
    skip_plots: bool,
) -> Dict[str, Any]:
    """
    Execute a single backtest run and persist its artifacts.

    Args:
        bt (Backtester): Backtester instance to reuse.
        factory (Callable[..., Any]): Strategy constructor.
        strategy_params (Dict[str, Any]): Strategy parameters.
        data_path (str): Historical data source.
        label (str): Identifier for filenames.
        output_dir (Path): Directory for reports.
        skip_plots (bool): Whether to bypass plot generation.

    Returns:
        Dict[str, Any]: Summary metrics and artifact paths.
    """
    safe_label = _sanitize_label(label)
    metrics = bt.run(strategy_factory=factory, strategy_params=strategy_params, data_path=data_path)

    trade_log = list(bt.trade_log)
    completed_trades = list(bt.completed_trades)

    metrics_path = output_dir / f"{safe_label}_metrics.json"
    trades_path = output_dir / f"{safe_label}_trade_log.csv"
    completed_path = output_dir / f"{safe_label}_completed_trades.csv"
    _write_json(metrics_path, metrics)
    _write_trade_log(trades_path, trade_log)
    _write_completed_trades(completed_path, completed_trades)

    equity_path = output_dir / f"{safe_label}_equity.png"
    dist_path = output_dir / f"{safe_label}_trade_distribution.png"
    if not skip_plots:
        try:
            bt.plot_equity_curve(str(equity_path))
        except RuntimeError as exc:
            print(f"[WARN] Equity plot skipped for {label}: {exc}")
        if completed_trades:
            try:
                bt.plot_trade_distribution(str(dist_path))
            except RuntimeError as exc:
                print(f"[WARN] Trade distribution plot skipped for {label}: {exc}")

    return {
        "label": safe_label,
        "metrics": metrics,
        "paths": {
            "metrics": metrics_path,
            "trade_log": trades_path,
            "completed_trades": completed_path,
            "equity_plot": equity_path if not skip_plots else None,
            "distribution_plot": dist_path if (completed_trades and not skip_plots) else None,
        },
    }


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """
    Parse CLI arguments for the backtester entrypoint.

    Args:
        argv (Optional[Sequence[str]]): Optional argument overrides.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Run backtests and generate performance artifacts.")
    parser.add_argument("--strategy", default="ma", help="Strategy name (ma, momentum, zscore, sentiment).")
    parser.add_argument("--symbol", default="AAPL", help="Symbol to backtest.")
    parser.add_argument("--data", default=str(DEFAULT_DATA_PATH), help="Path to historical data CSV.")
    parser.add_argument("--initial-capital", type=float, default=100_000.0, help="Starting capital.")
    parser.add_argument("--position-size", type=int, default=10, help="Default position size per trade.")
    parser.add_argument("--short-window", type=int, default=5, help="MA strategy short window.")
    parser.add_argument("--long-window", type=int, default=20, help="MA strategy long window.")
    parser.add_argument("--momentum-window", type=int, default=12, help="Momentum window length.")
    parser.add_argument("--momentum-threshold", type=float, default=0.0015, help="Momentum trigger threshold.")
    parser.add_argument("--lookback-window", type=int, default=30, help="Z-score strategy lookback.")
    parser.add_argument("--zscore-threshold", type=float, default=1.0, help="Z-score entry threshold.")
    parser.add_argument("--sentiment-positive", type=float, default=0.3, help="Sentiment buy threshold.")
    parser.add_argument("--sentiment-negative", type=float, default=-0.3, help="Sentiment sell threshold.")
    parser.add_argument("--sentiment-cooldown", type=int, default=3, help="Bars to wait between sentiment trades.")
    parser.add_argument("--max-order-size", type=int, default=1000, help="Risk control: max order size.")
    parser.add_argument("--max-position", type=int, default=2000, help="Risk control: max net position.")
    parser.add_argument("--cash", type=float, default=10000.0, help="Risk control: initial cash balance.")
    parser.add_argument("--max-total-buy", type=float, default=None, help="Risk control: max cumulative buy qty.")
    parser.add_argument("--max-total-sell", type=float, default=None, help="Risk control: max cumulative sell qty.")
    parser.add_argument("--output-dir", default="reports", help="Directory to store metrics and plots.")
    parser.add_argument("--skip-plots", action="store_true", help="Disable plot generation.")
    parser.add_argument("--sweep", action="store_true", help="Run preset parameter sweep after main run.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    """
    CLI entrypoint: runs each configured strategy, 
    saves outputs, and optionally performs sweeps.

    Args:
        argv (Optional[Sequence[str]]): Optional argument overrides when scripting/tests call main.
    """
    args = _parse_args(argv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    factory = _strategy_factory_from_name(args.strategy)
    strategy_params = _strategy_params_from_args(args.strategy, args)
    base_strategy_params = {"symbol": args.symbol, "position_size": args.position_size}
    risk_limits = {
        "max_order_size": args.max_order_size,
        "max_position": args.max_position,
        "cash_balance": args.cash,
        "max_total_buy": args.max_total_buy,
        "max_total_sell": args.max_total_sell,
    }

    bt = Backtester(
        strategy_factory=factory,
        strategy_params=base_strategy_params,
        market_data_path=args.data,
        initial_capital=args.initial_capital,
        risk_limits=risk_limits,
    )

    configs = Backtester.default_strategy_configs(args.symbol)
    matched = False
    for idx, cfg in enumerate(configs):
        if cfg.factory is factory:
            configs[idx] = StrategyConfig(name=cfg.name, factory=factory, params=strategy_params)
            matched = True
            break
    if not matched:
        configs.append(StrategyConfig(name=args.strategy, factory=factory, params=strategy_params))

    run_artifacts: List[Dict[str, Any]] = []
    for cfg in configs:
        result = _run_and_save(
            bt=bt,
            factory=cfg.factory,
            strategy_params=cfg.params,
            data_path=args.data,
            label=cfg.name,
            output_dir=output_dir,
            skip_plots=args.skip_plots,
        )
        run_artifacts.append(result)

    sweep_results: List[Dict[str, Any]] = []
    if args.sweep:
        configs = Backtester.default_strategy_configs(args.symbol)
        for cfg in configs:
            sweep_result = _run_and_save(
                bt=bt,
                factory=cfg.factory,
                strategy_params=cfg.params,
                data_path=args.data,
                label=cfg.name,
                output_dir=output_dir,
                skip_plots=args.skip_plots,
            )
            sweep_results.append({"name": cfg.name, "params": cfg.params, "metrics": sweep_result["metrics"]})
        _write_json(output_dir / "parameter_sweep.json", sweep_results)

    for artifact in run_artifacts:
        metrics_path = artifact["paths"]["metrics"]
        print(f"Backtest complete for {artifact['label']}. Metrics saved to {metrics_path}")


if __name__ == "__main__":
    main()
