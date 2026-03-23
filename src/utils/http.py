import os
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import requests


_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


_SESSION = requests.Session()
_SESSION.headers.update(_DEFAULT_HEADERS)

_LAST_REQUEST_AT = 0.0


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None

    if text.isdigit():
        return float(int(text))

    try:
        dt = parsedate_to_datetime(text)
    except Exception:
        return None

    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    seconds = (dt - now).total_seconds()
    return max(0.0, seconds)


def _rate_limit(min_delay_seconds: float):
    global _LAST_REQUEST_AT
    if min_delay_seconds <= 0:
        return

    now = time.monotonic()
    elapsed = now - _LAST_REQUEST_AT
    remaining = min_delay_seconds - elapsed
    if remaining > 0:
        time.sleep(remaining)

    _LAST_REQUEST_AT = time.monotonic()


def get_text(url: str) -> str:
    """
    HTTP GET with retry, exponential backoff and basic rate limiting.

    Environment variables (optional):
      - WW2_HTTP_TIMEOUT_SECONDS (default: 30)
      - WW2_HTTP_MIN_DELAY_SECONDS (default: 1.0)
      - WW2_HTTP_MAX_RETRIES (default: 10)
      - WW2_HTTP_BACKOFF_FACTOR (default: 2.0)
      - WW2_HTTP_MAX_BACKOFF_SECONDS (default: 120)
      - WW2_HTTP_JITTER_SECONDS (default: 0.25)
    """
    timeout = _env_float("WW2_HTTP_TIMEOUT_SECONDS", 30.0)
    min_delay = _env_float("WW2_HTTP_MIN_DELAY_SECONDS", 1.0)
    max_retries = _env_int("WW2_HTTP_MAX_RETRIES", 10)
    backoff_factor = _env_float("WW2_HTTP_BACKOFF_FACTOR", 2.0)
    max_backoff = _env_float("WW2_HTTP_MAX_BACKOFF_SECONDS", 120.0)
    jitter = _env_float("WW2_HTTP_JITTER_SECONDS", 0.25)

    retry_statuses = {429, 500, 502, 503, 504}

    for attempt in range(max_retries + 1):
        _rate_limit(min_delay)
        try:
            response = _SESSION.get(url, timeout=timeout)
        except requests.RequestException:
            if attempt >= max_retries:
                raise
            sleep_seconds = min(max_backoff, backoff_factor * (2 ** attempt))
            sleep_seconds += random.uniform(0.0, jitter)
            time.sleep(sleep_seconds)
            continue

        if response.status_code in retry_statuses:
            if attempt >= max_retries:
                response.raise_for_status()

            sleep_seconds = None
            if response.status_code == 429:
                sleep_seconds = _parse_retry_after(response.headers.get("Retry-After"))

            if sleep_seconds is None:
                sleep_seconds = min(max_backoff, backoff_factor * (2 ** attempt))

            sleep_seconds += random.uniform(0.0, jitter)
            time.sleep(sleep_seconds)
            continue

        response.raise_for_status()
        return response.text

    raise RuntimeError("unreachable")

