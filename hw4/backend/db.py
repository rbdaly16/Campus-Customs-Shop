"""SQLite connection helper shared by the API routes."""

import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"


def get_db(readonly: bool = True) -> sqlite3.Connection:
    # Read-only by default so catalogue routes can never modify shop data by accident.
    mode = "ro" if readonly else "rw"
    conn = sqlite3.connect(f"file:{DB_PATH}?mode={mode}", uri=True)
    conn.row_factory = sqlite3.Row
    return conn
