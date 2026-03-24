import json
import sqlite3

try:
    from src.database.common import get_db_path, get_or_create_alliance_id, now_brasilia_str
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.common import get_db_path, get_or_create_alliance_id, now_brasilia_str


def insert_raw_country(raw_payload: dict, section: str):
    conn = sqlite3.connect(get_db_path())
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
    conn = sqlite3.connect(get_db_path())
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
    conn = sqlite3.connect(get_db_path())
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


def refresh_gold_metrics(section: str):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        id_alliance = get_or_create_alliance_id(cursor, section)
        cursor.execute(
            """
            SELECT
                COUNT(1),
                SUM(military_deaths),
                SUM(civilian_deaths),
                SUM(civilian_holocaust_deaths),
                SUM(population)
            FROM silver_countries
            WHERE id_alliance = ?
            """,
            (id_alliance,),
        )
        row = cursor.fetchone()
        country_count, sum_military, sum_civilian, sum_holocaust, sum_population = row
        avg_population = None
        if country_count and country_count > 0 and sum_population is not None:
            avg_population = sum_population / country_count

        cursor.execute(
            """
            INSERT INTO gold_alliance_metrics (
                id_alliance, country_count, total_military_deaths, total_civilian_deaths,
                total_holocaust_deaths, total_population, average_population, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id_alliance) DO UPDATE SET
                country_count=excluded.country_count,
                total_military_deaths=excluded.total_military_deaths,
                total_civilian_deaths=excluded.total_civilian_deaths,
                total_holocaust_deaths=excluded.total_holocaust_deaths,
                total_population=excluded.total_population,
                average_population=excluded.average_population,
                updated_at=CURRENT_TIMESTAMP
            WHERE gold_alliance_metrics.country_count IS NOT excluded.country_count
               OR gold_alliance_metrics.total_military_deaths IS NOT excluded.total_military_deaths
               OR gold_alliance_metrics.total_civilian_deaths IS NOT excluded.total_civilian_deaths
               OR gold_alliance_metrics.total_holocaust_deaths IS NOT excluded.total_holocaust_deaths
               OR gold_alliance_metrics.total_population IS NOT excluded.total_population
               OR gold_alliance_metrics.average_population IS NOT excluded.average_population
            """,
            (
                id_alliance,
                country_count or 0,
                sum_military or 0,
                sum_civilian or 0,
                sum_holocaust or 0,
                sum_population or 0,
                avg_population,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_silver_countries_by_alliance(alliance_name: str):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
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


def get_gold_metrics_by_alliance(alliance_name: str):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT gm.*
        FROM gold_alliance_metrics gm
        JOIN alliances a ON gm.id_alliance = a.id_alliance
        WHERE a.alliance_name = ?
        """,
        (alliance_name,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def insert_country_html_cache_log(total: int, cached: int, fetched: int, errors: int) -> None:
    conn = sqlite3.connect(get_db_path())
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
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT data, total, cached, fetched, errors FROM country_html_cache_log ORDER BY rowid DESC"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
