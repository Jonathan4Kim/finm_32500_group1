# Assignment 7 — Performance-Aware Portfolio Analytics

This module benchmarks Pandas versus Polars for ingesting and enriching intraday market data, then evaluates parallel computing approaches for portfolio analytics. The workflow is orchestrated by `main.py`, which chains together ingestion, rolling-metric computation, portfolio aggregation, and reporting utilities located in the `Assignment7/` package.

## Key Components

| Module | Purpose |
| ------ | ------- |
| `data_loader.py` | Provides Pandas and Polars loaders plus memory-profiled variants for CSV ingestion from `market_data-1.csv`. |
| `metrics.py` | Adds rolling mean, rolling standard deviation, and rolling Sharpe ratio calculations in both Pandas and Polars; exposes a `benchmark_functions()` timer and `plot_benchmark()` helper. |
| `parallel.py` | Wraps sequential, threaded, and multiprocessing execution paths for symbol-level rolling metrics, captures CPU/memory deltas, and studies GIL impact across worker counts. |
| `portfolio.py` | Computes position-level value, volatility, and drawdown, aggregates nested portfolios defined in `portfolio_structure-1.json`, and compares sequential versus parallel execution. |
| `reporting.py` | Builds comparison tables and four Matplotlib charts (`1_execution_time.png`–`4_gil_impact.png`) summarizing ingestion, speedup, memory, and GIL experiments. |
| `performance_report.md` | Narrative summary of experimental results captured from the reporting scripts. |
| `tests/tests.py` | Pytest suite covering rolling metrics, parallel strategies, and portfolio aggregation logic. |

## Data Inputs

* `market_data-1.csv` — timestamped price observations for AAPL, MSFT, and SPY used by both Pandas and Polars loaders.
* `portfolio_structure-1.json` — nested portfolio definition with top-level holdings and an "Index Holdings" sub-portfolio consumed by `portfolio.py`.

## Running the Pipeline

From the repository root:

```bash
python Assignment7/main.py
```

The script will:

1. Time the rolling-metric functions via `metrics.benchmark_functions()`.
2. Load market data (`data_loader.load_data_pandas()`), read the portfolio JSON, and compare sequential versus parallel valuation (`portfolio.compare_modes()`).
3. Persist the enriched portfolio snapshot to `portfolio_results.json` with rounded values/volatilities/drawdowns.
4. Print ingestion and rolling-metric benchmark tables, generate the benchmark bar chart, and display the threading/multiprocessing report from `reporting.py`.
5. Save four PNG visualizations (`1_execution_time.png`–`4_gil_impact.png`) and show interactive plots.

All outputs are written to the `Assignment7/` directory.

## Performance Highlights

Performance figures captured in `performance_report.md` originate from the same scripts shipped in this package:

* **Data ingestion (`reporting.ingestion_time_comp`)** — Polars loads the CSV about 4× faster than Pandas while holding peak memory near 396 MB for both libraries, thanks to columnar parsing and lower overhead in `load_data_polars`.
* **Rolling metrics (`metrics.benchmark_functions`)** — Across 20 trials, Polars accelerates rolling mean, rolling std, and rolling Sharpe calculations by roughly 3.5× on average relative to their Pandas counterparts.
* **Parallel experiments (`parallel.compare_parallel_approaches` & `parallel.analyze_gil_impact`)** — Threading yields ~1.75× speedup versus sequential for symbol-by-symbol calculations, whereas multiprocessing suffers from process-spawn overhead on this dataset, illustrating the GIL trade-offs plotted in `4_gil_impact.png`.

These comparisons rely solely on the assets provided under `Assignment7/`.

## Implementation Notes

* Rolling calculations require `symbol` and `price` columns; each helper falls back to loading default data when `df=None`.
* Portfolio aggregation uses `ProcessPoolExecutor` for parallel mode and returns nested JSON-ready dictionaries with rounded metrics.
* Performance tracking leverages `timeit`, `psutil`, and `memory_profiler`, so those dependencies must be installed alongside `pandas`, `polars`, `matplotlib`, and `numpy`.

## Testing

Execute the automated coverage from the project root:

```bash
pytest Assignment7/tests/tests.py
```

The suite validates column expectations, numerical consistency between Pandas and Polars outputs, correctness of threading/multiprocessing pathways, and recursive portfolio aggregation behavior.
