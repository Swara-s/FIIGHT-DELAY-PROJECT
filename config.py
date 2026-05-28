"""Central configuration for the Flask application."""

from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "dataset" / "flights_data.csv"
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "flight_delay_model.pkl"
ENCODER_PATH = MODEL_DIR / "feature_bundle.pkl"
DATABASE_PATH = BASE_DIR / "database" / "flight_delay.db"


class Config:
    """Default Flask config."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    DATABASE_URI = f"sqlite:///{DATABASE_PATH.as_posix()}"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
