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


def insert_raw_weapon(raw_payload: dict, section: str):
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
            INSERT OR IGNORE INTO raw_weapons (
                id_alliance, country_id, country_name, country_link, weapon_name, weapon_link, payload
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                id_alliance,
                country_id,
                country_name,
                country_link,
                basic.get("weapon_name"),
                basic.get("weapon_link"),
                json.dumps(raw_payload, ensure_ascii=False),
            ),
        )

        if cursor.lastrowid:
            raw_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                SELECT id FROM raw_weapons
                WHERE id_alliance = ? AND country_name IS ? AND weapon_link IS ?
                ORDER BY id LIMIT 1
                """,
                (
                    id_alliance,
                    country_name,
                    basic.get("weapon_link"),
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


def insert_bronze_weapon(raw_id: int, parsed_data: dict, section: str):
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
            INSERT OR IGNORE INTO bronze_weapons (
                raw_id, country_id, id_alliance, country_name, country_link, weapon_name, weapon_link,
                origin_country, weapon_type, caliber, capacity, length, barrel_length,
                weight, range_value, muzzle_velocity, img
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                raw_id,
                country_id,
                id_alliance,
                basic.get("country_name"),
                basic.get("country_link"),
                basic.get("weapon_name"),
                basic.get("weapon_link"),
                details.get("country"),
                details.get("type"),
                details.get("caliber"),
                details.get("capacity"),
                details.get("lenght"),
                details.get("barrel_lenght"),
                details.get("weight"),
                details.get("range"),
                details.get("muzzle_velocity"),
                details.get("img"),
            ),
        )

        if cursor.lastrowid:
            bronze_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                SELECT id FROM bronze_weapons
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


def insert_silver_weapon(bronze_id: int, parsed_data: dict, section: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        id_alliance = get_or_create_alliance_id(cursor, section)
        cursor.execute("SELECT raw_id, country_id FROM bronze_weapons WHERE id = ?", (bronze_id,))
        row = cursor.fetchone()
        raw_id = row[0] if row else None
        country_id = row[1] if row else None
        details = parsed_data.get("details") or {}
        basic = parsed_data.get("basic") or {}

        basic_weapon_name = (basic.get("weapon_name") or "").strip() or None
        full_name = (details.get("name") or "").strip() or basic_weapon_name
        origin_country = (details.get("country") or "").strip() or None
        weapon_type = (details.get("type") or "").strip() or None
        caliber = (details.get("caliber") or "").strip() or None
        capacity = (details.get("capacity") or "").strip() or None
        length = (details.get("lenght") or "").strip() or None
        barrel_length = (details.get("barrel_lenght") or "").strip() or None
        weight = (details.get("weight") or "").strip() or None
        range_value = (details.get("range") or "").strip() or None
        muzzle_velocity = (details.get("muzzle_velocity") or "").strip() or None
        img = (details.get("img") or "").strip() or None

        cursor.execute(
            """
            INSERT OR IGNORE INTO silver_weapons (
                bronze_id, raw_id, country_id, id_alliance, full_name, country_name, country_link, weapon_link,
                origin_country, weapon_type, caliber, capacity, length, barrel_length,
                weight, range_value, muzzle_velocity, img
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bronze_id,
                raw_id,
                country_id,
                id_alliance,
                full_name,
                basic.get("country_name"),
                basic.get("country_link"),
                basic.get("weapon_link"),
                origin_country,
                weapon_type,
                caliber,
                capacity,
                length,
                barrel_length,
                weight,
                range_value,
                muzzle_velocity,
                img,
            ),
        )

        if cursor.lastrowid:
            silver_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                SELECT id FROM silver_weapons
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

