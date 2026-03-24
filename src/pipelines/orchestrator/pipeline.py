import argparse

try:
    from src.pipelines.countries.pipeline import run as run_countries
    from src.pipelines.persons.pipeline import run as run_persons
    from src.pipelines.weapons.pipeline import run as run_weapons
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from pipelines.countries.pipeline import run as run_countries
    from pipelines.persons.pipeline import run as run_persons
    from pipelines.weapons.pipeline import run as run_weapons


def run(include_countries: bool = True, include_persons: bool = True, include_weapons: bool = True, limit: int | None = None) -> None:
    print("Starting orchestrator...")

    if include_countries:
        print("Running countries pipeline...")
        run_countries()

    if include_persons:
        print("Running persons pipeline...")
        run_persons(limit=limit)

    if include_weapons:
        print("Running weapons pipeline...")
        run_weapons(limit=limit)

    print("Orchestrator finished.")


def main(
    include_countries: bool = True,
    include_persons: bool = True,
    include_weapons: bool = True,
    limit: int | None = None,
) -> None:
    run(
        include_countries=include_countries,
        include_persons=include_persons,
        include_weapons=include_weapons,
        limit=limit,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run WW2 pipelines with dependencies.")
    parser.add_argument("--only-countries", action="store_true", help="Run only countries pipeline.")
    parser.add_argument("--only-persons", action="store_true", help="Run only persons pipeline.")
    parser.add_argument("--only-weapons", action="store_true", help="Run only weapons pipeline.")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for persons and weapons.")
    args = parser.parse_args()

    if args.only_countries:
        main(include_countries=True, include_persons=False, include_weapons=False, limit=args.limit)
    elif args.only_persons:
        main(include_countries=False, include_persons=True, include_weapons=False, limit=args.limit)
    elif args.only_weapons:
        main(include_countries=False, include_persons=False, include_weapons=True, limit=args.limit)
    else:
        main(include_countries=True, include_persons=True, include_weapons=True, limit=args.limit)
