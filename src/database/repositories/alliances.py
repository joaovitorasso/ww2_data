import sqlite3

try:
    from src.database.common import get_connection
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.common import get_connection


def get_all_alliances():
    conn = get_connection(row_factory=sqlite3.Row)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alliances ORDER BY alliance_name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
