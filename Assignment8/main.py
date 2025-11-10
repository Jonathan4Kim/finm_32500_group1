"""
Process orchestrator for Assignment 8

Starts OrderManager, Gateway, OrderBook, and a Strategy benchmark in that order.
Also reports simple latency and throughput metrics derived from the run.
"""

from __future__ import annotations

import csv
import multiprocessing as mp
import queue
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import gateway
import orderbook
from order_manager import run_ordermanager

# MARKET_DATA_PATH = Path(__file__).with_name("market_data.csv")
MARKET_DATA_PATH = Path(__file__).with_name("market_data.csv")

def _count_market_ticks(csv_path: Path) -> int:
    with open(csv_path, newline="") as fp:
        reader = csv.reader(fp)
        next(reader, None)  # skip header
        return sum(1 for _ in reader)


def _order_manager_worker():
    run_ordermanager()


def _gateway_worker(metric_queue: mp.Queue):
    start = time.perf_counter()
    try:
        gateway.main()
    finally:
        duration = time.perf_counter() - start
        metric_queue.put({"component": "gateway", "duration": duration})


def _orderbook_worker(metric_queue: mp.Queue):
    start = time.perf_counter()
    try:
        data_points = orderbook.get_price_client()
    finally:
        duration = time.perf_counter() - start
        metric_queue.put(
            {
                "component": "orderbook",
                "duration": duration,
                "ticks_processed": len(data_points) if "data_points" in locals() else 0,
            }
        )


def _strategy_worker(metric_queue: mp.Queue, _csv_path: Path):
    """Run the live sentiment + moving average strategy and report metrics."""

    import socket
    from datetime import datetime

    from strategy import (
        SENTIMENT_HOST,
        SENTIMENT_PORT,
        MarketDataPoint,
        SentimentDataPoint,
        SentimentStrategy,
        WindowedMovingAverageStrategy,
        initialize_strategy_book,
        send_order,
    )

    start = time.perf_counter()
    buys = sells = holds = ticks_processed = 0
    orders_submitted = orders_acknowledged = rejected_orders = 0
    parse_errors = 0
    last_error: Optional[str] = None

    price_book = initialize_strategy_book()
    if price_book is None:
        duration = time.perf_counter() - start
        metric_queue.put(
            {
                "component": "strategy",
                "duration": duration,
                "ticks_processed": 0,
                "buys": 0,
                "sells": 0,
                "holds": 0,
                "orders_submitted": 0,
                "orders_acknowledged": 0,
                "rejected_orders": 0,
                "errors": 1,
                "last_error": "Price book unavailable",
            }
        )
        return

    sent_strategy = SentimentStrategy()
    ma_strategy = WindowedMovingAverageStrategy(s=5, l=20)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((SENTIMENT_HOST, SENTIMENT_PORT))

            while True:
                response = client.recv(1024)
                if not response:
                    break

                parts = response.decode().split("*")[:-1]
                if len(parts) < 3:
                    parse_errors += 1
                    continue

                ts_raw, symbol, sentiment_raw = parts[:3]

                try:
                    timestamp = datetime.strptime(ts_raw, "%Y-%m-%d %H:%M:%S")
                    sentiment = float(sentiment_raw)
                except ValueError as exc:
                    parse_errors += 1
                    last_error = str(exc)
                    continue

                price = price_book.read(symbol)
                if price is None:
                    parse_errors += 1
                    last_error = f"No price for symbol {symbol}"
                    continue

                sdp = SentimentDataPoint(timestamp, symbol, sentiment)
                sent_signal = sent_strategy.generate_signal(sdp)

                tick = MarketDataPoint(timestamp, symbol, price)
                ma_signal = ma_strategy.generate_signals(tick)
                if isinstance(ma_signal, list):
                    ma_signal = ma_signal[0] if ma_signal else "HOLD"

                ticks_processed += 1
                if ma_signal == "BUY":
                    buys += 1
                elif ma_signal == "SELL":
                    sells += 1
                else:
                    holds += 1

                if sent_signal != ma_signal:
                    continue

                my_order = {
                    "side": sent_signal,
                    "symbol": symbol,
                    "qty": 10,
                    "price": price,
                }

                try:
                    acknowledgment = send_order(my_order)
                    orders_submitted += 1
                    if acknowledgment.get("ok"):
                        orders_acknowledged += 1
                    else:
                        rejected_orders += 1
                except ConnectionRefusedError as exc:
                    last_error = f"Order manager unavailable: {exc}"
                    parse_errors += 1
                except Exception as exc:  # noqa: BLE001
                    last_error = str(exc)
                    parse_errors += 1
    except Exception as exc:  # noqa: BLE001
        last_error = str(exc)
    finally:
        duration = time.perf_counter() - start
        metric_queue.put(
            {
                "component": "strategy",
                "duration": duration,
                "ticks_processed": ticks_processed,
                "buys": buys,
                "sells": sells,
                "holds": holds,
                "orders_submitted": orders_submitted,
                "orders_acknowledged": orders_acknowledged,
                "rejected_orders": rejected_orders,
                "errors": parse_errors,
                "last_error": last_error,
            }
        )


