import os
import json
from bs4 import BeautifulSoup

try:
    from src.utils.configs import load_config
    from src.utils.countries_page_cache import get_countries_page_html
    from src.utils.country_html_cache import get_country_cache_path, get_country_html
except ImportError:
    import sys
    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from utils.configs import load_config
    from utils.countries_page_cache import get_countries_page_html
    from utils.country_html_cache import get_country_cache_path, get_country_html

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


def extract_countries(force_refresh: bool = False):
    link = _get_country_link()
    html = get_countries_page_html(link, fetch_if_missing=True, force_refresh=force_refresh)
    
    # Parse and save to JSON
    data = _parse_countries(html)
    output_path = os.path.join(os.path.dirname(CONFIG_PATH), '..', 'data', 'raw', 'countries.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return data


def ensure_countries_html_cache(force_refresh: bool = False) -> None:
    link = _get_country_link()
    get_countries_page_html(link, fetch_if_missing=True, force_refresh=force_refresh)


def cache_country_pages(country_sections: dict[str, list[dict]], force_refresh: bool = False) -> dict:
    total = 0
    already_cached = 0
    fetched = 0
    errors = 0
    fetched_paths: list[str] = []

    for _, countries in (country_sections or {}).items():
        for country in countries or []:
            country_link = (country or {}).get("link")
            if not country_link:
                continue

            total += 1
            html_path = get_country_cache_path(country_link)

            if not force_refresh and os.path.exists(html_path):
                already_cached += 1
                continue

            try:
                get_country_html(country_link, fetch_if_missing=True, force_refresh=force_refresh)
                fetched += 1
                fetched_paths.append(html_path)
            except Exception as exc:
                errors += 1
                print(f"  Error caching country html {country_link}: {exc}")

    print(
        "Country pages cache check:"
        f" total={total}, cached={already_cached}, fetched={fetched}, errors={errors}"
    )
    return {
        "total": total,
        "cached": already_cached,
        "fetched": fetched,
        "errors": errors,
        "fetched_paths": fetched_paths,
    }
    
    

if __name__ == "__main__":
    countries_data = extract_countries()
    print("Data saved to data/raw/countries.json")
    print(json.dumps(countries_data, indent=2, ensure_ascii=False))
