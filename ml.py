"""Machine learning utilities for training and prediction."""

from __future__ import annotations

import pickle
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, mean_absolute_error, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from backend.config import DATASET_PATH, MODEL_PATH, ENCODER_PATH, MODEL_DIR

try:
    from xgboost import XGBClassifier  # type: ignore

    XGBOOST_AVAILABLE = True
except Exception:
    XGBOOST_AVAILABLE = False


FEATURE_COLUMNS = [
    "Airline",
    "Airport",
    "Weather_Condition",
    "Departure_Hour",
    "Arrival_Hour",
    "Flight_Distance_KM",
    "Day_Of_Week",
]


@dataclass
class ModelBundle:
    classifier_name: str
    classifier_pipeline: Pipeline
    regression_pipeline: Pipeline
    metrics: dict


def _load_dataset() -> pd.DataFrame:
    """Load dataset and create modeled columns."""
    df = pd.read_csv(DATASET_PATH)
    df["Delay_Status"] = (df["Delay_Minutes"] > 15).astype(int)
    return df


def _build_preprocessor(categorical_cols: list[str], numeric_cols: list[str]) -> ColumnTransformer:
    """Create preprocessing pipeline for mixed features."""
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("cat", categorical_pipeline, categorical_cols),
            ("num", numeric_pipeline, numeric_cols),
        ]
    )


def train_models() -> ModelBundle:
    """Train classifier and regressor and save model artifacts."""
    df = _load_dataset()
    X = df[FEATURE_COLUMNS]
    y_cls = df["Delay_Status"]
    y_reg = df["Delay_Minutes"]

    X_train, X_test, y_train_cls, y_test_cls, y_train_reg, y_test_reg = train_test_split(
        X,
        y_cls,
        y_reg,
        test_size=0.2,
        random_state=42,
        stratify=y_cls,
    )

    categorical_cols = ["Airline", "Airport", "Weather_Condition"]
    numeric_cols = ["Departure_Hour", "Arrival_Hour", "Flight_Distance_KM", "Day_Of_Week"]
    preprocessor = _build_preprocessor(categorical_cols, numeric_cols)

    candidate_models = {
        "RandomForest": RandomForestClassifier(n_estimators=200, random_state=42),
    }
    if XGBOOST_AVAILABLE:
        candidate_models["XGBoost"] = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
        )

    best_name = ""
    best_pipeline = None
    best_f1 = -1.0
    model_scores = {}

    for name, model in candidate_models.items():
        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", model),
            ]
        )
        pipeline.fit(X_train, y_train_cls)
        preds = pipeline.predict(X_test)
        f1 = f1_score(y_test_cls, preds)
        acc = accuracy_score(y_test_cls, preds)
        model_scores[name] = {"f1": round(float(f1), 4), "accuracy": round(float(acc), 4)}
        if f1 > best_f1:
            best_f1 = f1
            best_name = name
            best_pipeline = pipeline

    regression_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", LinearRegression()),
        ]
    )
    regression_pipeline.fit(X_train, y_train_reg)
    reg_preds = regression_pipeline.predict(X_test)
    mae = mean_absolute_error(y_test_reg, reg_preds)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    bundle = {
        "classifier_name": best_name,
        "classifier_pipeline": best_pipeline,
        "regression_pipeline": regression_pipeline,
        "metrics": {
            "classification": model_scores,
            "best_model": best_name,
            "regression_mae": round(float(mae), 4),
            "total_rows": int(len(df)),
        },
    }

    with open(MODEL_PATH, "wb") as model_file:
        pickle.dump(bundle, model_file)
    with open(ENCODER_PATH, "wb") as metadata_file:
        pickle.dump({"feature_columns": FEATURE_COLUMNS}, metadata_file)

    return ModelBundle(**bundle)


def load_or_train_models() -> ModelBundle:
    """Load existing model or train a new one."""
    if not MODEL_PATH.exists():
        return train_models()
    with open(MODEL_PATH, "rb") as model_file:
        bundle = pickle.load(model_file)
    return ModelBundle(**bundle)


def predict_delay(bundle: ModelBundle, payload: dict) -> dict:
    """Predict delay class and delay minutes for one flight payload."""
    data = pd.DataFrame([payload], columns=FEATURE_COLUMNS)

    classifier = bundle.classifier_pipeline
    regressor = bundle.regression_pipeline

    class_pred = int(classifier.predict(data)[0])
    class_prob = float(classifier.predict_proba(data)[0][1]) if hasattr(classifier, "predict_proba") else 0.5
    reg_minutes = float(regressor.predict(data)[0])
    reg_minutes = max(0.0, reg_minutes)

    status = "Likely Delayed" if class_pred == 1 else "Likely On-Time"
    confidence = class_prob if class_pred == 1 else (1.0 - class_prob)

    return {
        "delay_status": status,
        "delay_probability": round(class_prob * 100, 2),
        "confidence_score": round(confidence * 100, 2),
        "predicted_delay_minutes": round(reg_minutes, 2),
    }
