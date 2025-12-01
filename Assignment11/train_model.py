from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


try:
    from xgboost import XGBClassifier  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    XGBClassifier = None


@dataclass
class TrainTestSplit:
    train_df: pd.DataFrame
    test_df: pd.DataFrame


class ModelTrainer:
    def __init__(self, features: List[str], label: str, model_params: Dict) -> None:
        # Store references to the feature columns, label name, and model configuration.
        self.features = features
        self.label = label
        self.model_params = model_params

    def temporal_train_test_split(self, df: pd.DataFrame, train_ratio: float = 0.7) -> TrainTestSplit:
        """
        
        Preserve time ordering by splitting on sorted unique dates.

        Args:
            df (pd.DataFrame): dataframe to be split
            train_ratio (float, optional): train-test split we want to split the 
            dataframe by. Defaults to 0.7.

        Raises:
            ValueError: If we don't have enough data for temporal splitting

        Returns:
            TrainTestSplit: Train Test Split to be utilized
        """
        # Determine the chronological split point.
        unique_dates = np.sort(df["date"].unique())
        if len(unique_dates) < 5:
            raise ValueError("Not enough unique dates to perform temporal split.")
        split_idx = max(1, int(len(unique_dates) * train_ratio))
        
        # Assign dates to train/test windows.
        train_dates = unique_dates[:split_idx]
        test_dates = unique_dates[split_idx:]
        
        # Subset the dataframe for each window.
        train_df = df[df["date"].isin(train_dates)].copy()
        test_df = df[df["date"].isin(test_dates)].copy()
        return TrainTestSplit(train_df=train_df, test_df=test_df)

    def _build_models(self) -> Dict[str, object]:
        """
        
        Instantiate each estimator requested in model_params.

        Returns:
            Dict[str, object]: dictionary of model name to 
            actual model, stored in dictionary
        """
        models: Dict[str, object] = {}
        if "LogisticRegression" in self.model_params:
            models["LogisticRegression"] = LogisticRegression(
                **self.model_params["LogisticRegression"], solver="lbfgs"
            )
        if "RandomForestClassifier" in self.model_params:
            models["RandomForestClassifier"] = RandomForestClassifier(
                **self.model_params["RandomForestClassifier"], random_state=42
            )
        if XGBClassifier and "XGBClassifier" in self.model_params:
            models["XGBClassifier"] = XGBClassifier(
                **self.model_params["XGBClassifier"],
                objective="binary:logistic",
                eval_metric="logloss",
            )
        return models

    def _build_pipeline(self, estimator: object) -> Pipeline:
        """
        Wrap an estimator with preprocessing steps shared across models.

        Args:
            estimator (object): estimator to be utilized

        Returns:
            Pipeline: Pipeline with relevant steps
        """
        return Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("estimator", estimator),
            ]
        )

    def train_and_evaluate(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> Dict:
        """
        
        Fit every model, capture cross-validation metrics, and pick the best performer.

        Args:
            train_df (pd.DataFrame): train dataframe
            test_df (pd.DataFrame): test dataframe

        Raises:
            ValueError: If there's no models that are available to train

        Returns:
            Dict: dictionary of models, best model, results, etc, by key.
        """
        # Extract feature/label matrices.
        X_train = train_df[self.features]
        y_train = train_df[self.label]
        X_test = test_df[self.features]
        y_test = test_df[self.label]

        # Build the estimators described in model_params.
        models = self._build_models()
        if not models:
            raise ValueError("No models available to train. Check model_params.json.")

        # Reuse a stratified CV splitter for consistent folds.
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

        results = {}
        best_model_name: Optional[str] = None
        best_accuracy = -np.inf
        best_pipeline: Optional[Pipeline] = None
        best_predictions = None
        best_probabilities = None

        for name, estimator in models.items():
            # Each estimator gets its own preprocessing pipeline.
            pipeline = self._build_pipeline(estimator)
            # Cross-validated accuracy on the training set.
            cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="accuracy")
            pipeline.fit(X_train, y_train)
            preds = pipeline.predict(X_test)
            accuracy = accuracy_score(y_test, preds)
            # Not every estimator exposes predict_proba (e.g., SVM), so guard it.
            probas = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline.named_steps["estimator"], "predict_proba") else None

            results[name] = {
                "cv_accuracy_mean": float(np.mean(cv_scores)),
                "cv_accuracy_std": float(np.std(cv_scores)),
                "accuracy": float(accuracy),
                "precision": float(precision_score(y_test, preds, zero_division=0)),
                "recall": float(recall_score(y_test, preds, zero_division=0)),
                "classification_report": classification_report(y_test, preds, zero_division=0, output_dict=True),
                "confusion_matrix": confusion_matrix(y_test, preds).tolist(),
            }

            if accuracy > best_accuracy:
                # Track the best-performing model for downstream signal generation.
                best_accuracy = accuracy
                best_model_name = name
                best_pipeline = pipeline
                best_predictions = preds
                best_probabilities = probas

        return {
            "models": results,
            "best_model": best_model_name,
            "best_pipeline": best_pipeline,
            "best_predictions": best_predictions,
            "best_probabilities": best_probabilities,
            "X_test": X_test,
            "y_test": y_test,
            "test_df": test_df,
        }


__all__ = ["ModelTrainer", "TrainTestSplit"]
