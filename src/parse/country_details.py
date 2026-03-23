import re
import requests
from bs4 import BeautifulSoup

try:
    from src.models.country import Country
except ImportError:
    import sys
    import os
    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from models.country import Country

def _parse_int(value: str):
    if not value:
        return None
    digits = re.sub(r'[^0-9]', '', value)
    return int(digits) if digits else None


def _clean_full_name(raw: str):
    if not raw:
        return None
    # Remover prefixos numéricos como "4" ou "7" no início
    cleaned = re.sub(r'^\d+', '', raw).strip()
    return cleaned if cleaned else None


def parse_country_details(link: str) -> Country:
    """
    Parse detailed information from a country page.
    
    Args:
        link: Relative link like '/country/germany'
    
    Returns:
        Country object with detailed info
    """
    base_url = "https://ww2db.com"
    full_url = base_url + link
    
    response = requests.get(full_url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract name from h2 tag with itemprop="name"
    name_tag = soup.find('h2', {'itemprop': 'name'})
    name = name_tag.get_text(strip=True) if name_tag else "Unknown"
    
    # Extract flag URL
    flag = None
    img_tag = soup.find('img', src=lambda x: x and '/images/flags/' in x)
    if img_tag:
        flag = base_url + img_tag['src']
    
    # Extract table data
    data = {
        'full_name': None,
        'alliance': None,
        'millitary_deaths': None,
        'civillian_deaths': None,
        'civillian_holocaust_deaths': None,
        'total_deaths': None,
        'population': None,
        'entry_date': None
    }
    rows = soup.select('table.table_noborder tr')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 3:
            continue
        label = cells[0].get_text(separator=' ', strip=True)
        value = cells[2].get_text(separator=' ', strip=True)

        label_norm = label.lower().replace('\xa0', ' ').strip()

        if 'full name' in label_norm:
            data['full_name'] = _clean_full_name(value)
        elif 'alliance' in label_norm:
            data['alliance'] = value
        elif 'military deaths' in label_norm:
            data['millitary_deaths'] = _parse_int(value)
        elif 'civilian deaths from holocaust' in label_norm or 'civ deaths from holocaust' in label_norm:
            data['civillian_holocaust_deaths'] = _parse_int(value)
        elif 'civilian deaths' in label_norm:
            data['civillian_deaths'] = _parse_int(value)
        elif 'total deaths' in label_norm:
            data['total_deaths'] = _parse_int(value)
        elif 'population' in label_norm:
            data['population'] = _parse_int(value)
        elif 'entry into ww2' in label_norm:
            data['entry_date'] = value

    # Total deaths fallback
    total_deaths = data['total_deaths']
    if total_deaths is None and data['millitary_deaths'] is not None and data['civillian_deaths'] is not None:
        total_deaths = data['millitary_deaths'] + data['civillian_deaths']

    # Use name as fallback for full_name if null
    full_name = data['full_name'] if data['full_name'] else name

    return Country(
        name=name,
        link=link,
        full_name=full_name,
        alliance=data['alliance'],
        millitary_deaths=data['millitary_deaths'],
        civillian_deaths=data['civillian_deaths'],
        civillian_holocaust_deaths=data['civillian_holocaust_deaths'],
        total_deaths=total_deaths,
        population=data['population'],
        entry_date=data['entry_date'],
        flag=flag
    )