# models/park.py
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class ParkGeometry:
    """Geometria do parque (GeoJSON)"""
    type: str  # Polygon, MultiPolygon
    coordinates: List[Any]

@dataclass
class Park:
    """Modelo de dados do parque"""
    id: str
    name: str
    city: str
    country: str
    geometry: ParkGeometry
    start_date: str
    end_date: str
    created_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'country': self.country,
            'geometry': {
                'type': self.geometry.type,
                'coordinates': self.geometry.coordinates
            },
            'start_date': self.start_date,
            'end_date': self.end_date
        }