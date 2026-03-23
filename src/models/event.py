from dataclasses import dataclass
from typing import Optional

@dataclass
class Event:
    name: str
    link: str
    country: str
    date: Optional[str] = None
    description: Optional[str] = None