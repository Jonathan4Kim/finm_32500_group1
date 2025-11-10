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
- `strategy.py` consumes `SharedPriceBook`, listens to sentiment, runs a short/long moving-average crossover, cross-checks the news signal, and sends JSON orders to the Order Manager.
- `order_manager.py` is a multi-client TCP server that validates, logs, and acknowledges orders.
- `shared_memory_utils.py` hosts the `SharedPriceBook` wrapper plus helper metadata utilities.
- `main.py` is intentionally empty—per the assignment we start each process explicitly so logs stay isolated.

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
| `strategy.py`           | Moving-average strategy plus order pipeline utilities. |
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

Because `main.py` is a stub, run each component in its own terminal so you can tail the logs independently:

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

The automated coverage is focused on the order-routing layer:

```bash
pytest tests/test_order_manager.py
```

The remaining test files are scaffolds ready for future connectivity, serialization, shared-memory, and strategy regression tests.

## Performance & Reporting

- `performance_report.md` holds latency, throughput, and footprint numbers once you gather them. Suggested metrics:
  - Price-tick → order decision latency (measure timestamps before/after `strategy.py` sends an order).
  - Gateway ticks/second throughput (count per second inside `gateway.py`).
  - Shared-memory size: `len(symbols) * (symbol bytes + float bytes)`.
- Update the report along with screenshots or CLI snippets when you finish benchmarking.

## Deliverables & Verification

- ✅ **Code** – all required modules live in this directory.
- ✅ **Video** – `video.mp4` showcases the processes running side-by-side.
- 🚧 **Documentation** – this README plus future updates to `performance_report.md`.
- 🚧 **Tests** – Order Manager covered; add end-to-end and shared-memory tests before submission.

## Troubleshooting & Next Steps

- If sockets refuse connections, ensure previous processes have exited so ports 9001/9002/62000 are free (`lsof -i :9001`).
- Shared memory segments persist until unlinked; use Python REPL with `SharedPriceBook(symbols=['DUMMY'], name='price_book', create=False).unlink()` for cleanup.
- Strategy currently expects helper methods (`get_price`, `get_all_symbols`) on the price book; implement these wrappers in `SharedPriceBook` or adjust the strategy runner accordingly.
- Extend the placeholder tests to cover serialization, shared memory propagation, and signal logic as outlined in the assignment brief.

Once the metrics and remaining tests are in place, update `performance_report.md`, regenerate the video if behavior changes, and share the repo with the TAs (`jcolli5158`, `hyoung3`).
