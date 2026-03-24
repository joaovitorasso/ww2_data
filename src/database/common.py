import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None


def get_db_path() -> str:
    """Return SQLite path under project data folder."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    db_folder = os.path.join(project_root, "data")
    os.makedirs(db_folder, exist_ok=True)
    return os.path.join(db_folder, "ww2.db")


def now_brasilia_str() -> str:
    if ZoneInfo is not None:
        dt = datetime.now(ZoneInfo("America/Sao_Paulo"))
    else:  # pragma: no cover
        dt = datetime.now(timezone(timedelta(hours=-3)))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_or_create_alliance_id(cursor: sqlite3.Cursor, section: str) -> int:
    alliance_name = (section or "").strip()
    cursor.execute("SELECT id_alliance FROM alliances WHERE alliance_name = ?", (alliance_name,))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute("INSERT INTO alliances (alliance_name) VALUES (?)", (alliance_name,))
    return cursor.lastrowid


def get_or_create_country_id(
    cursor: sqlite3.Cursor,
    id_alliance: int,
    country_name: str | None,
    country_link: str | None,
) -> int | None:
    normalized_name = (country_name or "").strip() or None
    normalized_link = (country_link or "").strip() or None

    if not id_alliance:
        return None

    if normalized_link:
        cursor.execute(
            """
            SELECT id
            FROM raw_countries
            WHERE id_alliance = ? AND link = ?
            ORDER BY id
            LIMIT 1
            """,
            (id_alliance, normalized_link),
        )
        row = cursor.fetchone()
        if row:
            return row[0]

    if normalized_name:
        cursor.execute(
            """
            SELECT id
            FROM raw_countries
            WHERE id_alliance = ? AND country_name = ?
            ORDER BY id
            LIMIT 1
            """,
            (id_alliance, normalized_name),
        )
        row = cursor.fetchone()
        if row:
            return row[0]

    if not normalized_name and not normalized_link:
        return None

    payload = json.dumps(
        {
            "basic": {
                "name": normalized_name,
                "link": normalized_link,
            },
            "details": None,
        },
        ensure_ascii=False,
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO raw_countries (id_alliance, country_name, link, payload)
        VALUES (?, ?, ?, ?)
        """,
        (id_alliance, normalized_name, normalized_link, payload),
    )
    if cursor.lastrowid:
        return cursor.lastrowid

    if normalized_link:
        cursor.execute(
            """
            SELECT id
            FROM raw_countries
            WHERE id_alliance = ? AND link = ?
            ORDER BY id
            LIMIT 1
            """,
            (id_alliance, normalized_link),
        )
        row = cursor.fetchone()
        if row:
            return row[0]

    if normalized_name:
        cursor.execute(
            """
            SELECT id
            FROM raw_countries
            WHERE id_alliance = ? AND country_name = ?
            ORDER BY id
            LIMIT 1
            """,
            (id_alliance, normalized_name),
        )
        row = cursor.fetchone()
        if row:
            return row[0]

    return None
