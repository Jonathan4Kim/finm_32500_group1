## Assignment 11 – ML Forecasting & Trading Signals

Implements an end-to-end machine learning workflow for short-term price direction forecasting:

- **Data ingestion** (`data_loader.py`) – loads OHLCV data, tickers, feature and model configs.
- **Feature engineering** (`feature_engineering.py`) – builds returns, SMAs, RSI, MACD, lagged features, and classification labels.
- **Model training** (`train_model.py`) – trains Logistic Regression, Random Forest, and optional XGBoost models with cross-validation and evaluation metrics.
- **Signal generation** (`signal_generator.py`) – converts predictions/probabilities into trading signals.
- **Backtesting** (`backtesting.py`) – simulates a long-only strategy versus buy-and-hold to produce performance metrics and equity curves.
- **Reporting** (`reporting.py`) – orchestrates the whole pipeline and saves artifacts to `reports/`.

### Environment

```
pip install pandas scikit-learn xgboost
```

(`xgboost` is optional; if unavailable the pipeline falls back to Logistic Regression and Random Forest.)

### Running the Pipeline

```
cd Assignment11
python reporting.py
```

The script performs:

1. Load CSV data/configs from `data/`.
2. Generate technical indicators, lagged returns, and labels (dropping rows with insufficient history).
3. Temporal train/test split (70/30 by distinct dates).
4. Train/evaluate the configured models with 5-fold cross-validation on the training window.
5. Generate holdout predictions, convert to signals, and backtest using a fixed notional position size per trade.
6. Store outputs in `Assignment11/reports/run_<timestamp>/`:
   - `signals.csv` – holdout rows with predictions, probabilities, signals, and realized returns.
   - `equity_curve.csv` – daily strategy vs. buy-and-hold equity.
   - `metrics.csv` – strategy KPIs (return, drawdown, win rate, trade count).
   - `models.json` – evaluation metrics for every trained model.

The console prints the best model statistics plus strategy performance.

### Files to Know

| File | Description |
|------|-------------|
| `data_loader.py` | Central loader for OHLCV/ticker data plus JSON configs |
| `feature_engineering.py` | Builds feature matrix and `direction` label |
| `train_model.py` | ModelTrainer class with temporal split + evaluations |
| `signal_generator.py` | Converts predictions to deterministic trading signals |
| `backtesting.py` | Backtester class + CSV export helper |
| `reporting.py` | Entry point producing the full assignment report |

### Notes

- Feature selection is governed by `data/features_config.json`.
- Model hyperparameters come from `data/model_params.json`.
- Adjust thresholds in `signal_generator.generate_signals` for different risk preferences.
