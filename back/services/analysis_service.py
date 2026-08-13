# services/analysis_service.py
from datetime import datetime
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
    def find_or_create_park(geometry: Any, osm_id: Optional[str], name: str, city: str, country: str, park_id: str,
                            is_up_to_date=False):
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
            park.is_up_to_date = is_up_to_date
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
        - Se startDate for fornecido, processa TODAS as imagens disponíveis a partir daquela data.
        - Se endDate for fornecido, limita o período (exceto se isUpToDate for True, aí usa hoje).
        - Se isUpToDate for True e startDate for None, busca a mais recente.
        - Retorna a análise mais recente (para exibição) e salva todas no banco.
        """
        num_buffers = metadata.get('numBuffers', 11)
        buffer_distance = metadata.get('bufferDistance', 90)
        satellites = metadata.get('satellites', ['Landsat 8'])
        park_id = metadata.get('id', 'unknown')

        start_date = metadata.get('startDate')
        end_date = metadata.get('endDate')
        is_up_to_date = metadata.get('isUpToDate', True)  # padrão True

        satellite_name = satellites[0] if satellites and len(satellites) > 0 else 'Landsat 8'
        print(f"🛰️ SATÉLITE: {satellite_name}")
        print(f"📅 isUpToDate: {is_up_to_date}")
        print(f"📅 startDate: {start_date}")
        print(f"📅 endDate: {end_date}")

        # ============================================================
        # 🔥 DECIDE O MODO DE PROCESSAMENTO
        # ============================================================
        image_dates = []

        if start_date:
            # 🔥 MODO PERÍODO: processa todas as imagens a partir de start_date
            filter_start = start_date

            if is_up_to_date:
                # Se isUpToDate for True, usa a data atual como fim (vai sempre buscar a mais recente)
                filter_end = datetime.now().strftime('%Y-%m-%d')
                print(f"📅 isUpToDate=True, endDate ignorado, usando data atual: {filter_end}")
            else:
                # Se isUpToDate for False, usa o endDate fornecido ou a data mais recente disponível
                if end_date:
                    filter_end = end_date
                else:
                    # Busca a data mais recente disponível no GEE
                    latest = EarthEngineService.get_latest_single_date(geometry, satellite_name)
                    filter_end = latest[:10] if latest else datetime.now().strftime('%Y-%m-%d')
                print(f"📅 isUpToDate=False, usando endDate: {filter_end}")

            print(f"📅 Período: {filter_start} a {filter_end}")

            # 🔥 Busca todas as datas disponíveis no período
            image_dates = EarthEngineService.list_image_datetimes(
                geometry=geometry,
                start_date=filter_start,
                end_date=filter_end,
                satellite_name=satellite_name
            )
            if not image_dates:
                print(f"⚠️ Nenhuma imagem disponível no período {filter_start} a {filter_end}")
                return None

            print(f"📊 Total de imagens no período: {len(image_dates)}")

        else:
            # 🔥 MODO ÚNICA IMAGEM: apenas a mais recente
            print("📅 Modo: Imagem única - buscando a mais recente")
            latest_gee_date = EarthEngineService.get_latest_single_date(geometry, satellite_name)
            if not latest_gee_date:
                print("⚠️ Não foi possível obter data do GEE")
                return None
            image_dates = [latest_gee_date]
            print(f"📅 Data mais recente no GEE: {latest_gee_date}")

        # ============================================================
        # 🔥 PROCESSAR CADA IMAGEM (CRIAR OU RECUPERAR)
        # ============================================================
        all_analyses = []  # Guarda objetos CoolingAnalysis já salvos

        for img_date in image_dates:
            # 1. Verifica se já existe análise para esta data
            existing = CoolingAnalysis.query.filter(
                CoolingAnalysis.park_id == park.id,
                CoolingAnalysis.num_buffers == num_buffers,
                CoolingAnalysis.buffer_distance == buffer_distance,
                CoolingAnalysis.image_date == img_date
            ).first()

            if existing:
                print(f"✅ Análise existente para {img_date} (ID: {existing.id})")
                all_analyses.append(existing)
                continue

            # 2. Se não existe, calcula e salva
            print(f"🔄 Calculando análise para {img_date}...")
            result = EarthEngineService.calculate_lst(
                geometry=geometry,
                start_date=img_date[:10],
                end_date=img_date[:10],
                num_buffers=num_buffers,
                buffer_distance=buffer_distance,
                satellite_name=satellite_name,
                image_datetime=img_date
            )

            if not result:
                print(f"❌ Falha ao processar imagem {img_date}")
                continue

            # Salva no banco
            analysis = DatabaseService.save_analysis(
                park_id=park.id,
                satellite_name=satellite_name,
                image_date=img_date,
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
                ditto_updated=False,
                qa_pixel=result.get('qa_pixel'),
                st_qa=result.get('st_qa')
            )

            # Atualiza DITTO (opcional)
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
            all_analyses.append(analysis)
            print(f"✅ Análise salva para {img_date} (ID: {analysis.id})")

        # ============================================================
        # 🔥 RETORNA A ANÁLISE MAIS RECENTE (primeira da lista ordenada)
        # ============================================================
        if not all_analyses:
            print("❌ Nenhuma análise foi processada com sucesso")
            return None

        # Ordena por data decrescente (mais recente primeiro)
        all_analyses.sort(key=lambda a: a.image_date, reverse=True)
        latest = all_analyses[0]

        print(f"📌 Retornando análise mais recente: {latest.image_date} (ID: {latest.id})")

        return {
            'success': True,
            'park_id': park.id,
            'osm_id': park.osm_id,
            'analysis_id': latest.id,
            'park_lst': {
                'celsius': latest.park_lst_celsius,
                'kelvin': latest.park_lst_kelvin
            },
            'pci': latest.pci,
            'pcd': latest.pcd,
            'pca': {
                'ha': latest.pca_ha,
                'm2': latest.pca_m2
            },
            'buffers': latest.buffers_data or [],
            'qa_pixel': latest.qa_pixel,
            'st_qa': latest.st_qa,
            'image_date': latest.image_date,
            'ditto_updated': latest.ditto_updated,
            'timestamp': latest.analyzed_at.isoformat() if latest.analyzed_at else datetime.now().isoformat(),
            'from_cache': False
        }
