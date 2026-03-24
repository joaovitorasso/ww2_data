"""Backward-compatible wrappers for person transformation functions."""

try:
    from src.transform.persons import parse_person_details, parse_person_details_from_html
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from transform.persons import parse_person_details, parse_person_details_from_html
