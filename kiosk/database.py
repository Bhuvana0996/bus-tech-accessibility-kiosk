import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "users.db"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "card_uid TEXT PRIMARY KEY, "
        "name TEXT NOT NULL, "
        "accessibility TEXT NOT NULL DEFAULT 'Not specified', "
        "registered INTEGER NOT NULL DEFAULT 1)"
    )

    # Upgrade an existing kiosk database created by an older version.
    columns = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "accessibility" not in columns:
        conn.execute(
            "ALTER TABLE users ADD COLUMN accessibility TEXT NOT NULL DEFAULT 'Not specified'"
        )
        conn.commit()

    return conn


def lookup_card(uid):
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT card_uid, name, accessibility, registered "
            "FROM users WHERE card_uid = ? AND registered = 1",
            (uid.upper(),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def add_card(uid, name, accessibility="Not specified"):
    conn = _connect()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO users(card_uid, name, accessibility, registered) "
            "VALUES (?, ?, ?, 1)",
            (uid.upper(), name, accessibility),
        )
        conn.commit()
    finally:
        conn.close()
