#!/usr/bin/env python3
"""
Script to test parsing functionality.
"""

import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, src_path)

from transform.countries import parse_country_details
from transform.persons import parse_person_details

def test_parsing():
    """Test parsing a single country."""
    test_link = "/country/germany"  # Example link
    
    try:
        country = parse_country_details(test_link)
        print("Test successful!")
        print(f"Name: {country.name}")
        print(f"Link: {country.link}")
        print(f"Full Name: {country.full_name}")
        print(f"Alliance: {country.alliance}")
        print(f"Military Deaths: {country.millitary_deaths}")
        print(f"Civilian Deaths: {country.civillian_deaths}")
        print(f"Holocaust Deaths: {country.civillian_holocaust_deaths}")
        print(f"Total Deaths: {country.total_deaths}")
        print(f"Population: {country.population}")
        print(f"Entry Date: {country.entry_date}")
        print(f"Flag: {country.flag}")
    except Exception as e:
        print(f"Test failed: {e}")


def test_person_parsing():
    """Test parsing a single person."""
    test_link = "/person_bio.php?person_id=490"  # Example link (Otto Abetz)

    try:
        person = parse_person_details(test_link)
        print("Person test successful!")
        print(f"Given Name: {person.name}")
        print(f"Surname: {person.surname}")
        print(f"Country: {person.country}")
        print(f"Born: {person.born}")
        print(f"Died: {person.died}")
        print(f"Category: {person.category}")
        print(f"Gender: {person.gender}")
        print(f"Image: {person.img}")
    except Exception as e:
        print(f"Person test failed: {e}")

if __name__ == "__main__":
    test_parsing()
    test_person_parsing()
