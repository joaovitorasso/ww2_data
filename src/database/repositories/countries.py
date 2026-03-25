import json
import sqlite3

try:
    from src.database.common import get_connection, get_or_create_alliance_id, now_brasilia_str
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.common import get_connection, get_or_create_alliance_id, now_brasilia_str


def insert_raw_country(raw_payload: dict, section: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        id_alliance = get_or_create_alliance_id(cursor, section)
        cursor.execute(
            """
            INSERT OR IGNORE INTO raw_countries (id_alliance, country_name, link, payload)
            VALUES (?, ?, ?, ?)
            """,
            (
                id_alliance,
                raw_payload.get("basic", {}).get("name"),
                raw_payload.get("basic", {}).get("link"),
                json.dumps(raw_payload, ensure_ascii=False),
            ),
        )

        if cursor.lastrowid:
            raw_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                SELECT id FROM raw_countries
                WHERE id_alliance = ? AND country_name = ? AND link IS ?
                ORDER BY id LIMIT 1
                """,
                (
                    id_alliance,
                    raw_payload.get("basic", {}).get("name"),
                    raw_payload.get("basic", {}).get("link"),
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


def insert_bronze_country(raw_id: int, parsed_data: dict, section: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        id_alliance = get_or_create_alliance_id(cursor, section)
        cursor.execute(
            """
            INSERT OR IGNORE INTO bronze_countries (
                raw_id, id_alliance, country_name, link, full_name, military_deaths,
                civilian_deaths, civilian_holocaust_deaths, total_deaths, population, entry_date, flag
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                raw_id,
                id_alliance,
                parsed_data["basic"]["name"],
                parsed_data["basic"]["link"],
                parsed_data["details"].get("full_name"),
                parsed_data["details"].get("millitary_deaths"),
                parsed_data["details"].get("civillian_deaths"),
                parsed_data["details"].get("civillian_holocaust_deaths"),
                parsed_data["details"].get("total_deaths"),
                parsed_data["details"].get("population"),
                parsed_data["details"].get("entry_date"),
                parsed_data["details"].get("flag"),
            ),
        )

        if cursor.lastrowid:
            bronze_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                SELECT id FROM bronze_countries
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


def insert_silver_country(bronze_id: int, parsed_data: dict, section: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        id_alliance = get_or_create_alliance_id(cursor, section)
        cursor.execute("SELECT raw_id FROM bronze_countries WHERE id = ?", (bronze_id,))
        row = cursor.fetchone()
        raw_id = row[0] if row else None

        full_name = parsed_data["details"].get("full_name") or parsed_data["basic"]["name"]
        military = parsed_data["details"].get("millitary_deaths")
        civilian = parsed_data["details"].get("civillian_deaths")
        total = parsed_data["details"].get("total_deaths")
        if total is None and military is not None and civilian is not None:
            total = (military or 0) + (civilian or 0)

        cursor.execute(
            """
            INSERT OR IGNORE INTO silver_countries (
                bronze_id, raw_id, id_alliance, country_name, link, full_name, military_deaths,
                civilian_deaths, civilian_holocaust_deaths, total_deaths, population, entry_date, flag
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bronze_id,
                raw_id,
                id_alliance,
                parsed_data["basic"]["name"],
                parsed_data["basic"]["link"],
                full_name,
                military,
                civilian,
                parsed_data["details"].get("civillian_holocaust_deaths"),
                total,
                parsed_data["details"].get("population"),
                parsed_data["details"].get("entry_date"),
                parsed_data["details"].get("flag"),
            ),
        )

        if cursor.lastrowid:
            silver_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                SELECT id FROM silver_countries
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


def get_silver_countries_by_alliance(alliance_name: str):
    conn = get_connection(row_factory=sqlite3.Row)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT sc.*
        FROM silver_countries sc
        JOIN alliances a ON sc.id_alliance = a.id_alliance
        WHERE a.alliance_name = ?
        ORDER BY sc.country_name
        """,
        (alliance_name,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def insert_country_html_cache_log(total: int, cached: int, fetched: int, errors: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        now_str = now_brasilia_str()
        cursor.execute(
            """
            INSERT INTO country_html_cache_log (data, total, cached, fetched, errors)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                now_str,
                int(total or 0),
                int(cached or 0),
                int(fetched or 0),
                int(errors or 0),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_country_html_cache_logs(limit: int | None = None):
    conn = get_connection(row_factory=sqlite3.Row)
    cursor = conn.cursor()
    query = "SELECT id, data, total, cached, fetched, errors FROM country_html_cache_log ORDER BY id DESC"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
