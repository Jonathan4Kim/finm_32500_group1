# Assignment 2 – Multi-Signal Strategy Simulation on S&P 500

This project is a market data simulation and trading strategy backtesting engine built for **FINM 32500**. It simulates trading strategies on generated market data and evaluates performance metrics like total return, Sharpe ratio, and max drawdown.

---

## 📁 Project Structure

```

Assignment2/
├── benchmark_strategy.py           # Implements a static strategy that buys at start of simulation
├── data_loader.py                  # Load market data into usable dataframe
├── engine.py                       # Simulation engine and trade execution logic
├── macd_strategy.py                # Implementation of MACD strategy
├── main.py                         # Entry point with client code to run simulations
├── models.py                       # Data models: Order, MarketDataPoint, etc.
├── moving_average_strategy.py      # Implementation of moving average strategy
├── price_loader.py                 # Gather market data from Yahoo Finance API
├── README.md                       # Project overview and usage guide
├── reporting.py                    # Utility functions for performance reporting
├── requirements.txt                # Python dependencies
├── rsi_strategy.py                 # Implementation of RSI strategy
├── strategies.py                   # Strategy abstraction 
├── strategy_comparison.ipynb       # Compare strategy performances with analysis + plots
└── volatility_breakout_strategy.py # Implementation of volatility breakout strategy

````

---

## ⚙️ Setup Instructions

To run the simulation and test strategies, follow these steps:

### 1. Clone the Repository

```bash
git clone https://github.com/Jonathan4Kim/finm_32500_group1.git
cd finm_32500_group1/Assignment2
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

### 4. Run Gather Market Data

```bash
python price_loader.py
```

### 5. Run the Simulation

```bash
python main.py
```

---

| File                              | Description                                                                                                                                          |
| --------------------------------- |------------------------------------------------------------------------------------------------------------------------------------------------------|
| `benchmark_strategy.py`           | Implements a baseline strategy that purchases assets at the beginning of the simulation and holds throughout. Useful for comparing active strategies. |
| `data_loader.py`                  | Loads market data from relavant parquet files into a usable dataframe.                                                                               |
| `engine.py`                       | Core simulation engine that manages the flow of time, applies strategies, executes trades, updates positions, and logs performance.                  |
| `macd_strategy.py`                | Strategy implementation based on the Moving Average Convergence Divergence (MACD) indicator for identifying trend reversals.                         |
| `main.py`                         | Main script to configure and run the simulation. Sets up market data, selects strategies, and triggers performance analysis.                         |
| `models.py`                       | Contains object definitions such as `Order`, and `MarketDataPoint`. Serves as the core data schema for the project.                                  |
| `moving_average_strategy.py`      | Implements a moving average crossover strategy using short-term and long-term moving averages to determine buy/sell signals.                         |
| `price_loader.py`                 | Downloads historical market data from Yahoo Finance API and preprocesses it for use in simulations.                                           |
| `README.md`                       | Project overview, setup instructions, and usage guide for running simulations and analyzing results.                                                 |
| `reporting.py`                    | Provides utility functions for calculating and reporting key performance metrics such as total return, Sharpe ratio, and drawdowns.                  |
| `requirements.txt`                | Lists all required Python packages and dependencies needed to run the simulation environment.                                                        |
| `rsi_strategy.py`                 | Implements a strategy based on the Relative Strength Index (RSI) to identify overbought or oversold conditions in the market.                        |
| `strategies.py`                   | Defines the abstract base `Strategy` class and outlines the interface all strategy implementations must follow.                                      |
| `strategy_comparison.ipynb`       | Jupyter Notebook that runs simulations across multiple strategies and visualizes comparative performance through plots and summary statistics.       |
| `volatility_breakout_strategy.py` | Implements a strategy that looks for price breakouts beyond a volatility threshold, aiming to capture large directional moves.                       |

---

## 📊 Example Performance Analysis

Open the Jupyter Notebook to explore how strategies compared:

```bash
jupyter notebook strategy_comparison.ipynb
```

Inside the notebook, you'll find:

* 📈 Performance charts
* 📉 Maximum drawdown
* 📈 Sharpe ratio calculation
* 📊 Comparative results for different strategies

---

## 🧪 Extending the Project

To add your own strategy:

1. Inherit from the abstract `Strategy` class in `strategies.py`.
2. Implement the `generate_signals()` method with your custom logic.
3. Add your strategy to the simulation setup in `main.py`.

---

## 📌 Requirements

See `requirements.txt` for full list, but major dependencies include:

* `pandas`
* `numpy`
* `matplotlib`
* `jupyter`

Install them all via:

```bash
pip install -r requirements.txt
```

---

## 📄 License

This project is for educational use only and part of the FINM 32500 coursework.

---