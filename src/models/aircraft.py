from dataclasses import dataclass
from typing import Optional

@dataclass
class Aircraft:
    name: str
    link: str
    country: str
    type: Optional[str] = None
    img: Optional[str] = None