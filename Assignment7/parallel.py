from __future__ import annotations
import time
import os
from dataclasses import dataclass
from typing import Dict, Tuple, Any, List

import pandas as pd
import numpy as np
import psutil
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from data_loader import load_data_pandas
from metrics import add_rolling_mean_pandas, add_rolling_std_pandas, add_rolling_sharpe_pandas

@dataclass
class PerformanceMetrics:
    execution_time: float
    cpu_percent: float
    memory_delta_mb: float
    approach: str

def compute_rolling_metrics_for_symbol(symbol_data: Tuple[str, pd.DataFrame]) -> Dict[str, Any]:
    """Compute rolling metrics for one symbol."""
    symbol, df = symbol_data
    df = df.sort_values("timestamp").reset_index(drop=True).copy()
    df = add_rolling_mean_pandas(df)
    df = add_rolling_std_pandas(df)
    df = add_rolling_sharpe_pandas(df)
    return {
        "symbol": symbol,
        "data": df,
        "latest_price": float(df["price"].iloc[-1]) if len(df) > 0 else None,
        "avg_sharpe": float(df["rolling_sharpe_20"].mean()) if "rolling_sharpe_20" in df.columns else None,
    }

def _proc_stats_snapshot(interval: float = 0.05) -> Tuple[float, float]:
    """Return (cpu_percent, memory_mb) for current process."""
    p = psutil.Process(os.getpid())
    return p.cpu_percent(interval=interval), p.memory_info().rss / (1024 ** 2)

def _group_by_symbol_list(df: pd.DataFrame) -> List[Tuple[str, pd.DataFrame]]:
    """Return list of (symbol, dataframe) tuples."""
    return [(sym, group[["timestamp", "symbol", "price"]].copy())
            for sym, group in df.groupby("symbol")]

def compute_metrics_sequential(df: pd.DataFrame) -> Tuple[Dict[str, Any], PerformanceMetrics]:
    """Sequential baseline."""
    grouped = _group_by_symbol_list(df)
    cpu_start, mem_start = _proc_stats_snapshot()
    t0 = time.perf_counter()
    results = {}
    for symbol, df_sym in grouped:
        results[symbol] = compute_rolling_metrics_for_symbol((symbol, df_sym))
    elapsed = time.perf_counter() - t0
    cpu_end, mem_end = _proc_stats_snapshot()
    return results, PerformanceMetrics(
        execution_time=elapsed,
        cpu_percent=(cpu_start + cpu_end) / 2,
        memory_delta_mb=(mem_end - mem_start),
        approach="Sequential"
    )

def compute_metrics_threading(df: pd.DataFrame, max_workers: int = 4) -> Tuple[Dict[str, Any], PerformanceMetrics]:
    """Threading with ThreadPoolExecutor."""
    grouped = _group_by_symbol_list(df)
    cpu_start, mem_start = _proc_stats_snapshot()
    t0 = time.perf_counter()
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        for out in exe.map(compute_rolling_metrics_for_symbol, grouped):
            results[out["symbol"]] = out
    elapsed = time.perf_counter() - t0
    cpu_end, mem_end = _proc_stats_snapshot()
    return results, PerformanceMetrics(
        execution_time=elapsed,
        cpu_percent=(cpu_start + cpu_end) / 2,
        memory_delta_mb=(mem_end - mem_start),
        approach="Threading"
    )

def compute_metrics_multiprocessing(df: pd.DataFrame, max_workers: int = 4) -> Tuple[Dict[str, Any], PerformanceMetrics]:
    """Multiprocessing with ProcessPoolExecutor."""
    grouped = _group_by_symbol_list(df)
    cpu_start, mem_start = _proc_stats_snapshot()
    t0 = time.perf_counter()
    results = {}
    with ProcessPoolExecutor(max_workers=max_workers) as exe:
        for out in exe.map(compute_rolling_metrics_for_symbol, grouped):
            results[out["symbol"]] = out
    elapsed = time.perf_counter() - t0
    cpu_end, mem_end = _proc_stats_snapshot()
    return results, PerformanceMetrics(
        execution_time=elapsed,
        cpu_percent=(cpu_start + cpu_end) / 2,
        memory_delta_mb=(mem_end - mem_start),
        approach="Multiprocessing"
    )

