try:
    from src.database.common import get_connection
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.common import get_connection


def clear_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM raw_countries")
    cursor.execute("DELETE FROM bronze_countries")
    cursor.execute("DELETE FROM silver_countries")
    cursor.execute("DELETE FROM raw_persons")
    cursor.execute("DELETE FROM bronze_persons")
    cursor.execute("DELETE FROM silver_persons")
    cursor.execute("DELETE FROM raw_weapons")
    cursor.execute("DELETE FROM bronze_weapons")
    cursor.execute("DELETE FROM silver_weapons")
    cursor.execute("DELETE FROM retry_countries")
    cursor.execute("DELETE FROM retry_persons")
    cursor.execute("DELETE FROM retry_weapons")
    cursor.execute("DELETE FROM country_html_cache_log")
    cursor.execute("DELETE FROM alliances")

    conn.commit()
    conn.close()
