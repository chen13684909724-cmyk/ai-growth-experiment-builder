from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "experiments.db"


def initialize_db(db_path: Path = DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS experiment_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                experiment_name TEXT NOT NULL,
                hypothesis TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )


def save_run(experiment_name: str, hypothesis: str, result: dict, db_path: Path = DB_PATH) -> None:
    initialize_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO experiment_runs (created_at, experiment_name, hypothesis, result_json) VALUES (?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), experiment_name, hypothesis, json.dumps(result)),
        )


def list_runs(db_path: Path = DB_PATH) -> list[dict]:
    initialize_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, created_at, experiment_name, hypothesis, result_json FROM experiment_runs ORDER BY id DESC"
        ).fetchall()
    return [
        {"id": r[0], "created_at": r[1], "experiment_name": r[2], "hypothesis": r[3], **json.loads(r[4])}
        for r in rows
    ]
