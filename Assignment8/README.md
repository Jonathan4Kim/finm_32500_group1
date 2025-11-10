# Interprocess Communication for Trading Systems

This folder contains our Assignment 8 submission for FINM 32500. We implemented a four-process trading stack—Gateway → OrderBook → Strategy → OrderManager—using real TCP sockets and POSIX shared memory. The goal is to stream market data, maintain a shared price book, consume sentiment, generate signals, and push executable orders in near real time.

## Architecture Overview

```
            price @9001 (TCP)                orders @62000 (TCP)
[Gateway] --------------------> [OrderBook] --------------------> [OrderManager]
    |                                 |                                   ^
    | sentiment @9002 (TCP)           | shared memory `price_book`        |
    +-------------------------------> [Strategy] -------------------------+
```

- `gateway.py` reads `market_data.csv`, replays ticks as a random-walk, and concurrently streams per-symbol sentiment integers. It pushes framed byte messages delimited by `b'*'`.
- `orderbook.py` subscribes to the price stream, initializes `SharedPriceBook`, and updates prices atomically so every strategy process shares the same view.
- `strategy.py` bundles the reusable `SentimentStrategy` and `WindowedMovingAverageStrategy`, attaches to shared memory, cross-checks both signals, and sends JSON orders to the Order Manager.
- `order_manager.py` is a multi-client TCP server that validates, logs, and acknowledges orders.
- `shared_memory_utils.py` hosts the `SharedPriceBook` wrapper plus helper metadata utilities.
- `main.py` now orchestrates the four processes end-to-end, tracking throughput/latency benchmarks for Gateway, OrderBook, and Strategy.

### Message Protocols

| Stream              | Format (UTF-8)                                    | Notes                              |
|---------------------|---------------------------------------------------|------------------------------------|
| Gateway price feed  | `"{timestamp}*{symbol}*{price}*"`                 | First frame per client is `SYMBOLS|...` |
| Gateway sentiment   | `"{timestamp}*{symbol}*{sentiment}*"`              | Sentiment ∈ [0, 100]                |
| Strategy → OM order | JSON dict (`side,symbol,qty,price,ts,id?`) + `*`  | Order Manager responds with ACK JSON + `*` |

Shared memory lives under the fixed name `price_book`. Symbols are stored as a NumPy structured array (`dtype=[('symbol','S10'),('price','f8')]`) protected by a multiprocessing lock to keep updates atomic.

## Repository Layout

| File / Dir              | Purpose |
|-------------------------|---------|
| `gateway.py`            | Dual-socket TCP server for price and sentiment streams. |
| `orderbook.py`          | Price client that hydrates and mutates shared memory. |
| `strategy.py`           | Sentiment + moving-average strategies plus order helpers. |
| `main.py`               | Process orchestrator that boots the stack and reports metrics. |
| `order_manager.py`      | Threaded TCP server that validates orders and emits ACKs. |
| `shared_memory_utils.py`| Shared memory + metadata helpers. |
| `market_data.csv`       | Historical ticks replayed by the Gateway. |
| `tests/`                | Pytest suite. |
| `performance_report.md` | Placeholder for latency/throughput measurements. |
| `video.mp4`             | Demo video showing the four processes running concurrently. |

## Prerequisites

1. Python 3.10+ (tested with CPython 3.11).
2. System packages that allow `multiprocessing.shared_memory` (Linux kernel ≥ 5.8 or macOS 12+).
3. Python deps: `numpy`, `pandas`, and `pytest` for the test suite.

Install dependencies with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install numpy pandas pytest
```

## Running the Stack

`main.py` is now the preferred entry point—it launches the Order Manager, Gateway, OrderBook, and Strategy in sequence, waits for each to warm up, and prints latency/throughput metrics when the run completes:

```bash
python main.py
```

This orchestrator counts the total ticks in `market_data.csv`, streams the feed once, and gathers runtime stats from Gateway, OrderBook, and the strategy benchmark so you can track performance changes between commits.

If you still prefer manual control (for example, to tail each log window independently), start every component in its own terminal:

1. **Order Manager** – must start first so clients can connect.
   ```bash
   python order_manager.py
   ```
2. **Gateway** – serves both TCP feeds on localhost (`9001`, `9002`).
   ```bash
   python gateway.py
   ```
3. **OrderBook** – connects to the price feed, receives the `SYMBOLS|...` bootstrap frame, and instantiates the shared memory region `price_book`.
   ```bash
   python orderbook.py
   ```
4. **Strategy** – attaches to `price_book`, streams sentiment, and starts emitting orders that satisfy both price and news signals.
   ```bash
   python strategy.py
   ```

> Tip: If you need to restart the OrderBook, call `SharedPriceBook(..., create=False).unlink()` first (as shown in `orderbook.py`) to avoid orphaned shared-memory segments.

### Configuration

Adjust host/port constants near the top of each module if you need different sockets. The stack assumes `localhost` networking and no firewall interference.

## Tests

| Test File | Focus | Notes |
|-----------|-------|-------|
| `tests/test_order_manager.py` | Live socket exchanges against the threaded Order Manager | Requires `pytest` (spins up the server on a test port) |
| `tests/test_shared_memory.py` | SharedPriceBook CRUD + strategy smoke tests | Needs `numpy` for shared memory arrays |
| `tests/test_strategy.py` | Moving-average and sentiment strategy unit coverage | Pure-Python; quick regression guardrails |
| `tests/test_serialization.py` | `SharedMemoryMetadata` persistence + overflow protection | Creates temporary shared-memory segments per test |
| `tests/test_connections.py` | Gateway helper coverage (`send_symbol_list`, `load_data`) | |

Run everything (fastest path) from the repo root:

```bash
pytest
```

## Performance & Reporting

- `performance_report.md` captures measured results from the latest orchestrated run. Highlights:
  - **Latency**: 20–50 ms from OrderBook tick receipt to OrderManager ACK (dominated by socket hops).
  - **Throughput**: Gateway streams ~8–10 ticks/sec per symbol (0.1 s pacing) with the strategy consuming 100 ticks in 28.66 s.
  - **Shared memory footprint**: ≈1 KB per symbol plus the fixed 1 KB metadata block (10 symbols → ~11 KB total).
  - **Benchmarks**: Gateway runtime 38.62 s (2.59 ticks/s), OrderBook runtime 33.64 s with ~340 ms processing latency, strategy BUY/SELL/HOLD counts logged for 100 ticks.

## Deliverables & Verification

- **Code** – all required modules live in this directory.
- **Video** – `video.mp4` showcases the processes running side-by-side.
- **Documentation** – this README plus `performance_report.md`.
- **Tests** – Order Manager covered.

## Troubleshooting & Next Steps

- If sockets refuse connections, ensure previous processes have exited so ports 9001/9002/62000 are free (`lsof -i :9001`).
- Shared memory segments persist until unlinked; use Python REPL with `SharedPriceBook(symbols=['DUMMY'], name='price_book', create=False).unlink()` for cleanup.
- When starting components manually, ensure `orderbook.py` is running before the strategy so the `trading_metadata` and `price_book` shared-memory segments exist; `main.py` already enforces this ordering.
- Extend the placeholder tests to cover serialization, shared memory propagation, and signal logic as outlined in the assignment brief.
