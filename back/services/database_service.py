# services/database_service.py
import traceback
from datetime import datetime

from geoalchemy2 import WKTElement

from extensions import db
from models import Park, CoolingAnalysis, SatelliteSource


class DatabaseService:

    @staticmethod
    def seed_satellites():
        """Popula a tabela de satélites com dados iniciais"""
        try:
            satellites = [
                {'name': 'Landsat 8', 'description': 'Landsat 8 OLI/TIRS - Imagens de 30m de resolução',
                 'platform': 'Landsat',
                 'sensor': 'OLI/TIRS', 'band_thermal': 'Band 10', 'resolution_m': 30, 'active': True},
                {'name': 'Landsat 9', 'description': 'Landsat 9 OLI-2/TIRS-2 - Imagens de 30m de resolução',
                 'platform': 'Landsat',
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

    @staticmethod
    def save_park(name: str, city: str, country: str, geometry: dict, tags: dict = None) -> Park:
        """Salva um parque no banco de dados"""
        try:
            # Verificar se já existe
            existing_park = Park.query.filter_by(name=name, city=city).first()
            if existing_park:
                print(f"📌 Parque já existe: {existing_park.id} - {existing_park.name}")
                return existing_park

            # Converter geometry para WKT (PostGIS)
            geom_wkt = None
            if geometry:
                if isinstance(geometry, dict):
                    coords = geometry.get('coordinates', [])
                    if coords:
                        wkt = f"POLYGON(({', '.join([f'{p[0]} {p[1]}' for p in coords[0]])}))"
                        geom_wkt = WKTElement(wkt, srid=4326)
                else:
                    geom_wkt = geometry

            park = Park(
                name=name,
                city=city,
                country=country,
                geometry=geom_wkt,
                tags=tags or {'source': 'api'},
                created_at=datetime.utcnow()
            )
            db.session.add(park)
            db.session.flush()
            print(f"✅ Parque criado: {park.id} - {park.name}")
            return park

        except Exception as e:
            print(f"❌ Erro ao salvar parque: {e}")
            traceback.print_exc()
            raise

    @staticmethod
    def save_analysis(
            park_id: int,
            satellite_name: str,
            image_date: str,
            pci: float,
            pcd: float,
            pca_ha: float,
            pca_m2: float,
            park_lst_celsius: float,
            park_lst_kelvin: float,
            num_buffers: int,
            buffer_distance: int,
            buffers_data: list,
            ditto_thing_id: str = None,
            ditto_updated: bool = False
    ) -> CoolingAnalysis:
        """Salva uma análise de cooling island no banco"""
        try:
            # Buscar o satellite_id pelo nome
            satellite = SatelliteSource.query.filter_by(name=satellite_name).first()
            satellite_id = satellite.id if satellite else 1

            analysis = CoolingAnalysis(
                park_id=park_id,
                satellite_id=satellite_id,
                image_date=image_date,
                pci=pci,
                pcd=pcd,
                pca_ha=pca_ha,
                pca_m2=pca_m2,
                park_lst_celsius=park_lst_celsius,
                park_lst_kelvin=park_lst_kelvin,
                num_buffers=num_buffers,
                buffer_distance=buffer_distance,
                buffers_data=buffers_data,
                ditto_thing_id=ditto_thing_id or f"park:{park_id}",
                ditto_updated=ditto_updated,
                analyzed_at=datetime.utcnow()
            )
            db.session.add(analysis)
            db.session.flush()
            print(f"✅ Análise salva: {analysis.id} - PCI: {analysis.pci}°C")
            return analysis

        except Exception as e:
            print(f"❌ Erro ao salvar análise: {e}")
            traceback.print_exc()
            raise

    @staticmethod
    def update_ditto_status(analysis_id: int, status: bool):
        """Atualiza o status do Ditto para uma análise"""
        try:
            analysis = CoolingAnalysis.query.get(analysis_id)
            if analysis:
                analysis.ditto_updated = status
                db.session.commit()
                print(f"✅ Ditto status atualizado para análise {analysis_id}: {status}")
        except Exception as e:
            print(f"❌ Erro ao atualizar status do Ditto: {e}")
            db.session.rollback()

    @staticmethod
    def get_park_history(park_id: int, limit: int = 10):
        """Busca histórico de análises de um parque"""
        try:
            analyses = CoolingAnalysis.query.filter_by(park_id=park_id) \
                .order_by(CoolingAnalysis.analyzed_at.desc()) \
                .limit(limit) \
                .all()
            return analyses
        except Exception as e:
            print(f"❌ Erro ao buscar histórico: {e}")
            return []
