from dataclasses import dataclass
from typing import Optional

@dataclass
class Weapon:
    name: str
    link: str
    country: str
    type: Optional[str] = None
    caliber: Optional[str] = None
    capacity: Optional[str] = None
    lenght: Optional[str] = None
    barrel_lenght: Optional[str] = None
    weight: Optional[str] = None
    range: Optional[str] = None
    muzzle_velocity: Optional[str] = None
    img: Optional[str] = None