import re

from bs4 import BeautifulSoup

try:
    from src.models.country import Country
    from src.utils.country_html_cache import get_country_html
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from models.country import Country
    from utils.country_html_cache import get_country_html


def _parse_int(value: str):
    if not value:
        return None
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else None


def _clean_full_name(raw: str):
    if not raw:
        return None
    cleaned = re.sub(r"^\d+", "", raw).strip()
    return cleaned if cleaned else None


def parse_country_details(link: str) -> Country:
    base_url = "https://ww2db.com"
    html = get_country_html(link, fetch_if_missing=True)
    soup = BeautifulSoup(html, "html.parser")

    name_tag = soup.find("h2", {"itemprop": "name"})
    name = name_tag.get_text(strip=True) if name_tag else "Unknown"

    flag = None
    img_tag = soup.find("img", src=lambda value: value and "/images/flags/" in value)
    if img_tag:
        flag = base_url + img_tag["src"]

    data = {
        "full_name": None,
        "alliance": None,
        "millitary_deaths": None,
        "civillian_deaths": None,
        "civillian_holocaust_deaths": None,
        "total_deaths": None,
        "population": None,
        "entry_date": None,
    }

    for row in soup.select("table.table_noborder tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue

        label = cells[0].get_text(separator=" ", strip=True)
        value = cells[2].get_text(separator=" ", strip=True)
        label_norm = label.lower().replace("\xa0", " ").strip()

        if "full name" in label_norm:
            data["full_name"] = _clean_full_name(value)
        elif "alliance" in label_norm:
            data["alliance"] = value
        elif "military deaths" in label_norm:
            data["millitary_deaths"] = _parse_int(value)
        elif "civilian deaths from holocaust" in label_norm or "civ deaths from holocaust" in label_norm:
            data["civillian_holocaust_deaths"] = _parse_int(value)
        elif "civilian deaths" in label_norm:
            data["civillian_deaths"] = _parse_int(value)
        elif "total deaths" in label_norm:
            data["total_deaths"] = _parse_int(value)
        elif "population" in label_norm:
            data["population"] = _parse_int(value)
        elif "entry into ww2" in label_norm:
            data["entry_date"] = value

    total_deaths = data["total_deaths"]
    if total_deaths is None and data["millitary_deaths"] is not None and data["civillian_deaths"] is not None:
        total_deaths = data["millitary_deaths"] + data["civillian_deaths"]

    return Country(
        name=name,
        link=link,
        full_name=data["full_name"] or name,
        alliance=data["alliance"],
        millitary_deaths=data["millitary_deaths"],
        civillian_deaths=data["civillian_deaths"],
        civillian_holocaust_deaths=data["civillian_holocaust_deaths"],
        total_deaths=total_deaths,
        population=data["population"],
        entry_date=data["entry_date"],
        flag=flag,
    )


def transform_country_sections(country_sections: dict[str, list[dict]]) -> dict[str, list[dict]]:
    detailed_data: dict[str, list[dict]] = {}

    for section, countries in country_sections.items():
        print(f"Processing section: {section}")
        detailed_countries: list[dict] = []

        for country in countries:
            try:
                if not country.get("link"):
                    print(f"  No link for {country['name']}; inserting as NULL with alliance {section}.")
                    raw_payload = {
                        "basic": country,
                        "details": {
                            "full_name": None,
                            "alliance": section,
                            "millitary_deaths": None,
                            "civillian_deaths": None,
                            "civillian_holocaust_deaths": None,
                            "total_deaths": None,
                            "population": None,
                            "entry_date": None,
                            "flag": None,
                        },
                    }
                else:
                    print(f"  Parsing details for {country['name']}...")
                    details = parse_country_details(country["link"])
                    raw_payload = {
                        "basic": country,
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

                detailed_countries.append(raw_payload)
            except Exception as exc:
                print(f"    Error parsing {country['name']}: {exc}")
                detailed_countries.append({"basic": country, "details": None, "error": str(exc)})

        detailed_data[section] = detailed_countries

    return detailed_data
