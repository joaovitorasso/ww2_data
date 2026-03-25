import json
import sqlite3

try:
    from src.database.common import get_connection, get_or_create_alliance_id, get_or_create_country_id
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.common import get_connection, get_or_create_alliance_id, get_or_create_country_id


def insert_raw_person(raw_payload: dict, section: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        id_alliance = get_or_create_alliance_id(cursor, section)
        basic = raw_payload.get("basic", {}) if isinstance(raw_payload, dict) else {}
        country_name = basic.get("country_name")
        country_link = basic.get("country_link")
        country_id = get_or_create_country_id(cursor, id_alliance, country_name, country_link)
        cursor.execute(
            """
            INSERT OR IGNORE INTO raw_persons (
                id_alliance, country_id, country_name, country_link, person_name, person_link, payload
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                id_alliance,
                country_id,
                country_name,
                country_link,
                basic.get("person_name"),
                basic.get("person_link"),
                json.dumps(raw_payload, ensure_ascii=False),
            ),
        )

        if cursor.lastrowid:
            raw_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                SELECT id FROM raw_persons
                WHERE id_alliance = ? AND country_name IS ? AND person_link IS ?
                ORDER BY id LIMIT 1
                """,
                (
                    id_alliance,
                    country_name,
                    basic.get("person_link"),
                ),
            )
            row = cursor.fetchone()
            raw_id = row[0] if row else None

        conn.commit()
        return raw_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_bronze_person(raw_id: int, parsed_data: dict, section: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        id_alliance = get_or_create_alliance_id(cursor, section)
        details = parsed_data.get("details") or {}
        basic = parsed_data.get("basic") or {}
        country_id = get_or_create_country_id(
            cursor,
            id_alliance,
            basic.get("country_name"),
            basic.get("country_link"),
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO bronze_persons (
                raw_id, country_id, id_alliance, country_name, country_link, person_name, person_link,
                given_name, surname, born, died, category, gender, img
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                raw_id,
                country_id,
                id_alliance,
                basic.get("country_name"),
                basic.get("country_link"),
                basic.get("person_name"),
                basic.get("person_link"),
                details.get("name"),
                details.get("surname"),
                details.get("born"),
                details.get("died"),
                details.get("category"),
                details.get("gender"),
                details.get("img"),
            ),
        )

        if cursor.lastrowid:
            bronze_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                SELECT id FROM bronze_persons
                WHERE raw_id = ?
                ORDER BY id LIMIT 1
                """,
                (raw_id,),
            )
            row = cursor.fetchone()
            bronze_id = row[0] if row else None

        conn.commit()
        return bronze_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _split_basic_person_name(person_name: str):
    if not person_name:
        return None, None
    text = str(person_name).strip()
    if not text:
        return None, None
    if "," in text:
        parts = [part.strip() for part in text.split(",", 1)]
        if len(parts) == 2:
            return parts[1] or None, parts[0] or None
    return text, None


def insert_silver_person(bronze_id: int, parsed_data: dict, section: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        id_alliance = get_or_create_alliance_id(cursor, section)
        cursor.execute("SELECT raw_id, country_id FROM bronze_persons WHERE id = ?", (bronze_id,))
        row = cursor.fetchone()
        raw_id = row[0] if row else None
        country_id = row[1] if row else None
        details = parsed_data.get("details") or {}
        basic = parsed_data.get("basic") or {}

        basic_person_name = (basic.get("person_name") or "").strip() or None
        given_name = (details.get("name") or "").strip() or None
        surname = (details.get("surname") or "").strip() or None
        if not given_name or not surname:
            fallback_given, fallback_surname = _split_basic_person_name(basic_person_name)
            given_name = given_name or fallback_given
            surname = surname or fallback_surname

        full_name = f"{given_name or ''} {surname or ''}".strip() or basic_person_name

        gender = details.get("gender")
        if gender is not None:
            gender = str(gender).strip() or None
            if gender:
                if gender.lower() == "male":
                    gender = "Male"
                elif gender.lower() == "female":
                    gender = "Female"

        cursor.execute(
            """
            INSERT OR IGNORE INTO silver_persons (
                bronze_id, raw_id, country_id, id_alliance, full_name, country_name, country_link, person_link,
                born, died, category, gender, img
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bronze_id,
                raw_id,
                country_id,
                id_alliance,
                full_name,
                basic.get("country_name"),
                basic.get("country_link"),
                basic.get("person_link"),
                details.get("born"),
                details.get("died"),
                details.get("category"),
                gender,
                details.get("img"),
            ),
        )

        if cursor.lastrowid:
            silver_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                SELECT id FROM silver_persons
                WHERE bronze_id = ?
                ORDER BY id LIMIT 1
                """,
                (bronze_id,),
            )
            row = cursor.fetchone()
            silver_id = row[0] if row else None

        conn.commit()
        return silver_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_silver_persons_by_alliance(alliance_name: str):
    conn = get_connection(row_factory=sqlite3.Row)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT sp.*
        FROM silver_persons sp
        JOIN alliances a ON sp.id_alliance = a.id_alliance
        WHERE a.alliance_name = ?
        ORDER BY sp.full_name
        """,
        (alliance_name,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

