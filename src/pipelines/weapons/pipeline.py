import argparse
import json
import os
import time
from dataclasses import asdict

try:
    from src.database.db import (
        finish_pipeline_execution,
        get_retry_weapons,
        init_db,
        insert_bronze_weapon,
        insert_raw_weapon,
        insert_silver_weapon,
        mark_retry_weapon_failed,
        mark_retry_weapon_succeeded,
        start_pipeline_execution,
    )
    from src.extract.weapons import extract_weapons
    from src.load.weapons import get_existing_details, get_output_path, import_details_to_db, load_transformed_data
    from src.pipelines.countries.pipeline import run as run_countries_pipeline
    from src.transform.weapons import parse_weapon_details, transform_weapon_sections
    from src.utils.retry_queue import get_retry_queue_settings
except ImportError:
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.db import (
        finish_pipeline_execution,
        get_retry_weapons,
        init_db,
        insert_bronze_weapon,
        insert_raw_weapon,
        insert_silver_weapon,
        mark_retry_weapon_failed,
        mark_retry_weapon_succeeded,
        start_pipeline_execution,
    )
    from extract.weapons import extract_weapons
    from load.weapons import get_existing_details, get_output_path, import_details_to_db, load_transformed_data
    from pipelines.countries.pipeline import run as run_countries_pipeline
    from transform.weapons import parse_weapon_details, transform_weapon_sections
    from utils.retry_queue import get_retry_queue_settings


def _get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _ensure_countries_dependency() -> None:
    countries_path = os.path.join(_get_project_root(), "data", "raw", "countries.json")
    if os.path.exists(countries_path):
        return

    print(f"Dependency missing: {countries_path}. Running countries pipeline first...")
    run_countries_pipeline()


def _process_weapon_retry_queue() -> None:
    wait_seconds, max_rows = get_retry_queue_settings()
    pending = get_retry_weapons(limit=max_rows)
    if not pending:
        print("No pending 429 retries for weapons.")
        return

    print(f"Waiting {wait_seconds}s before retrying {len(pending)} weapons from retry queue...")
    if wait_seconds > 0:
        time.sleep(wait_seconds)

    succeeded = 0
    failed = 0
    for row in pending:
        retry_id = row.get("id")
        alliance = row.get("alliance")
        queue_raw_id = row.get("raw_id")
        basic = json.loads(row.get("payload") or "{}")
        weapon_link = basic.get("weapon_link") or basic.get("link")

        if not alliance or not weapon_link:
            mark_retry_weapon_failed(retry_id, "missing alliance or weapon_link in retry payload")
            failed += 1
            continue

        try:
            details = asdict(parse_weapon_details(weapon_link))
            raw_payload = {"basic": basic, "details": details}
            raw_id = queue_raw_id or insert_raw_weapon(raw_payload, alliance)
            bronze_id = insert_bronze_weapon(raw_id, raw_payload, alliance)
            insert_silver_weapon(bronze_id, raw_payload, alliance)
            mark_retry_weapon_succeeded(retry_id)
            succeeded += 1
        except Exception as exc:
            mark_retry_weapon_failed(retry_id, str(exc))
            failed += 1

    remaining = len(get_retry_weapons(limit=max_rows))
    print(f"Weapons retry queue finished. success={succeeded}, failed={failed}, remaining={remaining}")


def run(limit: int | None = None) -> None:
    print("Starting WW2 weapons extraction...")
    print("Initializing database...")
    init_db()
    execution_id = start_pipeline_execution("weapons")
    execution_status = "completed"
    try:
        existing = get_existing_details()
        if existing is not None:
            output_path = get_output_path()
            print(f"Found existing detailed file at {output_path}. Importing into SQLite...")
            import_details_to_db(existing, limit=limit)
            _process_weapon_retry_queue()
            print("Import complete!")
            return

        _ensure_countries_dependency()

        print("Extracting weapon link list...")
        raw = extract_weapons()
        data = transform_weapon_sections(raw, limit=limit)
        output_path = load_transformed_data(data, limit=limit, save_json=True)
        _process_weapon_retry_queue()
        print(f"Detailed weapon data saved to {output_path}")
        print("Weapons extraction and database save complete!")
    except Exception:
        execution_status = "failed"
        raise
    finally:
        finish_pipeline_execution(execution_id, execution_status)


def main(limit: int | None = None) -> None:
    run(limit=limit)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run weapons extraction + detailed parsing.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N weapons when generating weapons_detailed.json (for quick tests).",
    )
    args = parser.parse_args()
    main(limit=args.limit)
