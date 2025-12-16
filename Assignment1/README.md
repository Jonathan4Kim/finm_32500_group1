# Assignment 1 – CSV-Based Algorithmic Trading Backtester

This project is a market data simulation and trading strategy backtesting engine built for **FINM 32500**. It simulates trading strategies on generated market data and evaluates performance metrics like total return, Sharpe ratio, and max drawdown.

---

## 📁 Project Structure

```

Assignment1/
├── data_generator.py        # Generate simulated market data
├── data_loader.py           # Load market data into usable objects
├── engine.py                # Simulation engine and trade execution logic
├── main.py                  # Entry point with client code to run simulations
├── market_data.csv          # Sample market data (AAPL)
├── models.py                # Data models: Order, MarketDataPoint, etc.
├── performance.ipynb        # Strategy performance analysis + plots
├── README.md                # Project overview and usage guide
├── reporting.py             # Utility functions for performance reporting
├── strategies.py            # Strategy implementations (MAC, Momentum)
└── requirements.txt         # Python dependencies

````

---

## ⚙️ Setup Instructions

To run the simulation and test strategies, follow these steps:

### 1. Clone the Repository

```bash
git clone https://github.com/AdithSrinivasan/finm32500_excelfilter.git
cd finm32500_excelfilter/Assignment1
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

### 4. Run the Simulation

```bash
python main.py
```

---

## 🧠 Module Descriptions

| File                | Description                                                                                                                 |
| ------------------- |-----------------------------------------------------------------------------------------------------------------------------|
| `data_generator.py` | Generates synthetic market data and writes it to a CSV file based on specified distribution parameters.                     |
| `data_loader.py`    | Loads market data from a CSV and returns a list of `MarketDataPoint` objects.                                               |
| `engine.py`         | Core engine that manages simulation flow, executes trades, logs P\&L, and portfilio positions.                              |
| `main.py`           | Main client script to create simulations, configure strategies, and run backtests.                                          |
| `market_data.csv`   | Example dataset for AAPL stock used in testing and demonstration.                                                           |
| `models.py`         | Contains class definitions for core objects such as `Order` and `MarketDataPoint`.                                          |
| `performance.ipynb` | Jupyter Notebook with analysis and plots of strategy performance: total return, Sharpe ratio, drawdowns, etc.               |
| `reporting.py`      | Reporting utility functions for performance metrics (e.g. Sharpe ratio, max drawdown).                                      |
| `strategies.py`     | Defines the abstract `Strategy` class and concrete implementations: MAC (moving average crossover) and Momentum strategies. |
| `requirements.txt`  | Lists all required Python packages for the project.                                                                         |

---

## 📊 Example Performance Analysis

Open the Jupyter Notebook to explore how strategies performed:

```bash
jupyter notebook performance.ipynb
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
# Homework 1: CSV-Based Algorithmic Trading Backtester

## Project Structure

- **data_generator.py** *(Given)*: Generates a `market_data.csv` file containing simulated market data.  
- **data_loader.py**: Loads data points from `market_data.csv` into a list of `MarketDataPoint` instances. The main function `load_data()` handles this.  
- **engine.py**: Uses `load_data` from `data_loader.py` along with `Order`, `OrderError`, and `ExecutionError` from `models.py` to run trading simulations.  
- **main.py**: Combines the `Strategy` and `MarketSimulation` classes to simulate trading using the Moving Average Crossover and Momentum strategies. Prints returns, Sharpe ratio, and maximum drawdown.  
- **market_data.csv**: Generated by `data_generator.py`. Contains 500+ data points with `timestamp`, `price`, and `symbol` attributes to be passed as `MarketDataPoint` instances in `data_loader.py`.  
- **models.py**: Contains key classes and unit tests:
  - `MarketDataPoint` (frozen class)
  - `Order`
  - `OrderError`
  - `ExecutionError`
  - `TestUpdate` (unit tests for order updates and frozen instances)  
- **performance.ipynb**: Analyzes strategy performance on market data, including equity curves, descriptive summaries, and analysis of specific periods.  
- **reporting.py**: Defines the `Reporting` class, which computes total return, periodic return, Sharpe ratio, and other metrics given an equity curve.  
- **requirements.txt**: Lists all required Python packages for project setup.  
- **strategies.py**: Defines the Moving Average Crossover (MAC) and Momentum strategies used in `engine.py` for trading simulations with `MarketDataPoint` instances.  
- **README.md**: This file.  



## Project Setup

This guide explains how to create and activate a Python virtual environment and install the dependencies listed in `requirements.txt`.

### Prerequisites
- Python 3.8+ installed on your system  
- `pip` (Python package manager)

---

### 1. Create a Virtual Environment

First, be sure to be using the correct directory, Assignment 1:

```bash
cd Assignment1
```

Run the following command in the root of the project directory:

```bash
python3 -m venv venv
````

This will create a folder named `venv` containing the virtual environment.

---

### 2. Activate the Virtual Environment

#### On macOS/Linux:

```bash
source venv/bin/activate
```

#### On Windows (PowerShell):

```powershell
.\venv\Scripts\Activate
```

When activated, your terminal prompt should show `(venv)` at the beginning.

---

### 3. Install Dependencies

With the virtual environment activated, run:

```bash
pip install -r requirements.txt
```

This will install all required packages.

---

### 4. Deactivate the Virtual Environment

When finished working, deactivate the environment with:

```bash
deactivate
```

---


### Notes

* Always activate the virtual environment before running scripts.
* If you add new dependencies, update `requirements.txt` with:

```bash
pip freeze > requirements.txt
```

## 2. Running the Project

To run the trading simulation, simply execute the `main.py` file:

```bash
python main.py
```

Test cases can be run using the `models.py` class:
```bash
python models.py 
```

