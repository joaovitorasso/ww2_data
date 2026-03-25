import json
import time

try:
    from src.database.db import (
        finish_pipeline_execution,
        get_retry_countries,
        init_db,
        insert_bronze_country,
        insert_country_html_cache_log,
        insert_raw_country,
        insert_silver_country,
        mark_retry_country_failed,
        mark_retry_country_succeeded,
        start_pipeline_execution,
    )
    from src.extract.countries import cache_country_pages, ensure_countries_html_cache, extract_countries
    from src.load.countries import get_existing_details, get_output_path, import_details_to_db, load_transformed_data
    from src.transform.countries import parse_country_details, transform_country_sections
    from src.utils.retry_queue import get_retry_queue_settings
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from database.db import (
        finish_pipeline_execution,
        get_retry_countries,
        init_db,
        insert_bronze_country,
        insert_country_html_cache_log,
        insert_raw_country,
        insert_silver_country,
        mark_retry_country_failed,
        mark_retry_country_succeeded,
        start_pipeline_execution,
    )
    from extract.countries import cache_country_pages, ensure_countries_html_cache, extract_countries
    from load.countries import get_existing_details, get_output_path, import_details_to_db, load_transformed_data
    from transform.countries import parse_country_details, transform_country_sections
    from utils.retry_queue import get_retry_queue_settings


def _build_country_payload(section: str, basic: dict, details) -> dict:
    return {
        "basic": basic,
        "details": {
            "full_name": details.full_name,
            "alliance": details.alliance,
            "millitary_deaths": details.millitary_deaths,
            "civillian_deaths": details.civillian_deaths,
            "civillian_holocaust_deaths": details.civillian_holocaust_deaths,
            "total_deaths": details.total_deaths,
            "population": details.population,
            "entry_date": details.entry_date,
            "flag": details.flag,
        },
    }


def _process_country_retry_queue() -> None:
    wait_seconds, max_rows = get_retry_queue_settings()
    pending = get_retry_countries(limit=max_rows)
    if not pending:
        print("No pending 429 retries for countries.")
        return

    print(f"Waiting {wait_seconds}s before retrying {len(pending)} countries from retry queue...")
    if wait_seconds > 0:
        time.sleep(wait_seconds)

    succeeded = 0
    failed = 0
    for row in pending:
        retry_id = row.get("id")
        section = row.get("section")
        queue_raw_id = row.get("raw_id")
        basic = json.loads(row.get("payload") or "{}")
        link = basic.get("link")

        if not link or not section:
            mark_retry_country_failed(retry_id, "missing section or link in retry payload")
            failed += 1
            continue

        try:
            details = parse_country_details(link)
            raw_payload = _build_country_payload(section, basic, details)
            raw_id = queue_raw_id or insert_raw_country(raw_payload, section)
            bronze_id = insert_bronze_country(raw_id, raw_payload, section)
            insert_silver_country(bronze_id, raw_payload, section)
            mark_retry_country_succeeded(retry_id)
            succeeded += 1
        except Exception as exc:
            mark_retry_country_failed(retry_id, str(exc))
            failed += 1

    remaining = len(get_retry_countries(limit=max_rows))
    print(f"Countries retry queue finished. success={succeeded}, failed={failed}, remaining={remaining}")


def run() -> None:
    print("Starting WW2 countries extraction...")
    print("Initializing database...")
    init_db()
    execution_id = start_pipeline_execution("countries")
    execution_status = "completed"
    try:
        ensure_countries_html_cache(force_refresh=True)
        print("Extracting country list...")
        raw = extract_countries()
        cache_report = cache_country_pages(raw, force_refresh=False)
        insert_country_html_cache_log(
            total=cache_report.get("total", 0),
            cached=cache_report.get("cached", 0),
            fetched=cache_report.get("fetched", 0),
            errors=cache_report.get("errors", 0),
        )
        if cache_report.get("fetched_paths"):
            fetched_paths = cache_report.get("fetched_paths") or []
            preview = fetched_paths[:10]
            print("Fetched country HTML files:")
            for path in preview:
                print(f"  - {path}")
            if len(fetched_paths) > len(preview):
                print(f"  ... and {len(fetched_paths) - len(preview)} more")

        existing = get_existing_details()
        if existing is not None:
            output_path = get_output_path()
            print(f"Found existing detailed file at {output_path}. Importing into SQLite...")
            import_details_to_db(existing)
            _process_country_retry_queue()
            print("Import complete!")
            return

        data = transform_country_sections(raw)
        output_path = load_transformed_data(data, save_json=True)
        _process_country_retry_queue()
        print(f"Detailed data saved to {output_path}")
        print("Extraction and database save complete!")
    except Exception:
        execution_status = "failed"
        raise
    finally:
        finish_pipeline_execution(execution_id, execution_status)


def main() -> None:
    run()


if __name__ == "__main__":
    main()
