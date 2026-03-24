import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

try:
    from src.models.weapon import Weapon
    from src.utils.http import get_text
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from models.weapon import Weapon
    from utils.http import get_text


def _normalize_label(text: str) -> str:
    if not text:
        return ""
    cleaned = text.replace("\xa0", " ").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.rstrip(":")
    return cleaned.lower().strip()


_EXPECTED_LABELS = {
    "country of origin",
    "type",
    "caliber",
    "capacity",
    "length",
    "barrel length",
    "weight",
    "ammunition weight",
    "range",
    "ceiling",
    "muzzle velocity",
}


def _find_weapon_info_table(soup: BeautifulSoup):
    best_table = None
    best_score = 0

    for table in soup.find_all("table"):
        score = 0
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            label = _normalize_label(cells[0].get_text(separator=" ", strip=True))
            if label in _EXPECTED_LABELS:
                score += 1

        if score > best_score:
            best_score = score
            best_table = table

    return best_table if best_score >= 2 else None


def parse_weapon_details_from_html(html: str, link: str) -> Weapon:
    base_url = "https://ww2db.com"
    soup = BeautifulSoup(html, "html.parser")

    name = ""
    name_tag = soup.find(["h1", "h2"], {"itemprop": "name"}) or soup.find(["h1", "h2"])
    if name_tag:
        name = name_tag.get_text(separator=" ", strip=True) or ""

    country = None
    weapon_type = None
    caliber = None
    capacity = None
    length = None
    barrel_length = None
    weight = None
    range_value = None
    muzzle_velocity = None

    table = _find_weapon_info_table(soup)
    if table:
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            label = _normalize_label(cells[0].get_text(separator=" ", strip=True))
            value_cell = cells[1]
            value_text = value_cell.get_text(separator=" ", strip=True) or None

            if label == "country of origin":
                country = value_text
            elif label == "type":
                weapon_type = value_text
            elif label == "caliber":
                caliber = value_text
            elif label == "capacity":
                capacity = value_text
            elif label == "ammunition weight" and not capacity:
                capacity = value_text
            elif label == "length":
                length = value_text
            elif label == "barrel length":
                barrel_length = value_text
            elif label == "weight":
                weight = value_text
            elif label in {"range", "ceiling"} and not range_value:
                range_value = value_text
            elif label == "muzzle velocity":
                muzzle_velocity = value_text

    img = None
    img_tag = (
        soup.select_one('img[itemprop="image"]')
        or soup.select_one("img.filephoto")
        or soup.find("img", src=lambda x: x and "weapon" in x.lower() and "/images/" in x)
        or soup.find("img", src=lambda x: x and "/images/" in x and "weapon" in x.lower())
    )
    if img_tag:
        img_src = (
            (img_tag.get("src") or "").strip()
            or (img_tag.get("data-src") or "").strip()
            or (img_tag.get("data-original") or "").strip()
            or (img_tag.get("data-lazy-src") or "").strip()
        )
        if img_src:
            img = img_src if img_src.startswith("http") else urljoin(base_url, img_src)

    return Weapon(
        name=name,
        link=link,
        country=country or "",
        type=weapon_type,
        caliber=caliber,
        capacity=capacity,
        lenght=length,
        barrel_lenght=barrel_length,
        weight=weight,
        range=range_value,
        muzzle_velocity=muzzle_velocity,
        img=img,
    )


def parse_weapon_details(link: str) -> Weapon:
    """
    Parse detailed information from a weapon page.

    Args:
        link: Relative link like '/weapon.php?q=100'
              (or a full URL starting with 'http')

    Returns:
        Weapon object with detailed info
    """
    base_url = "https://ww2db.com"
    full_url = link if link.startswith("http") else (base_url + link)

    html = get_text(full_url)
    return parse_weapon_details_from_html(html, link)

