import os
import re
from urllib.parse import urlparse

try:
    from src.utils.http import get_text
except ImportError:
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from utils.http import get_text


_BASE_URL = "https://ww2db.com"


def _get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _normalize_country_link(country_link: str) -> str:
    text = str(country_link or "").strip()
    if not text:
        return ""

    if text.startswith("http"):
        parsed = urlparse(text)
        text = parsed.path or ""
    else:
        text = text.split("#", 1)[0]
        text = text.split("?", 1)[0]

    if not text.startswith("/"):
        text = "/" + text
    return text.rstrip("/") or "/"

def _country_slug(country_link: str) -> str:
    normalized = _normalize_country_link(country_link)
    if normalized.startswith("/country/"):
        raw_slug = normalized[len("/country/") :]
    else:
        raw_slug = normalized.strip("/")

    safe_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", (raw_slug or "unknown").lower()).strip("_")
    return safe_slug or "unknown"


def get_country_cache_path(country_link: str | None = None) -> str:
    cache_dir = os.path.join(_get_project_root(), "data", "html")
    if country_link:
        return os.path.join(cache_dir, f"{_country_slug(country_link)}.html")
    return cache_dir


def load_country_html(country_link: str) -> str | None:
    path = get_country_cache_path(country_link)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def save_country_html(country_link: str, html: str) -> str:
    path = get_country_cache_path(country_link)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(html or "")
    return path


def get_country_html(country_link: str, fetch_if_missing: bool = True, force_refresh: bool = False) -> str:
    if not force_refresh:
        cached_html = load_country_html(country_link)
        if cached_html is not None:
            return cached_html

    if not fetch_if_missing:
        raise FileNotFoundError(f"Country HTML not found in cache for link: {country_link}")

    normalized_link = _normalize_country_link(country_link)
    full_url = country_link if str(country_link).strip().startswith("http") else (_BASE_URL + normalized_link)
    html = get_text(full_url)
    save_country_html(country_link, html)
    return html
