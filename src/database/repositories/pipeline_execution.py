import sqlite3

try:
    from src.database.common import get_connection, now_brasilia_str
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.common import get_connection, now_brasilia_str


def start_pipeline_execution(pipeline_type: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        normalized_pipeline_type = (pipeline_type or "").strip() or "unknown"
        now_str = now_brasilia_str()

        cursor.execute(
            """
            UPDATE pipeline_execution_log
            SET status = 'aborted',
                finished_at = COALESCE(finished_at, ?)
            WHERE status = 'running'
            """,
            (now_str,),
        )

        cursor.execute(
            """
            INSERT INTO pipeline_execution_log (pipeline_type, started_at, status)
            VALUES (?, ?, 'running')
            """,
            (normalized_pipeline_type, now_str),
        )
        execution_id = cursor.lastrowid

        cursor.execute(
            """
            UPDATE pipeline_execution_state
            SET current_execution_id = ?,
                pipeline_type = ?,
                updated_at = ?
            WHERE id = 1
            """,
            (execution_id, normalized_pipeline_type, now_str),
        )

        conn.commit()
        return execution_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def finish_pipeline_execution(execution_id: int, status: str = "completed") -> None:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        normalized_status = (status or "completed").strip().lower()
        if normalized_status not in {"completed", "failed", "aborted"}:
            normalized_status = "completed"
        now_str = now_brasilia_str()

        cursor.execute(
            """
            UPDATE pipeline_execution_log
            SET status = ?,
                finished_at = ?
            WHERE id = ?
            """,
            (normalized_status, now_str, execution_id),
        )

        cursor.execute(
            """
            UPDATE pipeline_execution_state
            SET current_execution_id = NULL,
                pipeline_type = NULL,
                updated_at = ?
            WHERE id = 1
              AND current_execution_id = ?
            """,
            (now_str, execution_id),
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_pipeline_execution_logs(limit: int | None = None):
    conn = get_connection(row_factory=sqlite3.Row)
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM pipeline_execution_log ORDER BY id DESC"
        params = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
