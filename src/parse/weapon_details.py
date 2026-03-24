"""Backward-compatible wrappers for weapon transformation functions."""

try:
    from src.transform.weapons import parse_weapon_details, parse_weapon_details_from_html
except ImportError:
    import os
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from transform.weapons import parse_weapon_details, parse_weapon_details_from_html
