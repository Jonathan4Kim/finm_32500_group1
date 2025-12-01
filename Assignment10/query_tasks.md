# Query Tasks - Results and Performance

## SQLite3 Queries

### Task 1: Retrieve all data for TSLA between 2025-11-17 and 2025-11-18

**Query:**
```sql
SELECT 
    p.timestamp,
    t.symbol,
    p.open,
    p.high,
    p.low,
    p.close,
    p.volume
FROM prices p
JOIN tickers t ON p.ticker_id = t.ticker_id
WHERE t.symbol = 'TSLA'
    AND p.timestamp BETWEEN '2025-11-17' AND '2025-11-18'
ORDER BY p.timestamp
```

**Results:**
- **Rows returned:** 391
- **Execution time:** ~1-2 ms
- **First row:** 2025-11-17 09:30:00, TSLA, open=268.31, close=268.07
- **Last row:** 2025-11-17 16:00:00, TSLA, open=286.19, close=286.86

**Sample Output:**
```
               timestamp symbol    open    high     low   close  volume
0    2025-11-17 09:30:00   TSLA  268.31  268.51  267.95  268.07    1609
1    2025-11-17 09:31:00   TSLA  268.94  269.11  268.28  269.04    4809
...
389  2025-11-17 15:59:00   TSLA  287.03  287.55  286.69  287.38    2308
390  2025-11-17 16:00:00   TSLA  286.19  286.89  285.28  286.86    1496
```

---

### Task 2: Calculate average daily volume per ticker

**Query:**
```sql
SELECT 
    t.symbol,
    AVG(p.volume) as avg_daily_volume
FROM prices p
JOIN tickers t ON p.ticker_id = t.ticker_id
GROUP BY t.symbol
ORDER BY t.symbol
```

**Results:**
- **Execution time:** ~1-3 ms
- **Rows returned:** 5 (one per ticker)

**Output:**
```
  symbol  avg_daily_volume
    AAPL       2767.83
    AMZN       2753.42
    GOOG       2740.16
    MSFT       2686.55
    TSLA       2777.42
```

---

### Task 3: Identify top 3 tickers by return over the full period

**Query:**
```sql
WITH first_last_prices AS (
    SELECT 
        t.symbol,
        (SELECT p.close FROM prices p 
         WHERE p.ticker_id = t.ticker_id 
         ORDER BY p.timestamp ASC LIMIT 1) as first_close,
        (SELECT p.close FROM prices p 
         WHERE p.ticker_id = t.ticker_id 
         ORDER BY p.timestamp DESC LIMIT 1) as last_close
    FROM tickers t
)
SELECT 
    symbol,
    first_close,
    last_close,
    ROUND(((last_close - first_close) / first_close) * 100, 2) as return_pct
FROM first_last_prices
WHERE first_close IS NOT NULL AND last_close IS NOT NULL
ORDER BY return_pct DESC
LIMIT 3
```

**Results:**
- **Execution time:** ~2-4 ms
- **Period:** 2025-11-17 09:30:00 to 2025-11-21 16:00:00

**Output:**
```
  symbol  first_close  last_close  return_pct
    MSFT       183.89      245.70       33.61%
    AAPL       270.88      334.57       23.51%
    GOOG       139.43      153.90       10.38%
```

**Analysis:** MSFT had the highest return (+33.61%) over the 5-day period, followed by AAPL (+23.51%). TSLA and AMZN had positive but lower returns.

---

### Task 4: Find first and last trade price for each ticker per day

**Query:**
```sql
SELECT 
    t.symbol,
    DATE(p.timestamp) as date,
    (SELECT p2.close FROM prices p2 
     WHERE p2.ticker_id = p.ticker_id 
       AND DATE(p2.timestamp) = DATE(p.timestamp)
     ORDER BY p2.timestamp ASC LIMIT 1) as first_price,
    (SELECT p3.close FROM prices p3 
     WHERE p3.ticker_id = p.ticker_id 
       AND DATE(p3.timestamp) = DATE(p.timestamp)
     ORDER BY p3.timestamp DESC LIMIT 1) as last_price
FROM prices p
JOIN tickers t ON p.ticker_id = t.ticker_id
GROUP BY t.symbol, DATE(p.timestamp)
ORDER BY t.symbol, date
```

**Results:**
- **Execution time:** ~3-5 ms
- **Rows returned:** 25 (5 tickers × 5 days)

