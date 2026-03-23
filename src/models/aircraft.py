from dataclasses import dataclass
from typing import Optional

@dataclass
class Aircraft:
    name: str
    link: str
    country: str
    manufactor: Optional[str] = None
    machinery: Optional[str] = None
    armament: Optional[str] = None
    crew: Optional[str] = None
    span: Optional[str] = None
    lenght: Optional[str] = None
    height: Optional[str] = None
    wing_area: Optional[str] = None
    weight_empty: Optional[str] = None
    weight_loaded: Optional[str] = None
    speed_max: Optional[str] = None
    service_ceiling: Optional[str] = None
    range_normal: Optional[str] = None
    range_max: Optional[str] = None
    type: Optional[str] = None
    img: Optional[str] = None