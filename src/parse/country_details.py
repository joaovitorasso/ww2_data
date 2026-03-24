"""Backward-compatible wrappers for country transformation functions."""

try:
    from src.transform.countries import parse_country_details
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from transform.countries import parse_country_details
