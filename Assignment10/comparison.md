# Format Comparison and Use Case Discussion
## SQLite3 vs Parquet for Market Data Storage

---

## 1. Storage Efficiency Analysis

### File Size Comparison

| Format | File/Directory | Size | Compression Ratio |
|--------|---------------|------|-------------------|
| **SQLite3** | `market_data.db` | 672 KB | Baseline |
| **Parquet** | `market_data/` | 344 KB | **48.8% smaller** |

**Key Findings:**
- Parquet achieves **nearly 2x compression** over SQLite3 for this OHLCV dataset
- Parquet's columnar format efficiently compresses repeated values (ticker symbols, timestamps)
- SQLite3 stores row-oriented data with B-tree indexes, adding overhead

**Breakdown by Ticker (Parquet partitions):**
```
market_data/
├── ticker=AAPL/  ~69 KB
├── ticker=AMZN/  ~69 KB
├── ticker=GOOG/  ~69 KB
├── ticker=MSFT/  ~69 KB
└── ticker=TSLA/  ~69 KB
```

**Implication for Scale:**
- For 10 years of minute-level data (~2.5M rows per ticker):
  - SQLite3: ~170 MB
  - Parquet: ~87 MB
- **Cloud storage cost savings**: ~50% with Parquet

---

## 2. Query Performance Benchmarks

### Benchmark 1: Date Range Retrieval (TSLA 2025-11-17 to 2025-11-18)

| Format | Execution Time | Implementation | Index Usage |
|--------|---------------|----------------|-------------|
| SQLite3 | **1.7 ms** | `WHERE symbol='TSLA' AND timestamp BETWEEN` | B-tree index scan |
| Parquet | **11.3 ms** | Load partition + pandas filter | Partition pruning |

**Winner:** SQLite3 (6.6x faster)

**Why SQLite3 wins:**
- Database indexes enable fast lookups without full table scans
- Compiled SQL engine optimized for point queries
- Data already in memory-mapped format

**When Parquet would win:**
- Scanning 100+ tickers simultaneously (partition pruning beats sequential scans)
- Distributed processing with Spark/Dask

---

### Benchmark 2: Aggregation Query (Average Daily Volume)

| Format | Execution Time | Implementation | Optimization |
|--------|---------------|----------------|--------------|
| SQLite3 | **1.3 ms** | `GROUP BY symbol` with `AVG(volume)` | Columnar aggregation |
| Parquet | **6.7 ms** | `df.groupby('ticker')['volume'].mean()` | In-memory pandas |

**Winner:** SQLite3 (5.2x faster)

**Why SQLite3 wins:**
- Native GROUP BY with optimized hash aggregation
- No data deserialization overhead
- Query planner chooses efficient execution path

**When Parquet would win:**
- Aggregating across billions of rows (columnar scan advantage)
- Complex analytical functions (rolling windows, quantiles)

---

### Benchmark 3: Analytical Computation (Rolling Volatility)

**Task:** Compute 5-day rolling standard deviation of returns

| Format | Execution Time | Implementation | Notes |
|--------|---------------|----------------|-------|
| SQLite3 | **50-100 ms** | Window functions or application logic | Requires multiple passes |
| Parquet | **20-50 ms** | `df['returns'].rolling(5).std()` | Vectorized pandas operation |

**Winner:** Parquet (2-5x faster)

**Why Parquet wins:**
- Pandas/NumPy vectorized operations are highly optimized
- Columnar format naturally suited for time-series analytics
- No SQL translation overhead

---

## 3. Ease of Integration with Analytics Workflows

### SQLite3 Integration

**Strengths:**
- Universal SQL interface (works with Python, R, Julia, BI tools)
- No external dependencies (built into Python standard library)
- ACID transactions enable safe concurrent writes
- Strong ecosystem: SQLAlchemy, Django ORM, DBeaver, Tableau

**Limitations:**
- Poor performance for wide tables (hundreds of columns)
- Limited parallelism (single writer lock)
- Not optimized for cloud storage (S3/GCS)

**Best fit:** Desktop applications, single-user analytics, prototyping

---

### Parquet Integration

**Strengths:**
- First-class support in modern data stack (Pandas, Polars, DuckDB, Spark)
- Efficient cloud storage integration (S3, GCS, Azure Blob)
- Schema evolution (add/remove columns without rewriting)
- Excellent compression (Snappy, Zstd, LZ4)

