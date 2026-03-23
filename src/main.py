import json
import os

try:
    from src.extract.countries import extract_countries
    from src.parse.country_details import parse_country_details
    from src.database.db import (
        init_db,
        insert_raw_country,
        insert_bronze_country,
        insert_silver_country,
        refresh_gold_metrics
    )
except ImportError:
    import sys
    src_root = os.path.dirname(__file__)
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from extract.countries import extract_countries
    from parse.country_details import parse_country_details
    from database.db import (
        init_db,
        insert_raw_country,
        insert_bronze_country,
        insert_silver_country,
        refresh_gold_metrics
    )

def main():
    """
    Main orchestrator: extract country list, then parse details for each.
    """
    print("Starting WW2 data extraction...")
    
    # Initialize database
    print("Initializing database...")
    init_db()
    
    # Step 1: Extract country list
    print("Extracting country list...")
    country_sections = extract_countries()
    
    # Step 2: For each section, parse details
    detailed_data = {}
    
    for section, countries in country_sections.items():
        print(f"Processing section: {section}")
        detailed_countries = []
        
        for country in countries:
            try:
                if not country.get('link'):
                    # Keep countries without link: insert as NULL values, retain alliance context
                    print(f"  No link for {country['name']}; inserting as NULL with alliance {section}.")
                    raw_payload = {
                        'basic': country,
                        'details': {
                            'full_name': None,
                            'alliance': section,
                            'millitary_deaths': None,
                            'civillian_deaths': None,
                            'civillian_holocaust_deaths': None,
                            'total_deaths': None,
                            'population': None,
                            'entry_date': None,
                            'flag': None
                        }
                    }
                else:
                    print(f"  Parsing details for {country['name']}...")
                    details = parse_country_details(country['link'])

                    raw_payload = {
                        'basic': country,
                        'details': {
                            'full_name': details.full_name,
                            'alliance': details.alliance,
                            'millitary_deaths': details.millitary_deaths,
                            'civillian_deaths': details.civillian_deaths,
                            'civillian_holocaust_deaths': details.civillian_holocaust_deaths,
                            'total_deaths': details.total_deaths,
                            'population': details.population,
                            'entry_date': details.entry_date,
                            'flag': details.flag
                        }
                    }

                # Raw insertion
                raw_id = insert_raw_country(raw_payload, section)

                # Bronze insertion (copy raw parsed values)
                bronze_id = insert_bronze_country(raw_id, raw_payload, section)

                # Silver insertion (clean normalization)
                insert_silver_country(bronze_id, raw_payload, section)

                detailed_countries.append(raw_payload)
            except Exception as e:
                print(f"    Error parsing {country['name']}: {e}")
                detailed_countries.append({
                    'basic': country,
                    'details': None,
                    'error': str(e)
                })
            except Exception as e:
                print(f"    Error parsing {country['name']}: {e}")
                detailed_countries.append({
                    'basic': country,
                    'details': None,
                    'error': str(e)
                })
        
        detailed_data[section] = detailed_countries

        # Update gold metrics per section
        refresh_gold_metrics(section)
    
    # Step 3: Save detailed data to JSON (optional raw output)
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'countries_detailed.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(detailed_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"Detailed data saved to {output_path}")
    print("Extraction and database save complete!")


if __name__ == "__main__":
    main()