**Sample Output:**
```
   symbol        date  first_price  last_price
     AAPL  2025-11-17       270.88      287.68
     AAPL  2025-11-18       287.48      289.52
     AAPL  2025-11-19       288.80      295.87
     AAPL  2025-11-20       296.99      319.43
     AAPL  2025-11-21       319.63      334.57
     MSFT  2025-11-17       183.89      215.36
     MSFT  2025-11-18       214.90      242.24
     TSLA  2025-11-21       266.75      292.32
```

**Analysis:** This query enables intraday range analysis, showing opening and closing prices for each trading day.

---

## Parquet Queries

### Task 1: Load all data for AAPL and compute 5-minute rolling average of close price

**Code:**
```python
ParquetStorage.load_ticker_parquet("AAPL")
ParquetStorage.compute_rolling_close_avg("AAPL")
```

**Results:**
- **Execution time:** ~10-20 ms (includes loading partition and computation)
- **Rows returned:** 1955 (all AAPL data)
- **Partition:** `market_data/ticker=AAPL/`

**Sample Output:**
```
               timestamp   close  close_5min_avg
0    2025-11-17 09:30:00  270.88      270.880000
1    2025-11-17 09:31:00  269.24      270.060000
2    2025-11-17 09:32:00  270.86      270.326667
3    2025-11-17 09:33:00  269.28      270.065000
4    2025-11-17 09:34:00  269.32      269.916000
...
1954 2025-11-21 16:00:00  334.57      332.636000
```

**Analysis:** The 5-minute rolling average smooths out short-term price fluctuations, useful for identifying trends and reducing noise in trading signals.

---

### Task 2: Compute 5-day rolling volatility (std dev) of returns for each ticker

**Code:**
```python
for ticker in ["AAPL", "AMZN", "GOOG", "MSFT", "TSLA"]:
    ParquetStorage.compute_rolling_volatility(ticker)
```

**Results:**
- **Execution time:** ~15-25 ms per ticker
- **Metric:** Rolling standard deviation of 5-period returns

**Latest 5-Day Rolling Volatility (as of 2025-11-21 16:00:00):**
```
Ticker  Close    5-Day Vol
AAPL    334.57   0.003023  (0.30%)
AMZN     77.16   0.006473  (0.65%)
GOOG    153.90   0.006917  (0.69%)
MSFT    245.70   0.005664  (0.57%)
TSLA    292.32   0.004198  (0.42%)
```

**Analysis:** GOOG shows the highest recent volatility (0.69%), while AAPL is the most stable (0.30%). This metric is critical for risk management and position sizing in trading strategies.

---

### Task 3: Compare query time and file size with SQLite3 for Task 1

**Comparison: TSLA Date Range Query (2025-11-17 to 2025-11-18)**

| Metric | SQLite3 | Parquet | Winner |
|--------|---------|---------|--------|
| **Query Time** | ~1-2 ms | ~10-15 ms | SQLite3 (5-10x faster) |
| **Storage Size** | 672 KB | 344 KB | Parquet (2x smaller) |
| **Rows Returned** | 391 | 391 | Tie (same data) |
| **Code Complexity** | SQL query | Python + pandas filter | SQLite3 (simpler) |

**File Size Details:**
- **SQLite3:** `market_data.db` = 672 KB
- **Parquet:** `market_data/` directory = 344 KB total
  - Per-ticker partitions: ~69 KB each
  - Includes all 5 tickers

**Performance Notes:**
- **SQLite3 wins on query speed** for small datasets due to indexed lookups and optimized SQL engine
- **Parquet wins on storage efficiency** due to columnar compression (Snappy codec)
- **Parquet advantage grows** with larger datasets (millions of rows) due to partition pruning
- **SQLite3 better for ad-hoc queries**, Parquet better for analytical pipelines

---

## Summary

### SQLite3 Performance Profile
- **Strengths:** Fast queries (1-5 ms), flexible SQL, good for complex joins
- **Best for:** Real-time trading, transactional workloads, exploratory analysis
- **File size:** 672 KB

### Parquet Performance Profile
- **Strengths:** 2x storage savings, excellent for analytics, partitioned reads
- **Best for:** Historical archives, backtesting, columnar analytics
- **File size:** 344 KB

### Key Insight
For this 9,775-row dataset, SQLite3 is faster for queries but Parquet is more storage-efficient. At scale (millions of rows), Parquet's partition pruning and columnar compression would likely outperform SQLite3 for analytical workloads.
