import json
import sqlite3

try:
    from src.database.common import get_db_path
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.common import get_db_path


def enqueue_retry_country(section: str, basic_payload: dict, error_message: str | None, raw_id: int | None = None):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        country_name = (basic_payload or {}).get("name")
        link = (basic_payload or {}).get("link")
        payload = json.dumps(basic_payload or {}, ensure_ascii=False)

        cursor.execute(
            """
            INSERT INTO retry_countries (raw_id, section, country_name, link, payload, last_error)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(section, link) DO UPDATE SET
                raw_id=COALESCE(excluded.raw_id, retry_countries.raw_id),
                country_name=excluded.country_name,
                payload=excluded.payload,
                last_error=excluded.last_error,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                raw_id,
                section,
                country_name,
                link,
                payload,
                str(error_message) if error_message is not None else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_retry_countries(limit: int | None = None):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM retry_countries ORDER BY id"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_retry_country_succeeded(retry_id: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM retry_countries WHERE id = ?", (retry_id,))
        conn.commit()
    finally:
        conn.close()


def mark_retry_country_failed(retry_id: int, error_message: str | None):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE retry_countries
            SET retry_count = retry_count + 1,
                last_error = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                str(error_message) if error_message is not None else None,
                retry_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def remove_retry_country_by_key(section: str, link: str | None):
    if not link:
        return
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM retry_countries WHERE section = ? AND link = ?", (section, link))
        conn.commit()
    finally:
        conn.close()


def remove_retry_country_by_raw_id(raw_id: int | None):
    if not raw_id:
        return
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM retry_countries WHERE raw_id = ?", (raw_id,))
        conn.commit()
    finally:
        conn.close()


def enqueue_retry_person(alliance: str, basic_payload: dict, error_message: str | None, raw_id: int | None = None):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        country_name = (basic_payload or {}).get("country_name")
        person_name = (basic_payload or {}).get("person_name")
        person_link = (basic_payload or {}).get("person_link") or (basic_payload or {}).get("link")
        payload = json.dumps(basic_payload or {}, ensure_ascii=False)
        country_id = None
        if raw_id:
            cursor.execute("SELECT country_id FROM raw_persons WHERE id = ?", (raw_id,))
            row = cursor.fetchone()
            country_id = row[0] if row else None

        cursor.execute(
            """
            INSERT INTO retry_persons (
                raw_id, country_id, alliance, country_name, person_name, person_link, payload, last_error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(alliance, person_link) DO UPDATE SET
                raw_id=COALESCE(excluded.raw_id, retry_persons.raw_id),
                country_id=COALESCE(excluded.country_id, retry_persons.country_id),
                country_name=excluded.country_name,
                person_name=excluded.person_name,
                payload=excluded.payload,
                last_error=excluded.last_error,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                raw_id,
                country_id,
                alliance,
                country_name,
                person_name,
                person_link,
                payload,
                str(error_message) if error_message is not None else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_retry_persons(limit: int | None = None):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM retry_persons ORDER BY id"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_retry_person_succeeded(retry_id: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM retry_persons WHERE id = ?", (retry_id,))
        conn.commit()
    finally:
        conn.close()


def mark_retry_person_failed(retry_id: int, error_message: str | None):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE retry_persons
            SET retry_count = retry_count + 1,
                last_error = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                str(error_message) if error_message is not None else None,
                retry_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def remove_retry_person_by_key(alliance: str, person_link: str | None):
    if not person_link:
        return
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM retry_persons WHERE alliance = ? AND person_link = ?", (alliance, person_link))
        conn.commit()
    finally:
        conn.close()


def remove_retry_person_by_raw_id(raw_id: int | None):
    if not raw_id:
        return
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM retry_persons WHERE raw_id = ?", (raw_id,))
        conn.commit()
    finally:
        conn.close()


def enqueue_retry_weapon(alliance: str, basic_payload: dict, error_message: str | None, raw_id: int | None = None):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        country_name = (basic_payload or {}).get("country_name")
        weapon_name = (basic_payload or {}).get("weapon_name")
        weapon_link = (basic_payload or {}).get("weapon_link") or (basic_payload or {}).get("link")
        payload = json.dumps(basic_payload or {}, ensure_ascii=False)
        country_id = None
        if raw_id:
            cursor.execute("SELECT country_id FROM raw_weapons WHERE id = ?", (raw_id,))
            row = cursor.fetchone()
            country_id = row[0] if row else None

        cursor.execute(
            """
            INSERT INTO retry_weapons (
                raw_id, country_id, alliance, country_name, weapon_name, weapon_link, payload, last_error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(alliance, weapon_link) DO UPDATE SET
                raw_id=COALESCE(excluded.raw_id, retry_weapons.raw_id),
                country_id=COALESCE(excluded.country_id, retry_weapons.country_id),
                country_name=excluded.country_name,
                weapon_name=excluded.weapon_name,
                payload=excluded.payload,
                last_error=excluded.last_error,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                raw_id,
                country_id,
                alliance,
                country_name,
                weapon_name,
                weapon_link,
                payload,
                str(error_message) if error_message is not None else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_retry_weapons(limit: int | None = None):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM retry_weapons ORDER BY id"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_retry_weapon_succeeded(retry_id: int):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM retry_weapons WHERE id = ?", (retry_id,))
        conn.commit()
    finally:
        conn.close()


def mark_retry_weapon_failed(retry_id: int, error_message: str | None):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE retry_weapons
            SET retry_count = retry_count + 1,
                last_error = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                str(error_message) if error_message is not None else None,
                retry_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def remove_retry_weapon_by_key(alliance: str, weapon_link: str | None):
    if not weapon_link:
        return
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM retry_weapons WHERE alliance = ? AND weapon_link = ?", (alliance, weapon_link))
        conn.commit()
    finally:
        conn.close()


def remove_retry_weapon_by_raw_id(raw_id: int | None):
    if not raw_id:
        return
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM retry_weapons WHERE raw_id = ?", (raw_id,))
        conn.commit()
    finally:
        conn.close()
