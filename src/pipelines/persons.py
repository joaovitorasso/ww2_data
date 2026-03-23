import json
import os
from dataclasses import asdict

import argparse

try:
    from src.extract.persons import extract_persons
    from src.parse.person_details import parse_person_details
    from src.database.db import (
        init_db,
        insert_raw_person,
        insert_bronze_person,
        insert_silver_person,
        refresh_gold_person_metrics,
    )
except ImportError:
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)

    from extract.persons import extract_persons
    from parse.person_details import parse_person_details
    from database.db import (
        init_db,
        insert_raw_person,
        insert_bronze_person,
        insert_silver_person,
        refresh_gold_person_metrics,
    )


def _get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main(limit: int | None = None):
    """
    Persons orchestrator: extract person link list from countries.json, then parse details for each person.
    Writes:
      - data/persons.json
      - data/processed/persons_detailed.json
    """
    print("Starting WW2 persons extraction...")

    print("Initializing database...")
    init_db()

    print("Extracting person link list...")
    person_sections = extract_persons()

    remaining = limit
    if limit:
        print(f"Limiting details extraction to first {limit} people...")

    detailed_data: dict[str, list[dict]] = {}
    details_cache: dict[str, dict] = {}

    for alliance, people in person_sections.items():
        if remaining is not None and remaining <= 0:
            break

        print(f"Processing alliance: {alliance}")
        detailed_people: list[dict] = []

        for entry in people:
            if remaining is not None and remaining <= 0:
                break

            person_link = entry.get("person_link") or entry.get("link")
            if not person_link:
                detailed_people.append({"basic": entry, "details": None, "error": "missing person_link"})
                continue

            try:
                if person_link not in details_cache:
                    details_cache[person_link] = asdict(parse_person_details(person_link))

                raw_payload = {"basic": entry, "details": details_cache[person_link]}

                raw_id = insert_raw_person(raw_payload, alliance)
                bronze_id = insert_bronze_person(raw_id, raw_payload, alliance)
                insert_silver_person(bronze_id, raw_payload, alliance)

                detailed_people.append({"basic": entry, "details": details_cache[person_link]})
            except Exception as e:
                detailed_people.append({"basic": entry, "details": None, "error": str(e)})
            finally:
                if remaining is not None:
                    remaining -= 1

        detailed_data[alliance] = detailed_people
        refresh_gold_person_metrics(alliance)

    output_path = os.path.join(_get_project_root(), "data", "processed", "persons_detailed.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(detailed_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"Detailed person data saved to {output_path}")
    print("Persons extraction and database save complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run persons extraction + detailed parsing.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N people when generating persons_detailed.json (for quick tests).",
    )
    args = parser.parse_args()
    main(limit=args.limit)