def _collect_metrics(
    metric_queue: mp.Queue, expected_count: int
) -> Dict[str, Dict[str, Any]]:
    metrics: Dict[str, Dict[str, Any]] = {}
    for _ in range(expected_count):
        try:
            entry = metric_queue.get(timeout=10)
        except queue.Empty:
            break
        metrics[entry["component"]] = entry
    return metrics


def _print_benchmarks(metrics: Dict[str, Dict[str, Any]], total_ticks: int):
    print("\n=== Latency & Throughput Benchmarks ===")
    gateway_stats = metrics.get("gateway")
    orderbook_stats = metrics.get("orderbook")
    strategy_stats = metrics.get("strategy")

    if gateway_stats:
        dur = gateway_stats["duration"]
        throughput = total_ticks / dur if dur else 0.0
        print(f"Gateway runtime: {dur:.2f}s | Throughput: {throughput:.2f} ticks/s")
    else:
        print("Gateway metrics unavailable.")

    if orderbook_stats:
        dur = orderbook_stats["duration"]
        ticks = orderbook_stats.get("ticks_processed", total_ticks)
        avg_latency = (dur / ticks) if ticks else 0.0
        print(
            f"OrderBook runtime: {dur:.2f}s | Avg processing latency: {avg_latency*1000:.2f} ms/tick"
        )
    else:
        print("OrderBook metrics unavailable.")

    if strategy_stats:
        dur = strategy_stats["duration"]
        ticks = strategy_stats.get("ticks_processed", 0)
        buys = strategy_stats.get("buys", 0)
        sells = strategy_stats.get("sells", 0)
        holds = strategy_stats.get("holds", 0)
        print(
            f"Strategy offline benchmark: {dur:.2f}s | ticks={ticks} "
            f"(BUY={buys}, SELL={sells}, HOLD={holds})"
        )
    else:
        print("Strategy metrics unavailable.")


def main():
    if not MARKET_DATA_PATH.exists():
        print(f"market_data.csv not found at {MARKET_DATA_PATH}", file=sys.stderr)
        sys.exit(1)

    total_ticks = _count_market_ticks(MARKET_DATA_PATH)
    metric_queue: mp.Queue = mp.Queue()

    processes = []
    try:
        om_proc = mp.Process(target=_order_manager_worker, name="OrderManager")
        om_proc.start()
        processes.append(om_proc)
        time.sleep(5)

        gateway_proc = mp.Process(
            target=_gateway_worker, args=(metric_queue,), name="Gateway"
        )
        gateway_proc.start()
        processes.append(gateway_proc)
        time.sleep(5)

        orderbook_proc = mp.Process(
            target=_orderbook_worker, args=(metric_queue,), name="OrderBook"
        )
        orderbook_proc.start()
        processes.append(orderbook_proc)
        time.sleep(5)

        strategy_proc = mp.Process(
            target=_strategy_worker,
            args=(metric_queue, MARKET_DATA_PATH),
            name="Strategy",
        )
        strategy_proc.start()
        processes.append(strategy_proc)

        gateway_proc.join()
        orderbook_proc.join()
        strategy_proc.join()

        metrics = _collect_metrics(metric_queue, expected_count=3)
        _print_benchmarks(metrics, total_ticks)

    except KeyboardInterrupt:
        print("\nInterrupted, stopping processes...")
    finally:
        for proc in processes:
            if proc.is_alive() and proc is not None:
                proc.terminate()
        for proc in processes:
            proc.join(timeout=1)


if __name__ == "__main__":
    # Ensure Ctrl+C stops all child processes
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
