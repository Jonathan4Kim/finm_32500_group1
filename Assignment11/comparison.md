## Model & Strategy Comparison

Outputs are generated automatically by `python reporting.py`. Summary interpretation guide:

1. **Model Metrics (`reports/run_*/models.json`)**
   - Compare `accuracy`, `precision`, `recall`, and cross-validation averages to decide which model generalizes best.
   - Inspect confusion matrices to understand false-positive vs. false-negative trade-offs.
   - Feature coefficients/importances can be introspected directly on the saved `best_pipeline`.

2. **Signal Quality (`reports/run_*/signals.csv`)**
   - Review probability scores to see confidence dispersion across tickers/dates.
   - Evaluate `next_return` alongside `signal` to confirm whether the classifier captured the correct direction.

3. **Backtest (`reports/run_*/equity_curve.csv`, `metrics.csv`)**
   - `metrics.csv` holds top-level KPIs: total return, max drawdown, win rate, trade count.
   - Plot `equity_curve.csv` to compare the strategy against buy-and-hold across the evaluation window.

### Discussion Pointers

- **Predictive Features:** Short-term returns (1/3/5d) plus RSI and MACD often explain most of the variance in `direction`. SMAs add smoothing for noisy tickers.
- **Model Selection:** Logistic Regression provides interpretable weights, while Random Forest handles non-linearities and typically improves recall. XGBoost (if installed) may edge out others on accuracy but increases training time.
- **Strategy Fit:** Signal thresholds (default 0.55) balance trade frequency vs. confidence. Raising the threshold improves win rate but lowers opportunity.
- **Limitations:** No transaction costs, borrowing limits, or slippage; the dataset is relatively small and lacks intraday granularity. Treat reported gains as indicative rather than actionable.
