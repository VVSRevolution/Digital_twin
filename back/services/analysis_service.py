# services/analysis_service.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from geoalchemy2.shape import to_shape
from shapely.geometry import shape

from extensions import db
from models import Park, CoolingAnalysis
from services.database_service import DatabaseService
from services.ditto_service import DittoService
from services.earth_engine_service import EarthEngineService


class AnalysisService:
    """Serviço para gerenciar análises de cooling island"""

    @staticmethod
    def _parse_bool(value: Any) -> bool:
        """Converte valores comuns para booleano real."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 't', 'yes', 'y', 'on'}
        return bool(value)

    @staticmethod
    def find_or_create_park(geometry: Any, osm_id: Optional[str], name: str, city: str, country: str, park_id: str):
        """
        Busca parque por OSM_ID ou geometria. Se não encontrar, cria novo.
        Retorna o parque e a geometria atualizada.
        """
        park = None

        if osm_id:
            # Busca por OSM_ID
            park = Park.query.filter_by(osm_id=str(osm_id)).first()

            if park:
                print(f"✅ Parque encontrado por OSM_ID: {park.name} (ID: {park.id})")
                if not geometry and park.geometry:
                    geom_wkt = to_shape(park.geometry)
                    geometry = geom_wkt.__geo_interface__
                return park, geometry

            # Busca por geometria igual
            if geometry:
                input_geom = shape(geometry)
                all_parks = Park.query.all()
                for p in all_parks:
                    if p.geometry:
                        p_geom = to_shape(p.geometry)
                        if p_geom.equals(input_geom):
                            park = p
                            print(f"✅ Parque encontrado por geometria igual: {park.name} (ID: {park.id})")
                            geometry = p_geom.__geo_interface__
                            return park, geometry

        # Sem OSM_ID, busca por geometria
        if geometry and not park:
            input_geom = shape(geometry)
            all_parks = Park.query.all()
            for p in all_parks:
                if p.geometry:
                    p_geom = to_shape(p.geometry)
                    if p_geom.equals(input_geom):
                        park = p
                        print(f"✅ Parque encontrado por geometria igual: {park.name} (ID: {park.id})")
                        geometry = p_geom.__geo_interface__
                        return park, geometry

        # Não encontrou, cria novo
        if not park:
            print(f"⚠️ Nenhum parque encontrado, criando novo...")
            park = DatabaseService.save_park(
                name=name,
                city=city,
                country=country,
                geometry=geometry,
                tags={'source': 'api', 'park_id': park_id, 'osm_id': str(osm_id) if osm_id else None}
            )
            if osm_id:
                park.osm_id = str(osm_id)
            db.session.commit()
            print(f"✅ Novo parque criado: {park.name} (ID: {park.id})")

        return park, geometry

    @staticmethod
    def find_existing_analysis(park_id: int, num_buffers: int, buffer_distance: int, start_date: str, end_date: str) -> \
            Optional[CoolingAnalysis]:
        """
        Busca análise existente com os mesmos parâmetros e mesma data da imagem.
        """
        # 🔥 BUSCA POR DATA QUE COMEÇA COM A DATA DO USUÁRIO
        existing = CoolingAnalysis.query.filter(
            CoolingAnalysis.park_id == park_id,
            CoolingAnalysis.num_buffers == num_buffers,
            CoolingAnalysis.buffer_distance == buffer_distance,
            CoolingAnalysis.image_date.like(f"{start_date}%")
        ).first()

        if existing:
            print(f"✅ Análise existente encontrada (ID: {existing.id})")
            return existing
        return None

    @staticmethod
    def find_existing_analysis_by_image_date(
            park_id: int,
            num_buffers: int,
            buffer_distance: int,
            image_date: str
    ) -> Optional[CoolingAnalysis]:
        """Busca análise existente para a mesma imagem e configuração."""
        existing = CoolingAnalysis.query.filter(
            CoolingAnalysis.park_id == park_id,
            CoolingAnalysis.num_buffers == num_buffers,
            CoolingAnalysis.buffer_distance == buffer_distance,
            CoolingAnalysis.image_date == image_date
        ).first()
        if existing:
            print(f"✅ Análise existente para imagem {image_date} (ID: {existing.id})")
        return existing

    @staticmethod
    def process_analysis(park: Park, geometry: Any, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Processa a análise de cooling island.
        """
        num_buffers = metadata.get('numBuffers', 11)
        buffer_distance = metadata.get('bufferDistance', 90)
        satellites = metadata.get('satellites', ['Landsat 8'])
        park_id = metadata.get('id', 'unknown')

        # 🔥 PEGA OS PARÂMETROS
        start_date = metadata.get('startDate')
        end_date = metadata.get('endDate')
        is_up_to_date = metadata.get('isUpToDate', True)

        satellite_name = satellites[0] if satellites and len(satellites) > 0 else 'Landsat 8'
        print(f"🛰️ SATÉLITE: {satellite_name}")
        print(f"📅 isUpToDate: {is_up_to_date}")
        print(f"📅 startDate: {start_date}")
        print(f"📅 endDate: {end_date}")

        # ============================================================
        # 🔥 VALIDAÇÃO DOS PARÂMETROS
        # ============================================================

        # 🔥 CASO 3: isUpToDate=false E endDate=null → ERRO
        if not is_up_to_date and not end_date:
            print("❌ ERRO: isUpToDate=false requer endDate")
            return None

        # 🔥 CASO 4: isUpToDate=true E endDate não é null → ERRO
        if is_up_to_date and end_date:
            print("❌ ERRO: isUpToDate=true não deve ter endDate")
            return None

        # 🔥 CASO 2: isUpToDate=false E endDate é definido
        # 🔥 CASO 1: isUpToDate=true E endDate=null

        # ============================================================
        # 🔥 DEFINE AS DATAS
        # ============================================================

        if is_up_to_date:
            # 🔥 CASO 1: Manter atualizado - SEMPRE PEGA A MAIS RECENTE
            print("📅 Modo: Manter atualizado - buscando imagem mais recente")

            # Pega a data mais recente do GEE
            latest_gee_date = EarthEngineService.get_latest_single_date(geometry, satellite_name)
            if not latest_gee_date:
                print("⚠️ Não foi possível obter data do GEE")
                return None

            # 🔥 USA A DATA MAIS RECENTE
            filter_start = latest_gee_date[:10]
            filter_end = latest_gee_date[:10]
            compare_date = latest_gee_date[:10]
            image_datetime = latest_gee_date
            print(f"📅 Data mais recente no GEE: {image_datetime}")

            # 🔥 VERIFICA SE JÁ EXISTE ANÁLISE COM ESSA DATA
            latest_analysis = CoolingAnalysis.query.filter_by(
                park_id=park.id,
                num_buffers=num_buffers,
                buffer_distance=buffer_distance
            ).order_by(CoolingAnalysis.image_date.desc()).first()

            if latest_analysis and latest_analysis.image_date[:10] == compare_date:
                print(f"✅ Análise já existe para {compare_date} - RETORNANDO DO CACHE")
                return {
                    'success': True,
                    'park_id': park.id,
                    'osm_id': park.osm_id,
                    'analysis_id': latest_analysis.id,
                    'park_lst': {
                        'celsius': latest_analysis.park_lst_celsius,
                        'kelvin': latest_analysis.park_lst_kelvin
                    },
                    'pci': latest_analysis.pci,
                    'pcd': latest_analysis.pcd,
                    'pca': {
                        'ha': latest_analysis.pca_ha,
                        'm2': latest_analysis.pca_m2
                    },
                    'buffers': latest_analysis.buffers_data or [],
                    'image_date': latest_analysis.image_date,
                    'ditto_updated': latest_analysis.ditto_updated,
                    'timestamp': latest_analysis.analyzed_at.isoformat() if latest_analysis.analyzed_at else datetime.now().isoformat(),
                    'from_cache': True
                }

            # 🔥 CALCULA A MAIS RECENTE
            print(f"⚠️ Calculando nova análise para {compare_date}...")

            result = EarthEngineService.calculate_lst(
                geometry=geometry,
                start_date=filter_start,
                end_date=filter_end,
                num_buffers=num_buffers,
                buffer_distance=buffer_distance,
                satellite_name=satellite_name,
                image_datetime=image_datetime
            )

        else:
            # 🔥 CASO 2: Período específico - USA ATÉ A DATA DEFINIDA
            print(f"📅 Modo: Período específico - até {end_date}")

            if not start_date:
                # Se não tem start_date, usa 30 dias atrás
                today = datetime.now()
                start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
                print(f"⚠️ startDate não fornecido, usando 30 dias atrás: {start_date}")

            # 🔥 USA O PERÍODO DEFINIDO PELO USUÁRIO
            filter_start = start_date
            filter_end = end_date
            compare_date = end_date  # 🔥 COMPARA A DATA FINAL
            image_datetime = end_date

            print(f"📅 Período: {filter_start} a {filter_end}")

            # 🔥 VERIFICA SE JÁ EXISTE ANÁLISE COM A DATA FINAL
            latest_analysis = CoolingAnalysis.query.filter_by(
                park_id=park.id,
                num_buffers=num_buffers,
                buffer_distance=buffer_distance
            ).filter(
                CoolingAnalysis.image_date.like(f"{end_date}%")
            ).first()

            if latest_analysis:
                print(f"✅ Análise já existe para {end_date} - RETORNANDO DO CACHE")
                return {
                    'success': True,
                    'park_id': park.id,
                    'osm_id': park.osm_id,
                    'analysis_id': latest_analysis.id,
                    'park_lst': {
                        'celsius': latest_analysis.park_lst_celsius,
                        'kelvin': latest_analysis.park_lst_kelvin
                    },
                    'pci': latest_analysis.pci,
                    'pcd': latest_analysis.pcd,
                    'pca': {
                        'ha': latest_analysis.pca_ha,
                        'm2': latest_analysis.pca_m2
                    },
                    'buffers': latest_analysis.buffers_data or [],
                    'image_date': latest_analysis.image_date,
                    'ditto_updated': latest_analysis.ditto_updated,
                    'timestamp': latest_analysis.analyzed_at.isoformat() if latest_analysis.analyzed_at else datetime.now().isoformat(),
                    'from_cache': True
                }

            # 🔥 CALCULA PARA O PERÍODO
            print(f"⚠️ Calculando nova análise para o período {filter_start} a {filter_end}...")

            result = EarthEngineService.calculate_lst(
                geometry=geometry,
                start_date=filter_start,
                end_date=filter_end,
                num_buffers=num_buffers,
                buffer_distance=buffer_distance,
                satellite_name=satellite_name,
                image_datetime=None  # 🔥 NÃO USA IMAGEM ESPECÍFICA, USA PERÍODO
            )

        # ============================================================
        # 🔥 SALVA RESULTADO
        # ============================================================

        if not result:
            return None

        image_datetime = result.get('image_date', image_datetime)

        analysis = DatabaseService.save_analysis(
            park_id=park.id,
            satellite_name=satellite_name,
            image_date=image_datetime,
            pci=result.get('pci'),
            pcd=result.get('pcd'),
            pca_ha=result.get('pca', {}).get('ha'),
            pca_m2=result.get('pca', {}).get('m2'),
            park_lst_celsius=result.get('park_lst', {}).get('celsius'),
            park_lst_kelvin=result.get('park_lst', {}).get('kelvin'),
            num_buffers=num_buffers,
            buffer_distance=buffer_distance,
            buffers_data=result.get('buffers'),
            ditto_thing_id=f"park:{park_id}",
            ditto_updated=False
        )

        # 🔥 ATUALIZA DITTO
        park_data = {
            'name': park.name,
            'city': park.city,
            'country': park.country,
            'osm_id': park.osm_id,
            'park_lst': result['park_lst']['celsius'],
            'pci': result['pci'],
            'pcd': result['pcd'],
            'pca': result['pca'],
            'buffers': result['buffers'],
            'geometry': geometry
        }
        ditto_success = DittoService.update_park_twin(park_id, park_data)

        if ditto_success:
            DatabaseService.update_ditto_status(analysis.id, True)

        db.session.commit()

        return {
            'success': True,
            'park_id': park.id,
            'osm_id': park.osm_id,
            'analysis_id': analysis.id,
            'park_lst': result['park_lst'],
            'pci': result['pci'],
            'pcd': result['pcd'],
            'pca': result['pca'],
            'buffers': result['buffers'],
            'image_date': result.get('image_date'),
            'ditto_updated': ditto_success,
            'timestamp': datetime.now().isoformat(),
            'from_cache': False
        }