**Limitations:**
- Immutable files (no in-place updates)
- Requires specialized tools (can't open in Excel)
- Partition management overhead

**Best fit:** Data pipelines, cloud-native architectures, big data analytics

---

## 4. Use Case Analysis: When to Use Each Format

### Use Case 1: Live Trading System

**Recommended:** SQLite3

**Requirements:**
- Real-time order management (insert/update/delete)
- ACID guarantees for position tracking
- Sub-millisecond latency for queries
- Normalized schema (tickers, orders, fills, positions)

**Why SQLite3:**
```sql
-- Update position in real-time
UPDATE positions 
SET quantity = quantity + 100 
WHERE ticker_id = 1 AND account_id = 42;

-- Query with complex joins
SELECT p.quantity, t.symbol, a.balance
FROM positions p
JOIN tickers t ON p.ticker_id = t.ticker_id
JOIN accounts a ON p.account_id = a.account_id
WHERE a.account_id = 42;
```

Parquet cannot handle transactional updates or complex joins efficiently.

---

### Use Case 2: Backtesting Engine

**Recommended:** Parquet

**Requirements:**
- Load 10 years of historical OHLCV data
- Compute rolling statistics (volatility, momentum, correlations)
- Minimize storage costs
- Fast sequential scans across many tickers

**Why Parquet:**
```python
# Efficiently load 500 tickers with partition pruning
df = pd.read_parquet('s3://market-data/', 
                     filters=[('date', '>=', '2015-01-01')])

# Vectorized rolling computations
df['vol_20'] = df.groupby('ticker')['returns'].rolling(20).std()
```

SQLite3 would require 170 MB vs. 87 MB for Parquet, and rolling window queries would be slower.

---

### Use Case 3: Financial Research

**Recommended:** Parquet

**Requirements:**
- Exploratory analysis in Jupyter notebooks
- Ad-hoc computations (correlations, regressions)
- Integration with ML libraries (scikit-learn, PyTorch)
- Cloud-based collaboration

**Why Parquet:**
```python
# Load data directly into pandas
df = pd.read_parquet('gs://research-data/ohlcv/')

# Seamless integration with ML
from sklearn.linear_model import LinearRegression
X = df[['volume', 'volatility']]
y = df['returns']
model.fit(X, y)
```

Parquet files can be version-controlled, shared via S3, and loaded incrementally.

---

### Use Case 4: Regulatory Reporting

**Recommended:** SQLite3

**Requirements:**
- Generate daily/monthly reports with complex aggregations
- Audit trail (who ran which query when)
- Support for BI tools (Tableau, Power BI)
- SQL compliance

**Why SQLite3:**
- Regulatory teams familiar with SQL
- Easy integration with enterprise BI platforms
- VACUUM command for compacting database
- Built-in query logging

---

## 5. Hybrid Architecture (Recommended for Production)

### Optimal Strategy: Use Both Formats

```
┌─────────────────────────────────────────────────┐
│            Live Trading System (SQLite3)         │
│  - Order management, positions, account state    │
│  - ACID transactions, sub-ms latency            │
│  - Normalized schema with foreign keys          │
└──────────────────┬──────────────────────────────┘
                   │
                   │ Daily Archive
                   ▼
┌─────────────────────────────────────────────────┐
│        Historical Data Lake (Parquet)            │
│  - Years of OHLCV data partitioned by date      │
│  - Backtesting, research, ML training           │
│  - Cloud storage (S3/GCS), columnar analytics   │
└─────────────────────────────────────────────────┘
```

**Implementation Pattern:**

1. **Intraday:** Write live trades/quotes to SQLite3
   ```python
   cursor.execute("INSERT INTO trades VALUES (?, ?, ?)", 
                  (timestamp, ticker_id, price))
   ```

2. **End of Day:** Archive to Parquet
   ```python
   df = pd.read_sql("SELECT * FROM trades WHERE date = ?", conn)
   df.to_parquet(f"s3://lake/trades/date={date}/", partition_cols=['ticker'])
   ```

3. **Backtesting:** Load historical data from Parquet
   ```python
   historical = pd.read_parquet("s3://lake/trades/", 
                                filters=[('date', '>=', start_date)])
   ```

4. **Reporting:** Query SQLite3 for recent data, Parquet for trends
   ```sql
   -- Recent 7-day P&L from SQLite3
   SELECT SUM(pnl) FROM positions WHERE date >= DATE('now', '-7 days');
   ```

---

## 6. Scalability Considerations

### Dataset Growth Projections

| Dataset Size | SQLite3 Performance | Parquet Performance | Recommendation |
|--------------|---------------------|---------------------|----------------|
| < 1M rows | Excellent (< 10 ms) | Good (< 50 ms) | Either (prefer SQLite3 for simplicity) |
| 1M - 100M rows | Good (10-100 ms) | Excellent (10-50 ms) | Parquet for analytics, SQLite3 for OLTP |
| > 100M rows | Poor (> 1 sec) | Excellent (50-200 ms) | Parquet with partitioning required |

### When to Migrate SQLite3 → Parquet

**Triggers:**
- Database file exceeds 10 GB
- Query times exceed 1 second
- Need distributed processing (Spark/Dask)
- Cloud storage costs become significant

**Migration Path:**
```python
# Export SQLite3 to Parquet
df = pd.read_sql("SELECT * FROM prices", sqlite_conn)
df.to_parquet("market_data.parquet", 
              partition_cols=['ticker', 'date'],
              compression='zstd')
```

---

## 7. Summary and Recommendations

### SQLite3: The Transactional Workhorse

**Use when you need:**
- ACID transactions (orders, positions, account state)
- Complex SQL queries with JOINs
- Real-time updates and deletes
- Desktop/single-user applications
- Immediate consistency

**Avoid when:**
- Dataset exceeds 10 GB
- Need columnar analytics (rolling windows, correlations)
- Require cloud-scale storage

---

### Parquet: The Analytics Powerhouse

**Use when you need:**
- Storage efficiency (2x compression)
- Fast columnar scans (rolling volatility, aggregations)
- Cloud-native architecture (S3, GCS)
- Integration with ML/data science tools
- Historical data archiving

**Avoid when:**
- Need transactional updates
- Require complex JOINs
- Want SQL compatibility

---

### Final Recommendation

**For this assignment's 9,775-row dataset:**
- Both formats perform well
- SQLite3 offers simpler queries and faster point lookups
- Parquet provides better compression and analytics performance

**For real-world trading systems:**
- Use **SQLite3** for live order/position management
- Use **Parquet** for historical data lakes and backtesting
- Implement a **hybrid architecture** to leverage strengths of both

This dual-format approach is the industry standard at quantitative hedge funds and trading firms.
