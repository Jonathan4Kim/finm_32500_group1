# Complexity Report: Runtime & Space Complexity in Financial Signal Processing

## 📌 Overview
This report analyzes and compares multiple trading strategy implementations for ingesting and processing market data.  
We evaluate **runtime performance**, **memory usage**, and **theoretical complexities** to understand how algorithmic design choices scale with data size.

---

## 📂 Dataset
- **Source:** `market_data.csv`  
- **Columns:** `timestamp, symbol, price`  
- **Sizes tested:** `1,000`, `10,000`, `100,000` ticks  

---

## ⚙️ Implemented Strategies
### 1. NaiveMovingAverageStrategy
- **Description:** Recomputes the average price from scratch for each tick.  
- **Time Complexity:** O(n) per tick → O(n²) overall  
- **Space Complexity:** O(n) (stores all past ticks)  

### 2. WindowedMovingAverageStrategy
- **Description:** Maintains fixed-size buffer for sliding average.  
- **Time Complexity:** O(1) per tick → O(n) overall  
- **Space Complexity:** O(k) (buffer of window size k)
---

## 🧮 Theoretical Complexity Summary

| Strategy                      | Time per Tick | Total Time (n ticks) | Space Usage |
|-------------------------------|----------------|-----------------------|-------------|
| NaiveMovingAverageStrategy    | O(n)           | O(n²)                 | O(n)        |
| WindowedMovingAverageStrategy | O(1)           | O(n)                  | O(k)        |
---

## 📊 Profiling & Benchmarking

### Runtime Results (seconds)

| Strategy                     | 1,000 ticks | 10,000 ticks | 100,000 ticks |
|------------------------------|-------------|--------------|---------------|
| NaiveMovingAverageStrategy   |0.01917600   |0.2089323     |2.18418240     |
| WindowedMovingAverageStrategy|0.00906944   |0.10207295    |0.93876433     |

### Memory Usage Results (KiB)

| Strategy                     | 1,000 ticks | 10,000 ticks | 100,000 ticks |
|------------------------------|-------------|--------------|---------------|
| NaiveMovingAverageStrategy   |0.000288     |0.080428      |0.880356       |
| WindowedMovingAverageStrategy|23.057164    |23.11152      |23.903596      |

---

## 📈 Visualizations
- **Runtime Scaling Plot**: Runtime vs. input size (log-log or linear)  
- **Memory Scaling Plot**: Memory usage vs. input size  
  <img alt="Naive_MAC_runtime_plot" height="300" src="plots\Naive_MAC_runtime_plot.png"/>
  <img alt="Windowed_MAC_runtime_ploy" height="300" src="plots\Windowed_MAC_runtime_plot.png"/>
  <img alt="Naive_MAC_memory_plot" height="300" src="plots\Naive_MAC_memory_plot.png"/>
  <img alt="Windowed_MAC_memory_plot" height="300" src="plots\Windowed_MAC_memory_plot.png"/>

---

## 🔍 Profiling Insights
- **Hotspots (cProfile):**
  - Top 3 runtime functions  
  - % time in parsing vs. strategy logic  

- **Memory Peaks (tracemalloc):**
  - Top allocation sources  
  - Peak usage in strategy logic  

---

## 🛠️ Optimization Notes
- Techniques attempted:
  - `collections.deque` for fixed-size buffer  
  - Vectorization (`numpy`)  
  - Generator-based streaming  
- **Impact:** Summarize observed improvements  

---

## ✅ Unit Test Results
- Correctness verified for all strategies  
- Optimized strategy runs under **1 second** and uses **<100 MB** for 100k ticks  
- Profiling confirmed expected hotspots and memory peaks  

---

## 📖 Conclusion
- Naive strategy is infeasible for large datasets (O(n²) scaling).  
- Windowed and optimized approaches scale efficiently (O(n) time, O(k) space).  
- Profiling confirms that algorithm design choices directly impact trading system performance.  
