from dataclasses import dataclass
from typing import Optional

@dataclass
class Country:
    name: str
    link: str
    full_name: Optional[str] = None
    alliance: Optional[str] = None
    millitary_deaths: Optional[int] = None
    civillian_deaths: Optional[int] = None
    civillian_holocaust_deaths: Optional[int] = None
    total_deaths: Optional[int] = None
    population: Optional[int] = None
    entry_date: Optional[str] = None
    flag: Optional[str] = None  # URL to flag image, if available

    # Add more fields as needed based on the page structure