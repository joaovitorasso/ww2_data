"""
Compatibility facade for database functions.

The implementation is split by domain under `src/database/`.
Existing imports from `src.database.db` continue to work.
"""

try:
    from src.database.admin import clear_db
    from src.database.common import get_db_path
    from src.database.repositories.alliances import get_all_alliances
    from src.database.repositories.countries import (
        get_country_html_cache_logs,
        get_gold_metrics_by_alliance,
        get_silver_countries_by_alliance,
        insert_bronze_country,
        insert_country_html_cache_log,
        insert_raw_country,
        insert_silver_country,
        refresh_gold_metrics,
    )
    from src.database.repositories.persons import (
        get_gold_person_metrics_by_alliance,
        get_silver_persons_by_alliance,
        insert_bronze_person,
        insert_raw_person,
        insert_silver_person,
        refresh_gold_person_metrics,
    )
    from src.database.repositories.pipeline_execution import (
        finish_pipeline_execution,
        get_pipeline_execution_logs,
        start_pipeline_execution,
    )
    from src.database.repositories.retry_queue import (
        enqueue_retry_country,
        enqueue_retry_person,
        enqueue_retry_weapon,
        get_retry_countries,
        get_retry_persons,
        get_retry_weapons,
        mark_retry_country_failed,
        mark_retry_country_succeeded,
        mark_retry_person_failed,
        mark_retry_person_succeeded,
        mark_retry_weapon_failed,
        mark_retry_weapon_succeeded,
        remove_retry_country_by_key,
        remove_retry_country_by_raw_id,
        remove_retry_person_by_key,
        remove_retry_person_by_raw_id,
        remove_retry_weapon_by_key,
        remove_retry_weapon_by_raw_id,
    )
    from src.database.repositories.weapons import (
        insert_bronze_weapon,
        insert_raw_weapon,
        insert_silver_weapon,
        refresh_gold_weapon_metrics,
    )
    from src.database.schema import init_db
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)

    from database.admin import clear_db
    from database.common import get_db_path
    from database.repositories.alliances import get_all_alliances
    from database.repositories.countries import (
        get_country_html_cache_logs,
        get_gold_metrics_by_alliance,
        get_silver_countries_by_alliance,
        insert_bronze_country,
        insert_country_html_cache_log,
        insert_raw_country,
        insert_silver_country,
        refresh_gold_metrics,
    )
    from database.repositories.persons import (
        get_gold_person_metrics_by_alliance,
        get_silver_persons_by_alliance,
        insert_bronze_person,
        insert_raw_person,
        insert_silver_person,
        refresh_gold_person_metrics,
    )
    from database.repositories.pipeline_execution import (
        finish_pipeline_execution,
        get_pipeline_execution_logs,
        start_pipeline_execution,
    )
    from database.repositories.retry_queue import (
        enqueue_retry_country,
        enqueue_retry_person,
        enqueue_retry_weapon,
        get_retry_countries,
        get_retry_persons,
        get_retry_weapons,
        mark_retry_country_failed,
        mark_retry_country_succeeded,
        mark_retry_person_failed,
        mark_retry_person_succeeded,
        mark_retry_weapon_failed,
        mark_retry_weapon_succeeded,
        remove_retry_country_by_key,
        remove_retry_country_by_raw_id,
        remove_retry_person_by_key,
        remove_retry_person_by_raw_id,
        remove_retry_weapon_by_key,
        remove_retry_weapon_by_raw_id,
    )
    from database.repositories.weapons import (
        insert_bronze_weapon,
        insert_raw_weapon,
        insert_silver_weapon,
        refresh_gold_weapon_metrics,
    )
    from database.schema import init_db


__all__ = [
    "get_db_path",
    "init_db",
    "insert_raw_country",
    "insert_bronze_country",
    "insert_silver_country",
    "insert_country_html_cache_log",
    "refresh_gold_metrics",
    "insert_raw_person",
    "insert_bronze_person",
    "insert_silver_person",
    "refresh_gold_person_metrics",
    "insert_raw_weapon",
    "insert_bronze_weapon",
    "insert_silver_weapon",
    "refresh_gold_weapon_metrics",
    "start_pipeline_execution",
    "finish_pipeline_execution",
    "get_pipeline_execution_logs",
    "enqueue_retry_country",
    "get_retry_countries",
    "mark_retry_country_succeeded",
    "mark_retry_country_failed",
    "remove_retry_country_by_key",
    "remove_retry_country_by_raw_id",
    "enqueue_retry_person",
    "get_retry_persons",
    "mark_retry_person_succeeded",
    "mark_retry_person_failed",
    "remove_retry_person_by_key",
    "remove_retry_person_by_raw_id",
    "enqueue_retry_weapon",
    "get_retry_weapons",
    "mark_retry_weapon_succeeded",
    "mark_retry_weapon_failed",
    "remove_retry_weapon_by_key",
    "remove_retry_weapon_by_raw_id",
    "get_all_alliances",
    "get_silver_countries_by_alliance",
    "get_gold_metrics_by_alliance",
    "get_country_html_cache_logs",
    "get_silver_persons_by_alliance",
    "get_gold_person_metrics_by_alliance",
    "clear_db",
]
