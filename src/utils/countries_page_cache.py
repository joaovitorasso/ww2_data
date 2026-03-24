import os

try:
    from src.utils.http import get_text
except ImportError:
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from utils.http import get_text


def _get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_countries_page_cache_path() -> str:
    return os.path.join(_get_project_root(), "data", "html", "countries.html")


def load_countries_page_html() -> str | None:
    path = get_countries_page_cache_path()
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def save_countries_page_html(html: str) -> str:
    path = get_countries_page_cache_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(html or "")
    return path


def get_countries_page_html(url: str, fetch_if_missing: bool = True, force_refresh: bool = False) -> str:
    if not force_refresh:
        cached_html = load_countries_page_html()
        if cached_html is not None:
            return cached_html

    if not fetch_if_missing:
        raise FileNotFoundError("Countries page HTML not found in cache.")

    html = get_text(url)
    save_countries_page_html(html)
    return html
