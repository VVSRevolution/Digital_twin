# models/sensor.py
from datetime import datetime
from typing import Optional, Dict

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from extensions import db


class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)

    # 🔥 CAMPOS OBRIGATÓRIOS
    name = db.Column(db.String(100), nullable=False)  # Nome do sensor (ex: 0238D)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # 🔥 CAMPOS OPCIONAIS
    altitude = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)  # 🔥 TUDO QUE NÃO IMPORTAR VAI AQUI

    # 🔥 GEOMETRIA (DERIVADA DE LAT/LON)
    geometry = db.Column(Geometry('POINT', srid=4326))

    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    readings = db.relationship('TemperatureReading', backref='sensor', lazy='dynamic')

    def to_dict(self):
        geom = None
        if self.geometry:
            shape = to_shape(self.geometry)
            geom = mapping(shape)

        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'description': self.description,
            'geometry': geom,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TemperatureReading(db.Model):
    __tablename__ = 'temperature_readings'

    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False, index=True)

    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    temperature = db.Column(db.Float, nullable=False)  # °C

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'sensor_id': self.sensor_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'temperature': self.temperature
        }