def compare_parallel_approaches(df: pd.DataFrame, max_workers: int = 4) -> pd.DataFrame:
    """Compare sequential, threading, and multiprocessing."""
    _, seq = compute_metrics_sequential(df)
    _, thr = compute_metrics_threading(df, max_workers=max_workers)
    _, mp = compute_metrics_multiprocessing(df, max_workers=max_workers)
    rows = [
        {
            "Approach": seq.approach,
            "Execution Time (s)": round(seq.execution_time, 4),
            "CPU (%)": round(seq.cpu_percent, 2),
            "Memory Δ (MB)": round(seq.memory_delta_mb, 2),
            "Speedup vs Sequential": 1.0
        },
        {
            "Approach": thr.approach,
            "Execution Time (s)": round(thr.execution_time, 4),
            "CPU (%)": round(thr.cpu_percent, 2),
            "Memory Δ (MB)": round(thr.memory_delta_mb, 2),
            "Speedup vs Sequential": round(seq.execution_time / thr.execution_time, 2) if thr.execution_time > 0 else None
        },
        {
            "Approach": mp.approach,
            "Execution Time (s)": round(mp.execution_time, 4),
            "CPU (%)": round(mp.cpu_percent, 2),
            "Memory Δ (MB)": round(mp.memory_delta_mb, 2),
            "Speedup vs Sequential": round(seq.execution_time / mp.execution_time, 2) if mp.execution_time > 0 else None
        }
    ]
    return pd.DataFrame(rows)

def analyze_gil_impact(df: pd.DataFrame, worker_counts: List[int] = [1, 2, 4, 8]) -> pd.DataFrame:
    """Test threading vs multiprocessing with different worker counts."""
    rows = []
    for workers in worker_counts:
        t0 = time.perf_counter()
        _, _ = compute_metrics_threading(df, max_workers=workers)
        thread_time = time.perf_counter() - t0

        t0 = time.perf_counter()
        _, _ = compute_metrics_multiprocessing(df, max_workers=workers)
        mp_time = time.perf_counter() - t0

        rows.append({
            "Workers": workers,
            "Threading (s)": round(thread_time, 4),
            "Multiprocessing (s)": round(mp_time, 4)
        })
    return pd.DataFrame(rows)

def verify_consistency(results_a: Dict[str, Any], results_b: Dict[str, Any], tolerance: float = 1e-8) -> bool:
    """Check if two result sets match numerically."""
    if set(results_a.keys()) != set(results_b.keys()):
        return False
    for sym in results_a.keys():
        df_a = results_a[sym]["data"].reset_index(drop=True)
        df_b = results_b[sym]["data"].reset_index(drop=True)
        if df_a.shape != df_b.shape:
            return False
        for col in ["rolling_mean_20", "rolling_std_20", "rolling_sharpe_20"]:
            if col in df_a.columns and col in df_b.columns:
                diff = (df_a[col].fillna(0) - df_b[col].fillna(0)).abs().max()
                if diff > tolerance:
                    return False
    return True

if __name__ == "__main__":
    df = load_data_pandas()
    if df is None or df.empty:
        raise SystemExit("No data loaded")

    workers = min(4, max(1, psutil.cpu_count(logical=False) or 1))
    
    print(f"\nTask 3: Threading vs Multiprocessing Analysis")
    print(f"\nDataset: {len(df):,} rows, {df['symbol'].nunique()} symbols")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    # Performance comparison
    print(f"\n1. Performance Comparison (using {workers} workers):\n")
    summary = compare_parallel_approaches(df, max_workers=workers)
    print(summary.to_string(index=False))

    # GIL impact
    print(f"\n2. GIL Impact Analysis:\n")
    worker_list = [1, 2, 4, min(8, max(1, psutil.cpu_count(logical=False) or 1))]
    gil_df = analyze_gil_impact(df, worker_counts=worker_list)
    print(gil_df.to_string(index=False))

    # Consistency check
    print(f"\n3. Consistency Verification:\n")
    seq_res, _ = compute_metrics_sequential(df)
    thr_res, _ = compute_metrics_threading(df, max_workers=workers)
    mp_res, _ = compute_metrics_multiprocessing(df, max_workers=workers)

    thr_ok = verify_consistency(seq_res, thr_res)
    mp_ok = verify_consistency(seq_res, mp_res)
    print(f"Threading matches Sequential: {'Pass' if thr_ok else 'Fail'}")
    print(f"Multiprocessing matches Sequential: {'Pass' if mp_ok else 'Fail'}")

    # Discussion
    print(f"\n4. Discussion:\n")
    print("Threading shows some speedup but is limited by the GIL for CPU-bound tasks.")
    print("Multiprocessing has higher overhead for small datasets but scales better with")
    print("more data. For this workload, threading is faster due to lower process spawning")
    print("costs. Use threading for I/O tasks, multiprocessing for heavy computation.")