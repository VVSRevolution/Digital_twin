# models/satellite_source.py
from extensions import db
from datetime import datetime


class SatelliteSource(db.Model):
    __tablename__ = 'satellite_sources'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    platform = db.Column(db.String(50))
    sensor = db.Column(db.String(50))
    band_thermal = db.Column(db.String(10))
    resolution_m = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'platform': self.platform,
            'sensor': self.sensor,
            'band_thermal': self.band_thermal,
            'resolution': self.resolution_m,
            'active': self.active
        }