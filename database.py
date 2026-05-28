"""Database helper functions for SQLite operations."""

import sqlite3
from contextlib import closing
from datetime import datetime

from backend.config import DATABASE_PATH


def get_connection():
    """Return an SQLite connection with dictionary-like rows."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables required by the project."""
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                flight_number TEXT NOT NULL,
                airline TEXT NOT NULL,
                airport TEXT NOT NULL,
                weather_condition TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                arrival_time TEXT NOT NULL,
                delay_probability REAL NOT NULL,
                predicted_delay_minutes REAL NOT NULL,
                delay_status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()


def now_iso():
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat()
