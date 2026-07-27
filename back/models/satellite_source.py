# models/satellite_source.py
from datetime import datetime

from extensions import db


class SatelliteSource(db.Model):
    __tablename__ = 'satellite_sources'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255))
    platform = db.Column(db.String(50))
    sensor = db.Column(db.String(50))
    band_thermal = db.Column(db.String(20))
    resolution_m = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)
    collection_id = db.Column(db.String(100))  # 🔥 ADICIONA ESSE CAMPO
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    analyses = db.relationship('CoolingAnalysis', backref='satellite', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'platform': self.platform,
            'sensor': self.sensor,
            'band_thermal': self.band_thermal,
            'resolution_m': self.resolution_m,
            'active': self.active,
            'collection_id': self.collection_id,  # 🔥 ADICIONA
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
