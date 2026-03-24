import json
import os

try:
    from src.database.db import (
        enqueue_retry_person,
        remove_retry_person_by_raw_id,
        insert_raw_person,
        insert_bronze_person,
        insert_silver_person,
        refresh_gold_person_metrics,
    )
    from src.utils.retry_queue import is_429_error
except ImportError:
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.db import (
        enqueue_retry_person,
        remove_retry_person_by_raw_id,
        insert_raw_person,
        insert_bronze_person,
        insert_silver_person,
        refresh_gold_person_metrics,
    )
    from utils.retry_queue import is_429_error


def _get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_output_path() -> str:
    return os.path.join(_get_project_root(), "data", "processed", "persons_detailed.json")


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


def import_details_to_db(detailed_data: dict[str, list[dict]], limit: int | None = None) -> None:
    remaining = limit
    if limit:
        print(f"Limiting import to first {limit} people...")

    for alliance, people in (detailed_data or {}).items():
        if remaining is not None and remaining <= 0:
            break

        print(f"Importing alliance: {alliance}")
        for payload in people or []:
            if remaining is not None and remaining <= 0:
                break

            try:
                if not isinstance(payload, dict):
                    continue
                if payload.get("details") is None:
                    if is_429_error(payload.get("error")):
                        raw_id = insert_raw_person(payload, alliance)
                        enqueue_retry_person(
                            alliance,
                            payload.get("basic") or {},
                            payload.get("error"),
                            raw_id=raw_id,
                        )
                    continue

                raw_id = insert_raw_person(payload, alliance)
                bronze_id = insert_bronze_person(raw_id, payload, alliance)
                insert_silver_person(bronze_id, payload, alliance)
                remove_retry_person_by_raw_id(raw_id)
            except Exception as exc:
                name = payload.get("basic", {}).get("person_name") if isinstance(payload, dict) else None
                print(f"    Error importing {name or 'person'}: {exc}")
            finally:
                if remaining is not None:
                    remaining -= 1

        refresh_gold_person_metrics(alliance)


def load_transformed_data(
    detailed_data: dict[str, list[dict]],
    limit: int | None = None,
    save_json: bool = True,
) -> str | None:
    output_path = None
    if save_json:
        output_path = save_details(detailed_data)
    import_details_to_db(detailed_data, limit=limit)
    return output_path
