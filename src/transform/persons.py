import re
from dataclasses import asdict
from urllib.parse import urljoin

from bs4 import BeautifulSoup

try:
    from src.models.person import Person
    from src.utils.http import get_text
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from models.person import Person
    from utils.http import get_text


def _normalize_label(text: str) -> str:
    if not text:
        return ""
    cleaned = text.replace("\xa0", " ").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.rstrip(":")
    return cleaned.lower().strip()


_EXPECTED_LABELS = {
    "surname",
    "given name",
    "given names",
    "born",
    "died",
    "country",
    "category",
    "gender",
}


def _find_person_info_table(soup: BeautifulSoup):
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


def parse_person_details_from_html(html: str, link: str) -> Person:
    base_url = "https://ww2db.com"
    soup = BeautifulSoup(html, "html.parser")

    given_name = None
    surname = None
    born = None
    died = None
    country = None
    category = None
    gender = None

    table = _find_person_info_table(soup)
    if table:
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            label = _normalize_label(cells[0].get_text(separator=" ", strip=True))
            value_cell = cells[1]
            value_text = value_cell.get_text(separator=" ", strip=True) or None

            if label == "surname":
                surname = value_text
            elif label in {"given name", "given names"}:
                given_name = value_text
            elif label == "born":
                born = value_text
            elif label == "died":
                died = value_text
            elif label == "country":
                country = value_text
            elif label == "category":
                category = value_text
            elif label == "gender":
                gender = value_text

    heading = soup.find(["h1", "h2"], {"itemprop": "name"})
    heading_text = heading.get_text(separator=" ", strip=True) if heading else None
    if heading_text and (not given_name or not surname):
        if "," in heading_text:
            parts = [part.strip() for part in heading_text.split(",", 1)]
            if len(parts) == 2:
                surname = surname or parts[0] or None
                given_name = given_name or parts[1] or None
        else:
            given_name = given_name or heading_text or None

    img = None
    img_tag = (
        soup.select_one('img[itemprop="image"].filephoto')
        or soup.select_one('img[itemprop="image"]')
        or soup.select_one("img.filephoto")
        or soup.find("img", src=lambda value: value and "/images/person_" in value)
        or soup.find("img", alt=lambda value: value and "file photo" in value.lower())
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

    return Person(
        name=given_name or "",
        surname=surname or "",
        link=link,
        country=country or "",
        born=born,
        died=died,
        category=category,
        gender=gender,
        img=img,
    )


def parse_person_details(link: str) -> Person:
    base_url = "https://ww2db.com"
    full_url = link if link.startswith("http") else (base_url + link)
    html = get_text(full_url)
    return parse_person_details_from_html(html, link)


def transform_person_sections(person_sections: dict[str, list[dict]], limit: int | None = None) -> dict[str, list[dict]]:
    remaining = limit
    if limit:
        print(f"Limiting details extraction to first {limit} people...")

    detailed_data: dict[str, list[dict]] = {}
    details_cache: dict[str, dict] = {}

    for alliance, people in person_sections.items():
        if remaining is not None and remaining <= 0:
            break

        print(f"Processing alliance: {alliance}")
        detailed_people: list[dict] = []

        for entry in people:
            if remaining is not None and remaining <= 0:
                break

            person_link = entry.get("person_link") or entry.get("link")
            if not person_link:
                detailed_people.append({"basic": entry, "details": None, "error": "missing person_link"})
                continue

            try:
                if person_link not in details_cache:
                    details_cache[person_link] = asdict(parse_person_details(person_link))

                detailed_people.append({"basic": entry, "details": details_cache[person_link]})
            except Exception as exc:
                detailed_people.append({"basic": entry, "details": None, "error": str(exc)})
            finally:
                if remaining is not None:
                    remaining -= 1

        detailed_data[alliance] = detailed_people

    return detailed_data

