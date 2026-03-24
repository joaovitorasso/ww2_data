#!/usr/bin/env python3
"""
Offline test for the weapon details parser using a provided HTML snippet.
"""

import os
import sys

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, src_path)

from parse.weapon_details import parse_weapon_details_from_html


def main() -> None:
    html = """
    <html><body>
      <h2 itemprop="name">10.5 cm FlaK 38 Anti-Aircraft Gun</h2>
      <table class="table_noborder"><tbody>
        <tr><td class="table_noborder">Country of Origin</td><td class="table_noborder"><a href="/country/germany">Germany</a></td></tr>
        <tr><td class="table_noborder">Type</td><td class="table_noborder">Anti-Aircraft Gun</td></tr>
        <tr><td class="table_noborder">Caliber</td><td class="table_noborder">105.000 mm</td></tr>
        <tr><td class="table_noborder">Length</td><td class="table_noborder">6.648 m</td></tr>
        <tr><td class="table_noborder">Barrel Length</td><td class="table_noborder">5.547 m</td></tr>
        <tr><td class="table_noborder">Weight</td><td class="table_noborder">10224.000 kg</td></tr>
        <tr><td class="table_noborder">Ammunition Weight</td><td class="table_noborder">14.80 kg</td></tr>
        <tr><td class="table_noborder">Ceiling</td><td class="table_noborder">9.450 km</td></tr>
        <tr><td class="table_noborder">Muzzle Velocity</td><td class="table_noborder">881 m/s</td></tr>
      </tbody></table>
      <img itemprop="image" src="/images/weapon_flak38.jpg">
    </body></html>
    """.strip()

    weapon = parse_weapon_details_from_html(html, "/weapon.php?q=100")

    assert weapon.name == "10.5 cm FlaK 38 Anti-Aircraft Gun", weapon
    assert weapon.link == "/weapon.php?q=100", weapon
    assert weapon.country == "Germany", weapon
    assert weapon.type == "Anti-Aircraft Gun", weapon
    assert weapon.caliber == "105.000 mm", weapon
    assert weapon.lenght == "6.648 m", weapon
    assert weapon.barrel_lenght == "5.547 m", weapon
    assert weapon.weight == "10224.000 kg", weapon
    assert weapon.capacity == "14.80 kg", weapon
    assert weapon.range == "9.450 km", weapon
    assert weapon.muzzle_velocity == "881 m/s", weapon
    assert weapon.img == "https://ww2db.com/images/weapon_flak38.jpg", weapon

    print("OK:", weapon)


if __name__ == "__main__":
    main()

