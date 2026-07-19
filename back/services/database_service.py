# services/database_service.py
from extensions import db
from models import SatelliteSource


class DatabaseService:

    @staticmethod
    def seed_satellites():
        """Popula a tabela de satélites com dados iniciais"""
        try:
            satellites = [
                {'name': 'Landsat 8', 'description': 'Landsat 8 OLI/TIRS - Imagens de 30m de resolução', 'platform': 'Landsat',
                 'sensor': 'OLI/TIRS', 'band_thermal': 'Band 10', 'resolution_m': 30, 'active': True},
                {'name': 'Landsat 9', 'description': 'Landsat 9 OLI-2/TIRS-2 - Imagens de 30m de resolução', 'platform': 'Landsat',
                 'sensor': 'OLI-2/TIRS-2', 'band_thermal': 'Band 10', 'resolution_m': 30, 'active': True},
                {'name': 'SENTINEL_2', 'description': 'Sentinel 2 MSI - Imagens de 10m', 'platform': 'Sentinel',
                 'sensor': 'MSI', 'band_thermal': 'Band 10', 'resolution_m': 10, 'active': False},
                {'name': 'MODIS', 'description': 'MODIS - Imagens de 1000m', 'platform': 'Terra/Aqua',
                 'sensor': 'MODIS', 'band_thermal': 'Band 31', 'resolution_m': 1000, 'active': False}
            ]

            for data in satellites:
                if not SatelliteSource.query.filter_by(name=data['name']).first():
                    db.session.add(SatelliteSource(**data))

            db.session.commit()
            print("✅ Satélites populados com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro ao popular satélites: {e}")
            db.session.rollback()
            return False