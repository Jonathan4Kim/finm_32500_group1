import os, json, time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd, numpy as np
from data_loader import load_data_pandas

@dataclass
class PositionMetrics:
    symbol: str
    quantity: int
    latest_price: float
    value: float
    volatility: float
    drawdown: float


def compute_position_metrics(arg):
    """Compute value, 20-period rolling volatility of returns, and max drawdown."""
    pos, df = arg
    sym, qty = pos["symbol"], pos["quantity"]
    d = df[df["symbol"] == sym].sort_values("timestamp")

    if d.empty:
        p = float(pos.get("price", 0.0))
        return PositionMetrics(sym, qty, p, qty * p, 0.0, 0.0)

    prices = d["price"].astype(float).reset_index(drop=True)
    latest = float(prices.iloc[-1])
    value = qty * latest

    # rolling volatility: 20-period rolling std of returns (min_periods=1), take last
    returns = prices.pct_change()
    rolling_std = returns.rolling(window=20, min_periods=1).std()
    vol = float(rolling_std.iloc[-1]) if not rolling_std.empty else 0.0

    # max drawdown (peak-to-trough)
    cummax = prices.cummax()
    drawdowns = (prices - cummax) / cummax
    max_dd = float(drawdowns.min()) if not drawdowns.empty else 0.0

    return PositionMetrics(sym, qty, latest, value, vol, max_dd)

def compute_positions(positions: List[Dict], df: pd.DataFrame, parallel=True, workers=4):
    data = [(p, df) for p in positions]
    if parallel and data:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(compute_position_metrics, data))
    return [compute_position_metrics(x) for x in data]

def aggregate_metrics(pos_metrics: List[PositionMetrics], sub_aggregates: List[Dict] = None):
    sub_aggregates = sub_aggregates or []
    total_value = sum(p.value for p in pos_metrics) + sum(s["total_value"] for s in sub_aggregates)
    # weighted volatility
    weighted = sum(p.value * p.volatility for p in pos_metrics) + sum(s["total_value"] * s["aggregate_volatility"] for s in sub_aggregates)
    agg_vol = weighted / total_value if total_value else 0.0
    # worst drawdown
    all_dd = [p.drawdown for p in pos_metrics] + [s["max_drawdown"] for s in sub_aggregates]
    max_dd = min(all_dd) if all_dd else 0.0
    return {"total_value": total_value, "aggregate_volatility": agg_vol, "max_drawdown": max_dd}

def process_portfolio(portfolio: Dict, df: pd.DataFrame, parallel=True, workers=4):
    positions = portfolio.get("positions", [])
    subs = portfolio.get("sub_portfolios", [])

    pos_metrics = compute_positions(positions, df, parallel, workers) if positions else []
    sub_results = [process_portfolio(sp, df, parallel, workers) for sp in subs]

    agg = aggregate_metrics(pos_metrics, sub_results)
    # explicit rounding/formatting
    return {
        "name": portfolio.get("name", "Portfolio"),
        "positions": [
            {
                "symbol": p.symbol,
                "quantity": p.quantity,
                "latest_price": round(p.latest_price, 2),
                "value": round(p.value, 2),
                "volatility": round(p.volatility, 4),
                "drawdown": round(p.drawdown, 4),
            }
            for p in pos_metrics
        ],
        "sub_portfolios": sub_results,
        "total_value": round(agg["total_value"], 2),
        "aggregate_volatility": round(agg["aggregate_volatility"], 4),
        "max_drawdown": round(agg["max_drawdown"], 4),
    }

def compare_modes(portfolio: Dict, df: pd.DataFrame, workers=4):
    t0 = time.perf_counter()
    seq = process_portfolio(portfolio, df, parallel=False, workers=workers)
    t1 = time.perf_counter()
    par = process_portfolio(portfolio, df, parallel=True, workers=workers)
    t2 = time.perf_counter()
    seq_time, par_time = t1 - t0, t2 - t1
    speedup = seq_time / par_time if par_time > 0 else 1.0
    return {"sequential_time": seq_time, "parallel_time": par_time, "speedup": speedup, "result": par}

if __name__ == "__main__":
    df = load_data_pandas()
    pf_path = os.path.join(os.path.dirname(__file__), "portfolio_structure-1.json")
    if not os.path.exists(pf_path):
        raise SystemExit(f"Missing portfolio file: {pf_path}")

    with open(pf_path) as f:
        portfolio = json.load(f)

    workers = min(4, max(1, (df["symbol"].nunique() if "symbol" in df.columns else 1)))
    comp = compare_modes(portfolio, df, workers=workers)

    print(f"\nSequential: {comp['sequential_time']:.4f}s | Parallel: {comp['parallel_time']:.4f}s | Speedup: {comp['speedup']:.2f}x\n")
    res = comp["result"]
    print(f"{res['name']}: Value=${res['total_value']:,.2f}, Vol={res['aggregate_volatility']:.4f}, MaxDD={res['max_drawdown']:.2%}\n")

    for p in res["positions"]:
        print(f"  {p['symbol']} x{p['quantity']}: ${p['value']:,.2f}, vol={p['volatility']:.4f}, dd={p['drawdown']:.2%}")

    for s in res["sub_portfolios"]:
        print(f"  Sub '{s['name']}': ${s['total_value']:,.2f}, vol={s['aggregate_volatility']:.4f}, dd={s['max_drawdown']:.2%}")

    with open("portfolio_results.json", "w") as f:
        json.dump(res, f, indent=2)

    print("\nSaved portfolio_results.json")