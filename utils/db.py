import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "journal.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def ensure_columns(conn, table_name, columns):
    existing_columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})")}
    for column_name, column_def in columns.items():
        if column_name not in existing_columns:
            conn.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
            )


def init_db():
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_new INTEGER DEFAULT 1,
                seen_tour INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(
            conn,
            "users",
            {
                "seen_tour": "INTEGER DEFAULT 0",
            },
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
            """
        )
        ensure_columns(
            conn,
            "journal_entries",
            {
                "user_id": "INTEGER",
                "entry_date": "TEXT NOT NULL DEFAULT ''",
                "journal_text": "TEXT NOT NULL DEFAULT ''",
                "source_type": "TEXT DEFAULT 'text'",
                "input_language": "TEXT DEFAULT 'en-US'",
                "sentiment": "TEXT NOT NULL DEFAULT 'Neutral'",
                "sentiment_score": "REAL DEFAULT 0",
                "emotion": "TEXT NOT NULL DEFAULT 'Neutral'",
                "emotion_confidence": "REAL DEFAULT 0",
                "emotion_scores": "TEXT DEFAULT '{}'",
                "themes": "TEXT DEFAULT '[]'",
                "energy_level": "TEXT DEFAULT 'Moderate'",
                "stress_index": "INTEGER DEFAULT 50",
                "recommendation": "TEXT DEFAULT ''",
                "forecast": "TEXT DEFAULT ''",
                "created_at": "TEXT DEFAULT ''",
            },
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mood_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                entry_date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                mood_key TEXT NOT NULL,
                mood_label TEXT NOT NULL,
                color_hex TEXT NOT NULL,
                mood_score INTEGER NOT NULL,
                note TEXT DEFAULT '',
                journal_entry_id INTEGER,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sleep_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sleep_date TEXT NOT NULL,
                bedtime TEXT NOT NULL,
                wake_time TEXT NOT NULL,
                duration_hours REAL NOT NULL,
                quality_rating INTEGER NOT NULL,
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                habit_key TEXT NOT NULL,
                habit_label TEXT NOT NULL,
                status TEXT NOT NULL,
                points_awarded INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reward_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                points INTEGER NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS challenge_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                challenge_key TEXT NOT NULL,
                challenge_title TEXT NOT NULL,
                coins_awarded INTEGER NOT NULL,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                code TEXT NOT NULL,
                points_cost INTEGER NOT NULL,
                partner_name TEXT NOT NULL,
                status TEXT NOT NULL,
                redemption_type TEXT NOT NULL,
                details TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.commit()
    finally:
        conn.close()
