from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from backtesting import Backtester, save_backtest_outputs
from data_loader import DataLoader
from feature_engineering import FeatureEngineer
from signal_generator import generate_signals
from train_model import ModelTrainer


# Keep everything relative to the assignment directory to simplify execution from any path.
ASSIGNMENT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ASSIGNMENT_ROOT / "reports"


def _format_pct(value: float) -> str:
    """Convert a decimal value to percentage text with two decimals."""
    return f"{value * 100:.2f}%"


def run_pipeline() -> dict:
    """
    Execute the full workflow: load data, engineer features, train models, produce signals, and backtest.
    """
    # Load raw market data, tickers, and configuration files.
    loader = DataLoader()
    loaded = loader.load_all()

    # Create the full feature matrix/labels according to the config.
    engineer = FeatureEngineer(
        features=loaded.features_config["features"],
        label=loaded.features_config["label"],
    )
    feature_df = engineer.transform(loaded.market_data)

    # Train all configured models and evaluate them on a temporal holdout.
    trainer = ModelTrainer(
        features=loaded.features_config["features"],
        label=loaded.features_config["label"],
        model_params=loaded.model_params,
    )
    split = trainer.temporal_train_test_split(feature_df)
    model_results = trainer.train_and_evaluate(split.train_df, split.test_df)

    # Turn best-model predictions into tradable signals.
    signals = generate_signals(
        model_results["test_df"],
        model_results["best_predictions"],
        model_results["best_probabilities"],
    )

    # Simulate the trading strategy and produce KPIs plus equity curve.
    backtester = Backtester()
    bt_result = backtester.run(signals)

    # Persist run artifacts to a timestamped directory for later review.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = REPORTS_DIR / f"run_{timestamp}"
    save_backtest_outputs(bt_result, run_dir)
    with open(run_dir / "models.json", "w", encoding="utf-8") as f:
        json.dump(model_results["models"], f, indent=2)

    return {
        "loaded": loaded,
        "feature_df": feature_df,
        "split": split,
        "model_results": model_results,
        "signals": signals,
        "backtest": bt_result,
        "run_dir": run_dir,
    }


def main() -> None:
    """Entry point for CLI execution that prints headline metrics."""
    # Execute the full pipeline and capture references to the outputs.
    outputs = run_pipeline()
    model_results = outputs["model_results"]
    bt_metrics = outputs["backtest"].metrics

    # Pull the stats for the winning model.
    best_name = model_results["best_model"]
    best_stats = model_results["models"][best_name]

    # Display human-friendly modeling metrics.
    print("=== Assignment 11 Report ===")
    print(f"Best model: {best_name}")
    print(
        f"Holdout Accuracy: {_format_pct(best_stats['accuracy'])} | "
        f"Precision: {_format_pct(best_stats['precision'])} | "
        f"Recall: {_format_pct(best_stats['recall'])}"
    )
    print(f"Cross-validated accuracy mean: {_format_pct(best_stats['cv_accuracy_mean'])}")

    # Show backtest KPIs, formatting percentages where applicable.
    print("\n=== Backtest Metrics ===")
    for key, value in bt_metrics.items():
        if "return" in key or "drawdown" in key or "win_rate" in key:
            print(f"{key}: {_format_pct(value)}")
        else:
            print(f"{key}: {value}")

    # Indicate where the detailed CSV/JSON artifacts are stored.
    print("\nReports saved to:", outputs["run_dir"])


if __name__ == "__main__":
    main()
