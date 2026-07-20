# models/park.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from geoalchemy2 import Geometry

from extensions import db


# ============================================================
# 📦 DATACLASS (para uso em memória)
# ============================================================
@dataclass
class ParkGeometry:
    """Geometria do parque (GeoJSON)"""
    type: str  # Polygon, MultiPolygon
    coordinates: List[Any]


@dataclass
class ParkData:
    """Modelo de dados do parque (em memória)"""
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


# ============================================================
# 🗄️ SQLALCHEMY MODEL (para o banco de dados)
# ============================================================
class Park(db.Model):
    __tablename__ = 'parks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    osm_id = db.Column(db.String(50), unique=True)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))

    # Geometria PostGIS
    geometry = db.Column(Geometry('POLYGON', srid=4326))
    centroid = db.Column(Geometry('POINT', srid=4326))
    area_ha = db.Column(db.Float)

    # Metadados
    tags = db.Column(db.JSON)
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    analyses = db.relationship('CoolingAnalysis', backref='park', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'osm_id': self.osm_id,
            'city': self.city,
            'country': self.country,
            'area_ha': self.area_ha,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
