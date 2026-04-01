from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

from .config import DB_PATH
from .models import Apartment


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT,
            country TEXT,
            city TEXT,
            user_type TEXT,
            language TEXT,
            budget INTEGER,
            move_in TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS apartments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            city TEXT,
            country TEXT,
            rent REAL,
            deposit REAL,
            furnished INTEGER,
            utilities_included INTEGER,
            url TEXT,
            notes TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def load_profile() -> Dict[str, object]:
    init_db()
    conn = get_connection()
    row = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
    conn.close()
    if not row:
        return {}
    return dict(row)


def save_profile(profile: Dict[str, object]) -> None:
    init_db()
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO user_profile (id, name, country, city, user_type, language, budget, move_in)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            country=excluded.country,
            city=excluded.city,
            user_type=excluded.user_type,
            language=excluded.language,
            budget=excluded.budget,
            move_in=excluded.move_in
        """,
        (
            profile.get("name", ""),
            profile.get("country", ""),
            profile.get("city", ""),
            profile.get("user_type", ""),
            profile.get("language", ""),
            int(profile.get("budget", 0) or 0),
            profile.get("move_in", ""),
        ),
    )
    conn.commit()
    conn.close()


def save_apartment(apartment: Apartment) -> None:
    init_db()
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO apartments (title, city, country, rent, deposit, furnished, utilities_included, url, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            apartment.title,
            apartment.city,
            apartment.country,
            apartment.rent,
            apartment.deposit,
            int(apartment.furnished),
            int(apartment.utilities_included),
            apartment.url,
            apartment.notes,
        ),
    )
    conn.commit()
    conn.close()


def list_apartments() -> List[dict]:
    init_db()
    conn = get_connection()
    rows = conn.execute("SELECT * FROM apartments ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_apartment(apartment_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM apartments WHERE id = ?", (apartment_id,))
    conn.commit()
    conn.close()
