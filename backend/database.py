"""Koneksi dan inisialisasi SQLite (khusus development). Skema ada di schema.sql."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .criteria import CRITERIA

SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path=None) -> sqlite3.Connection:
    path = Path(path or config.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)  # FastAPI menjalankan handler sinkron di thread pool
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.executemany(
        "INSERT OR REPLACE INTO criterion (code, name, type, min_val, max_val) VALUES (?,?,?,?,?)",
        [(c["code"], c["name"], c["type"], c["min"], c["max"]) for c in CRITERIA],
    )
    conn.commit()
