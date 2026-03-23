from dataclasses import dataclass
from typing import Optional

@dataclass
class Person:
    name: str
    surname: str
    link: str
    country: str
    born: Optional[str] = None
    died: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    img: Optional[str] = None