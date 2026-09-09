import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "users.db"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS users (card_uid TEXT PRIMARY KEY, name TEXT NOT NULL, registered INTEGER NOT NULL DEFAULT 1)")
    conn.commit()
    return conn


def lookup_card(uid):
    conn = _connect()
    try:
        row = conn.execute("SELECT card_uid, name, registered FROM users WHERE card_uid = ? AND registered = 1", (uid.upper(),)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def add_card(uid, name):
    conn = _connect()
    try:
        conn.execute("INSERT OR REPLACE INTO users(card_uid, name, registered) VALUES (?, ?, 1)", (uid.upper(), name))
        conn.commit()
    finally:
        conn.close()
