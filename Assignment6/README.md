# FINM 32500 – Assignment 6  
**Design Patterns in Financial Software Architecture**

## Overview
This assignment delivers a modular Python platform that simulates a financial analytics and trading workflow. The implementation highlights how classic object-oriented design patterns (creational, structural, and behavioral) support clean separation of concerns across data ingestion, portfolio modeling, strategy execution, analytics, and reporting.

## Key Learning Objectives
- Apply creational patterns (Factory, Singleton, Builder) to orchestrate configuration, instrument creation, and portfolio assembly.
- Use structural patterns (Decorator, Adapter, Composite) to extend analytics, normalize external data, and model nested portfolio hierarchies.
- Implement behavioral patterns (Strategy, Observer, Command) to encapsulate trading logic, event notification, and undoable trade execution.
- Evaluate design tradeoffs that balance extensibility, maintainability, and runtime complexity in a finance-focused codebase.

## Project Layout
- `Assignment6/main.py` – Entry point that wires together configuration, data ingestion, strategies, analytics, and reporting.
- `Assignment6/models.py` – Instrument classes, analytics decorators, and portfolio composite components.
- `Assignment6/data_loader.py` – Adapters that transform external Bloomberg and Yahoo Finance data into unified market data points.
- `Assignment6/patterns/` – Implementations of Factory, Builder, Singleton, Strategy, Observer, Command, and supporting abstractions.
- `Assignment6/analytics.py` – Financial metrics (volatility, beta, drawdown) used by decorators.
- `Assignment6/engine.py` – Trading engine that coordinates strategy evaluation and signal publication.
- `Assignment6/reporting.py` – Observer-based logging and alerting utilities.
- `Assignment6/tests/` – Place unit tests validating each pattern and integration flow.
- `Assignment6/design_report.md` – Written discussion covering rationale, tradeoffs, and reflections on pattern usage.

## Data and Configuration Sources
- `config.json` – Singleton configuration consumed by the entire system (logging, strategy parameters, etc.).
- `strategy_params.json` – Strategy-specific thresholds and lookback parameters.
- `portfolio_structure.json` – Nested portfolio specification parsed by the Builder and Composite patterns.
- `market_data.csv` & `instruments.csv` – Baseline datasets for instrument creation and market snapshots.
- `external_data_yahoo.json` & `external_data_bloomberg.xml` – Mock external feeds adapted into a common internal schema.

## Getting Started
1. Ensure Python 3.10+ is available (the code relies on dataclasses, typing features, and pathlib from the standard library).
2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies if additional packages were introduced for the assignment (otherwise, the standard library suffices):
   ```bash
   pip install -r requirements.txt
   ```

## Running the Simulation
Execute the orchestrator to load configuration, ingest data, run strategies, and emit reports:
```bash
python -m Assignment6.main
```
The console output will demonstrate instrument creation via the Factory, portfolio assembly via the Builder and Composite patterns, decorated analytics, strategy signal generation, observer notifications, and command-based trade lifecycle handling.

## Suggested Validation
- **Unit tests:** Add or extend tests in `Assignment6/tests/` and run with `pytest Assignment6/tests`.
- **Manual checks:** Experiment with `strategy_params.json` or `portfolio_structure.json` to observe how patterns support configuration-driven behavior without code changes.
- **Decorator stacking:** Wrap instruments with volatility, beta, and drawdown decorators to confirm layered analytics.

## Deliverables Checklist
- Code implementing each required pattern and demonstrating its role.
- `design_report.md` summarizing architecture decisions and tradeoffs.
- Updated README (this file) containing setup, execution, and module descriptions.

## Support and Extensions
- Extend the strategy layer with additional behavioral patterns (e.g., Template Method for multi-step strategies).
- Integrate new adapters for alternate data vendors by following the adapter interface in `data_loader.py`.
- Enhance command history with persistence or auditing hooks to simulate production trading controls.
