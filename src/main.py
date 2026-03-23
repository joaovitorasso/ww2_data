import json
import os

try:
    from src.extract.countries import extract_countries
    from src.parse.country_details import parse_country_details
except ImportError:
    import sys
    src_root = os.path.dirname(__file__)
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from extract.countries import extract_countries
    from parse.country_details import parse_country_details

def main():
    """
    Main orchestrator: extract country list, then parse details for each.
    """
    print("Starting WW2 data extraction...")
    
    # Step 1: Extract country list
    print("Extracting country list...")
    country_sections = extract_countries()
    
    # Step 2: For each section, parse details (limit to first 3 for demo)
    detailed_data = {}
    
    for section, countries in country_sections.items():
        print(f"Processing section: {section}")
        detailed_countries = []
        
        # Limit to first 3 countries per section for demo
        for country in countries[:3]:
            try:
                print(f"  Parsing details for {country['name']}...")
                details = parse_country_details(country['link'])
                detailed_countries.append({
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
                })
            except Exception as e:
                print(f"    Error parsing {country['name']}: {e}")
                detailed_countries.append({
                    'basic': country,
                    'details': None,
                    'error': str(e)
                })
        
        detailed_data[section] = detailed_countries
    
    # Step 3: Save detailed data
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'countries_detailed.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(detailed_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"Detailed data saved to {output_path}")
    print("Extraction complete!")

if __name__ == "__main__":
    main()