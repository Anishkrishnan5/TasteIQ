import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tasteiq.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spoonacular_id INTEGER,
        payload TEXT,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()