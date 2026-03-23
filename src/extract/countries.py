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
    
    # Find all <b> tags that are followed by a table with links
    bold_tags = soup.find_all('b')
    for bold in bold_tags:
        section_title = bold.get_text(strip=True)
        table = bold.find_next('table')
        if table:
            links = table.find_all('a', href=True)
            if links:  # Only include if there are links
                countries = []
                for link in links:
                    countries.append({
                        'name': link.get_text(strip=True),
                        'link': link['href']
                    })
                data[section_title] = countries
    
    return data


def extract_countries():
    link = _get_country_link()
    response = requests.get(link)

    if response.status_code != 200:
        raise ValueError(f"Failed to fetch countries data from {link}")
    
    html = response.text
    
    # Parse and save to JSON
    data = _parse_countries(html)
    output_path = os.path.join(os.path.dirname(CONFIG_PATH), '..', 'data', 'countries.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return data
    
    

if __name__ == "__main__":
    countries_data = extract_countries()
    print("Data saved to data/countries.json")
    print(json.dumps(countries_data, indent=2, ensure_ascii=False))