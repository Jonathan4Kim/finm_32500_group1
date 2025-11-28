# Assignment 10 – Market Data Storage & Reporting

Python workflow for ingesting multi-ticker OHLCV data, persisting it in SQLite and Parquet, and comparing how each format supports typical analytics queries.

## Project Structure

- `data_loader.py` – validates `data/market_data_multi.csv` and `data/tickers.csv`.
- `sqlite_storage.py` – applies `data/schema.sql`, loads normalized tables, and exposes SQL query helpers.
- `parquet_storage.py` – materializes a ticker-partitioned Parquet dataset plus rolling metrics helpers.
- `reporting.py` – orchestrates the full workflow, captures benchmark metrics, and prints the results.
- `tests/` – pytest suite covering ingestion, schema creation, data insertion, and analytics helpers.

## Environment

Tested with Python 3.11 and the following key packages:

```
pip install pandas pyarrow pytest
```

The default relative paths assume commands are executed from the `Assignment10/` directory.

## Running the Reporting Workflow

```
cd Assignment10
python reporting.py
```

The script performs:

1. CSV ingestion and validation (9775 rows, 5 tickers, 2025-11-17 through 2025-11-21).
2. SQLite refresh (`market_data.db`), inserts data once, and executes the four required SQL queries.
3. Parquet conversion (`market_data/` partitioned by `ticker`), ticker-level data pulls, and 5-day rolling volatility.
4. Storage comparison: file sizes plus query timings for (a) TSLA range retrieval and (b) average daily volume.

Sample comparison output from the dataset:

| Format  | Artifact        | Size     | TSLA range query | Avg volume query |
|---------|-----------------|----------|------------------|------------------|
| SQLite  | `market_data.db` | 672 KB   | 1.7 ms           | 1.3 ms           |
| Parquet | `market_data/`   | 337 KB   | 11.3 ms          | 6.7 ms           |

Key query highlights:

- TSLA 2-day slice returns 782 bars and mirrors the Parquet partition pull.
- Average daily volume per ticker spans ~2.74–2.78K shares and matches across both formats.
- Top 3 tickers by return over the sample window: MSFT (33.6%), AAPL (23.5%), GOOG (10.4%).
- 5-day rolling volatility (latest point) ranges from ~0.30% (AAPL) to ~0.69% (GOOG).

## Tests

```
cd Assignment10
pytest tests
```

The suite verifies schema creation, insert logic, SQL query structure, Parquet partitioning, and rolling analytics helpers.

## Notes

- Parquet conversion may emit `sysctl` warnings inside sandboxed macOS environments; they are harmless.
- Re-running `reporting.py` overwrites `market_data.db` and the `market_data/` directory to keep artifacts in sync.
