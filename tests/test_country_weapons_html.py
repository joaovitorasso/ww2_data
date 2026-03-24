#!/usr/bin/env python3
"""
Offline test for parsing the Weapons section from a country page HTML snippet.
"""

import os
import sys

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, src_path)

from extract.weapons import _parse_country_weapons


def main() -> None:
    html = """
    <html><body>
      <table border="0" class="table_noborder" width="100%">
        <tbody>
          <tr><td colspan="3"><b>Weapons</b></td></tr>
          <tr>
            <td><a href="/weapon.php?q=100">10.5 cm FlaK 38 Anti-Aircraft Gun</a></td>
            <td><a href="/weapon.php?q=7">Gewehr 43 Rifle</a></td>
          </tr>
        </tbody>
      </table>
    </body></html>
    """.strip()

    weapons = _parse_country_weapons(html)

    assert weapons == [
        {"name": "10.5 cm FlaK 38 Anti-Aircraft Gun", "link": "/weapon.php?q=100"},
        {"name": "Gewehr 43 Rifle", "link": "/weapon.php?q=7"},
    ], weapons

    print("OK:", weapons)


if __name__ == "__main__":
    main()

