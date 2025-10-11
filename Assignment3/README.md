# Assignment 3 - Runtime & Space Complexity in Financial Signal Processing

This project for **FINM 32500** analyzes how algorithmic design choices affect execution time and memory usage in financial trading systems. The module ingests market data from a CSV file, applies multiple trading strategies with varying computational complexities, and uses profiling tools to measure and compare performance.

The goal is to understand how different approaches to signal processing and trading logic affect **execution time**, **memory usage**, and **scalability** in real-world financial data applications.

---

## 📁 Project Structure

```
Assignment3/
├── plots                           # Contains memory and runtime plots for Naive MAC and Windowed MAC
|     └── Naive_MAC_memory_plot.png
|     └── Naive_MAC_runtime_plot.png
|     └── Windowed_MAC_memory_plot.png
|     └── Windowed_MAC_runtime_plot.png
|── README.md                       # Project overview and usage guide                         
├── complexity_report.md            # Summary of findings, runtime performance, and memory usage 
├── data_generator.py               # Market data simulation and CSV generation
├── data_loader.py                  # Loads market data from CSV into MarketDataPoint objects
├── ma_tests.py                     # Unit tests & performance profiling tests
├── market_data.csv                 # Generated market data file (CSV) 
├── models.py                       # MarketDataPoint and Order models
├── profiler.py                     # Profiling runtime and memory usage of strategies
└── strategies.py                   # Base Strategy class and two Moving Average implementations

```
---
## Strategy Overview

* `NaiveMovingAverageStrategy`: Recomputes averages from scratch. Time Complexity: O(n), Space Complexity: O(n)
* `WindowedMovingAverageStrategy`: Maintains a fixed-size buffer and updates averages incrementally. Time Complexity: O(1), Space Complexity: O(k)

## 🎯 Learning Objectives

* Understand the impact of algorithmic design on runtime and memory usage.
* Implement strategies with different computational complexities.
* Use profiling tools to measure performance and memory footprint.
* Visualize and compare strategy scalability.
* Explore optimization techniques to improve efficiency.
---
## ⚙️ Setup Instructions

To run the simulation and test strategies, follow these steps:

### 1. Clone the Repository

```bash
git clone https://github.com/Jonathan4Kim/finm_32500_group1.git
cd finm_32500_group1/Assignment3
````

### 2. Set Up a Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```
### 4. Load / Ingest Market Data
```bash
python data_generator.py
python data_loader.py
```
* Generates market_data.csv with simulated ticks for a chosen symbol.
* Loads CSV and converts each row into a MarketDataPoint dataclass.
* Returns a list of ticks (data_points) ready for strategy execution.

### 5. Run Strategies (optional test run for correctness checks)
```bash
python strategies.py
```
* Executes NaiveMovingAverageStrategy and WindowedMovingAverageStrategy
* Prints example signals
* Good for verifying correctness before profiling

### 6. Profile Runtime and Memory Usage 
```bash
python profiler.py
```
* Measures execution time using timeit/cProfile
* Measures peak memory using memory_profiler
* Runs strategies on 1k, 10k, 100k ticks
* Generates profiling summary (prints results and saves plots in plots/ folder)

### 7. Run Unit Tests
```bash
python -m unittest ma_tests.py
```
or 
```bash
pytest -v ma_tests.py
```
* Ensures strategies produce correct signals
* Confirms runtime and memory limits for large datasets
---
## See complexity_report.md for full breakdown of strategies, runtime, space complexity, and results

---
| File                   | Descriptions                                                                                                          |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `data_generator.py`    | Generates simulated market data and saves it to CSV.                                                                 |
| `data_loader.py`       | Loads CSV market data into `MarketDataPoint` objects.                                                                |
| `strategies.py`        | Defines the abstract Strategy class and implements `NaiveMovingAverageStrategy` and `WindowedMovingAverageStrategy`. |
| `profiler.py`          | Profiles runtime and memory usage of strategies and generates performance plots.                                     |
| `ma_tests.py`          | Unit tests and performance tests for moving average strategies.                                                      |
| `models.py`            | Defines `MarketDataPoint` and `Order` dataclasses.                                                                   |
| `market_data.csv`      | Generated market data CSV for testing strategies.                                                                    |
| `complexity_report.md` | Summary of strategy runtime, memory usage, and scalability analysis.                                                 |
| `plots/`               | Contains runtime and memory usage plots for each strategy.                                                           |
| `README.md`            | Project overview, setup instructions, and usage guide.                                                               |

---
## 📌 Requirements

See `requirements.txt` for full list, but major dependencies include:

* `matplotlib`
* `memory_profiler`
* `psutil`
* `pytest` or `unittest`

Install them all via:

```bash
pip install -r requirements.txt
```
---
## 📄 License

This project is for educational use only and part of the FINM 32500 coursework.

---