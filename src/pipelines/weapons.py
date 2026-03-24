import argparse
import json
import os
from dataclasses import asdict

try:
    from src.extract.weapons import extract_weapons
    from src.parse.weapon_details import parse_weapon_details
    from src.database.db import (
        init_db,
        insert_raw_weapon,
        insert_bronze_weapon,
        insert_silver_weapon,
        refresh_gold_weapon_metrics,
    )
except ImportError:
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)

    from extract.weapons import extract_weapons
    from parse.weapon_details import parse_weapon_details
    from database.db import (
        init_db,
        insert_raw_weapon,
        insert_bronze_weapon,
        insert_silver_weapon,
        refresh_gold_weapon_metrics,
    )


def _get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main(limit: int | None = None) -> None:
    """
    Weapons pipeline:
      1) Extract weapon links from country pages and save to data/raw/weapons.json
      2) Visit each weapon link and save detailed data to data/processed/weapons_detailed.json
    """
    print("Starting WW2 weapons extraction...")

    print("Initializing database...")
    init_db()

    output_path = os.path.join(_get_project_root(), "data", "processed", "weapons_detailed.json")
    if os.path.exists(output_path):
        print(f"Found existing detailed file at {output_path}. Importing into SQLite...")
        with open(output_path, "r", encoding="utf-8") as f:
            detailed_data = json.load(f)

        remaining = limit
        if limit:
            print(f"Limiting import to first {limit} weapons...")

        for alliance, weapons in (detailed_data or {}).items():
            if remaining is not None and remaining <= 0:
                break

            print(f"Importing alliance: {alliance}")
            for payload in weapons or []:
                if remaining is not None and remaining <= 0:
                    break

                try:
                    if not isinstance(payload, dict):
                        continue
                    if payload.get("details") is None:
                        continue

                    raw_id = insert_raw_weapon(payload, alliance)
                    bronze_id = insert_bronze_weapon(raw_id, payload, alliance)
                    insert_silver_weapon(bronze_id, payload, alliance)
                except Exception as e:
                    name = payload.get("basic", {}).get("weapon_name") if isinstance(payload, dict) else None
                    print(f"    Error importing {name or 'weapon'}: {e}")
                finally:
                    if remaining is not None:
                        remaining -= 1

            refresh_gold_weapon_metrics(alliance)

        print("Import complete!")
        return

    print("Extracting weapon link list...")
    weapon_sections = extract_weapons()

    remaining = limit
    if limit:
        print(f"Limiting details extraction to first {limit} weapons...")

    detailed_data: dict[str, list[dict]] = {}
    details_cache: dict[str, dict] = {}

    for alliance, weapons in weapon_sections.items():
        if remaining is not None and remaining <= 0:
            break

        print(f"Processing alliance: {alliance}")
        detailed_weapons: list[dict] = []

        for entry in weapons:
            if remaining is not None and remaining <= 0:
                break

            weapon_link = entry.get("weapon_link") or entry.get("link")
            if not weapon_link:
                detailed_weapons.append({"basic": entry, "details": None, "error": "missing weapon_link"})
                continue

            try:
                if weapon_link not in details_cache:
                    details_cache[weapon_link] = asdict(parse_weapon_details(weapon_link))

                raw_payload = {"basic": entry, "details": details_cache[weapon_link]}

                raw_id = insert_raw_weapon(raw_payload, alliance)
                bronze_id = insert_bronze_weapon(raw_id, raw_payload, alliance)
                insert_silver_weapon(bronze_id, raw_payload, alliance)

                detailed_weapons.append(raw_payload)
            except Exception as e:
                detailed_weapons.append({"basic": entry, "details": None, "error": str(e)})
            finally:
                if remaining is not None:
                    remaining -= 1

        detailed_data[alliance] = detailed_weapons
        refresh_gold_weapon_metrics(alliance)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(detailed_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"Detailed weapon data saved to {output_path}")
    print("Weapons extraction and database save complete!")


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
