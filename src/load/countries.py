import json
import os

try:
    from src.database.db import (
        enqueue_retry_country,
        remove_retry_country_by_raw_id,
        insert_raw_country,
        insert_bronze_country,
        insert_silver_country,
        refresh_gold_metrics,
    )
    from src.utils.retry_queue import is_429_error
except ImportError:
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.db import (
        enqueue_retry_country,
        remove_retry_country_by_raw_id,
        insert_raw_country,
        insert_bronze_country,
        insert_silver_country,
        refresh_gold_metrics,
    )
    from utils.retry_queue import is_429_error


def _get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_output_path() -> str:
    return os.path.join(_get_project_root(), "data", "processed", "countries_detailed.json")


def get_existing_details() -> dict | None:
    output_path = get_output_path()
    if not os.path.exists(output_path):
        return None
    with open(output_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_details(detailed_data: dict[str, list[dict]]) -> str:
    output_path = get_output_path()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(detailed_data, handle, indent=2, ensure_ascii=False, default=str)
    return output_path


def import_details_to_db(detailed_data: dict[str, list[dict]]) -> None:
    for section, countries in (detailed_data or {}).items():
        print(f"Importing section: {section}")
        for payload in countries or []:
            try:
                if not isinstance(payload, dict):
                    continue
                if payload.get("details") is None:
                    if is_429_error(payload.get("error")):
                        raw_id = insert_raw_country(payload, section)
                        enqueue_retry_country(
                            section,
                            payload.get("basic") or {},
                            payload.get("error"),
                            raw_id=raw_id,
                        )
                    continue

                raw_id = insert_raw_country(payload, section)
                bronze_id = insert_bronze_country(raw_id, payload, section)
                insert_silver_country(bronze_id, payload, section)
                remove_retry_country_by_raw_id(raw_id)
            except Exception as exc:
                name = (payload or {}).get("basic", {}).get("name") if isinstance(payload, dict) else None
                print(f"    Error importing {name or 'country'}: {exc}")

        refresh_gold_metrics(section)


def load_transformed_data(detailed_data: dict[str, list[dict]], save_json: bool = True) -> str | None:
    output_path = None
    if save_json:
        output_path = save_details(detailed_data)
    import_details_to_db(detailed_data)
    return output_path
