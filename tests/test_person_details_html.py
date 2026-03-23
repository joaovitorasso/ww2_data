#!/usr/bin/env python3
"""
Offline test for the person details parser using a provided HTML snippet.
"""

import os
import sys

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, src_path)

from parse.person_details import parse_person_details_from_html


def main() -> None:
    html = """
    <html><body>
      <table border="0"><tbody>
        <tr><td>Surname</td><td>Abetz</td></tr>
        <tr><td>Given Name</td><td>Otto</td></tr>
        <tr><td>Born</td><td>26 May 1903</td></tr>
        <tr><td>Died</td><td>5 May 1958</td></tr>
        <tr><td>Country</td><td><a href="/country/germany">Germany</a></td></tr>
        <tr><td>Category</td><td>Government</td></tr>
        <tr><td>Gender</td><td>Male</td></tr>
      </tbody></table>
      <div style="display: inline; float: right;">
        <img itemprop="image" class="filephoto" alt="Abetz file photo [6847]" title="Abetz file photo [6847]" src="/images/person_abetz1.jpg">
        <script>
          function resizeText(className, percent) { return; }
        </script>
        <br>
        <img src="/images/icon_font_small.jpg" title="Decrease font size">
        <img src="/images/icon_font_medium.jpg" title="Reset font size">
        <img src="/images/icon_font_large.jpg" title="Increase font size">
      </div>
    </body></html>
    """.strip()

    person = parse_person_details_from_html(html, "/person_bio.php?person_id=490")

    assert person.name == "Otto", person
    assert person.surname == "Abetz", person
    assert person.country == "Germany", person
    assert person.born == "26 May 1903", person
    assert person.died == "5 May 1958", person
    assert person.category == "Government", person
    assert person.gender == "Male", person
    assert person.img == "https://ww2db.com/images/person_abetz1.jpg", person

    print("OK:", person)


if __name__ == "__main__":
    main()
