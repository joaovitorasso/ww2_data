import os
import requests
import json
from bs4 import BeautifulSoup

try:
    from src.utils.configs import load_config
except ImportError:
    import sys
    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from utils.configs import load_config

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'configs.yaml')


def _load_links():
    config = load_config(CONFIG_PATH)
    return config.get('link', [])


def _get_country_link():
    links = _load_links()
    for item in links:
        if isinstance(item, dict) and 'countries' in item:
            return item['countries']
    raise KeyError('countries link not found in configuration')


def _parse_countries(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    data = {}
    
    # Find all <b> tags that are followed by a table with country entries
    bold_tags = soup.find_all('b')
    for bold in bold_tags:
        section_title = bold.get_text(strip=True)
        table = bold.find_next('table')
        if not table:
            continue

        countries = []
        for row in table.find_all('tr'):
            for cell in row.find_all(['td', 'th']):
                # anchors in this cell
                cell_anchors = cell.find_all('a')
                if cell_anchors:
                    for a in cell_anchors:
                        name = a.get_text(strip=True)
                        if not name:
                            continue
                        countries.append({
                            'name': name,
                            'link': a.get('href') if a.has_attr('href') else None
                        })
                else:
                    # plain text entries like Brazil (no link)
                    text = cell.get_text(separator=' ', strip=True)
                    if text:
                        countries.append({
                            'name': text,
                            'link': None
                        })

        # Deduplicate by (name, link)
        unique_countries = []
        seen = set()
        for item in countries:
            key = (item['name'], item['link'])
            if key not in seen:
                seen.add(key)
                unique_countries.append(item)

        if unique_countries:
            data[section_title] = unique_countries
    
    return data


def extract_countries():
    link = _get_country_link()
    response = requests.get(link)

    if response.status_code != 200:
        raise ValueError(f"Failed to fetch countries data from {link}")
    
    html = response.text
    
    # Parse and save to JSON
    data = _parse_countries(html)
    output_path = os.path.join(os.path.dirname(CONFIG_PATH), '..', 'data', 'raw', 'countries.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return data
    
    

if __name__ == "__main__":
    countries_data = extract_countries()
    print("Data saved to data/raw/countries.json")
    print(json.dumps(countries_data, indent=2, ensure_ascii=False))