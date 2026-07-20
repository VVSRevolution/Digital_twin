# models/analysis.py
from datetime import datetime

from extensions import db


class CoolingAnalysis(db.Model):
    __tablename__ = 'cooling_analyses'

    id = db.Column(db.Integer, primary_key=True)
    park_id = db.Column(db.Integer, db.ForeignKey('parks.id'), nullable=False)
    satellite_id = db.Column(db.Integer, db.ForeignKey('satellite_sources.id'), nullable=False)

    # Métricas
    pci = db.Column(db.Float)
    pcd = db.Column(db.Float)
    pca_ha = db.Column(db.Float)
    pca_m2 = db.Column(db.Float)

    # LST
    park_lst_celsius = db.Column(db.Float)
    park_lst_kelvin = db.Column(db.Float)

    # Configuração
    num_buffers = db.Column(db.Integer)
    buffer_distance = db.Column(db.Integer)
    buffers_data = db.Column(db.JSON)

    # Metadados
    image_date = db.Column(db.String(20))
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ditto
    ditto_thing_id = db.Column(db.String(255))
    ditto_updated = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'park_id': self.park_id,
            'satellite_id': self.satellite_id,
            'pci': self.pci,
            'pcd': self.pcd,
            'pca_ha': self.pca_ha,
            'pca_m2': self.pca_m2,
            'park_lst_celsius': self.park_lst_celsius,
            'image_date': self.image_date,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None
        }
