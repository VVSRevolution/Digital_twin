# models/ndvi.py
from datetime import datetime, timezone

from extensions import db


class NDVIAnalysis(db.Model):
    __tablename__ = 'ndvi_analyses'

    id = db.Column(db.Integer, primary_key=True)
    park_id = db.Column(db.Integer, db.ForeignKey('parks.id'), nullable=False)

    # 🔥 SATÉLITE USADO (SEMPRE SENTINEL-2, MAS GUARDA)
    satellite_name = db.Column(db.String(50), nullable=False, default='SENTINEL_2')

    # 🔥 DATA DA IMAGEM SENTINEL-2 USADA
    image_date = db.Column(db.String(20), nullable=False)

    # 🔥 DADOS DO NDVI (MESMA ESTRUTURA DOS BUFFERS)
    ndvi_data = db.Column(db.JSON, nullable=False)

    # Metadados
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    park = db.relationship('Park', backref='ndvi_analyses')

    def to_dict(self):
        return {
            'id': self.id,
            'park_id': self.park_id,
            'satellite_name': self.satellite_name,
            'image_date': self.image_date,
            'ndvi': self.ndvi_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
