# Assignment 5: Testing & CI in Financial Engineering

## Overview  
This assignment implements a backtesting engine for a simple trading strategy, along with a comprehensive **pytest-based test suite** covering strategy logic, broker behavior, engine loop, edge cases, and failure handling. Automated testing and coverage monitoring are enforced via **GitHub Actions**, which ensures that total code coverage remains **above 90%** for every push or pull request.

## Components

1. **Strategy**

   * A volatility break-out strategy that generates buy/sell signals based on an *x-day volatility window*.
   * Signals are returned as a `pandas.Series` aligned with the price data.

2. **Broker**

   * Manages `cash`, `position` (number of shares), and executes `buy` and `sell` operations.
   * Enforces rules: rejects invalid input (negative prices), raises on insufficient cash or shares.

3. **Backtester / Engine**

   * Takes a `Strategy`, `Broker`, and price series (typically a `pandas.Series` of closing prices).
   * On each time-step: reads the signal, executes trades via the broker, tracks equity = cash + position × price.

## Testing

We built a pytest suite that covers the following requirements:

### 1. Strategy logic

* Ensures the signal generation is correct for breakout logic (window, threshold behaviour).
* Verifies that the output is a `Series` matching the price index and contains valid signals.

### 2. Broker behaviour

* Tests that `buy` and `sell` update `cash` and `position` correctly.
* Tests that invalid inputs (negative price) raise a `ValueError`.
* Tests that insufficient cash for `buy`, or no shares for `sell`, raise a `ValueError`.

### 3. Engine loop & equity consistency

* Tests that after running the engine, the final equity equals the broker's `cash + position × last_price`.
* Verifies the engine executes trades according to the strategy signals and updates the broker accordingly.

### 4. Edge cases

We handle and test the following unusual data scenarios:

* **Empty price series** → Engine should raise a `ValueError` or handle gracefully.
* **Constant price series** → Strategy may generate no signals, engine still returns a valid equity series.
* **NaNs at the head of the series** → Engine should detect invalid / incomplete data and raise or clean appropriately.
* **Very short series** (e.g., length < window) → Engine / strategy should raise or handle the limitation.

### 5. Failure handling

* We include a test that mocks the broker to force a failure (e.g., broker `buy` raises `ValueError`).
* We assert that this exception propagates through the engine and is logged/raised as expected.

## How to run

From the project root:

```bash
# Install dependencies (pytest, pandas, numpy, etc.)
pip install -r requirements.txt

# Run pytest with coverage
coverage run -m pytest -q

# Then view the coverage summary
coverage report -m
```

You can also generate an HTML coverage report:

```bash
coverage html
# Open htmlcov/index.html in your browser
```

## Files and Structure

```
Assignment5/
├── backtester/
│   ├── __init__.py           # Package initializer
│   ├── broker.py             # Broker class (trade validation, position tracking)
│   ├── engine.py             # Backtester engine (main loop + equity tracking)
│   ├── price_loader.py       # Loads and validates price data
│   └── strategy.py           # Volatility breakout strategy implementation
│
├── tests/
│   ├── __init__.py           # Marks tests as a package
│   ├── conftest.py           # Shared pytest fixtures for broker, strategy, and prices
│   ├── test_broker.py        # Tests for Broker class and error handling
│   ├── test_engine.py        # Tests for Backtester (loop logic, equity, edge cases)
│   └── test_strategy.py      # Tests for strategy signal generation and validation
│
└── README.md                 # This file
```


## Coverage Summary
```
Name                         Stmts   Miss  Cover   Missing
----------------------------------------------------------
backtester\__init__.py           0      0   100%
backtester\broker.py            19      3    84%   15, 20, 24
backtester\engine.py            20      0   100%
backtester\price_loader.py      19      1    95%   35
backtester\strategy.py          21      1    95%   8
tests\__init__.py                0      0   100%
tests\conftest.py               12      0   100%
tests\test_broker.py             7      0   100%
tests\test_engine.py            79      0   100%
tests\test_strategy.py          37      0   100%
----------------------------------------------------------
TOTAL                          214      5    98%
```

✅ Overall Coverage: 98% — indicating full testing of all major components, with only minor untested branches in broker.py, price_loader.py, and strategy.py.
























