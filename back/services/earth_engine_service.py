# services/earth_engine_service.py
import json
import os
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict

import ee

from config import Config
from models import SatelliteSource

TABLE_6_3 = {
    1: 'Dados ausentes',
    21824: 'Céu limpo com áreas de baixa pressão',
    21826: 'Nuvens expandidas sobre terra',
    21888: 'Água com áreas de baixa pressão',
    21890: 'Nuvens expandidas sobre água',
    21952: 'Água com céu limpo',
    22080: 'Media probabilidade de nuvens',
    22144: 'Media probabilidade de nuvens sobre água',
    22280: 'Alta probabilidade de nuvens',
    23888: 'Alta probabilidade de sombra de nuvens',
    23952: 'Água com sombras de nuvens',
    24088: 'Media probabilidade nuvens com sombras',
    24216: 'Media probabilidade nuvens com sombras sobre água',
    24344: 'Alta probabilidade nuvens com sombras',
    24472: 'Alta probabilidade nuvens com sombras sobre água',
    30048: 'Neve ou gelo',
    54596: 'Cirrus',
    54852: 'Cirrus com nuvens',
    55052: 'Cirrus denso'
}
TABLE_6_3_EMOJIS = {
    1: '❌',
    21824: '☀️',
    21826: '☁️',
    21888: '🌊',
    21890: '🌊️☁️',
    21952: '🌊☀️',
    22080: '↕️☁️',
    22144: '↕️🌊⛅',
    22280: '⬆️☁️',
    23888: '⬆️⛅',
    23952: '🌊⛅',
    24088: '↕️⛈️',
    24216: '↕️🌊⛈️',
    24344: '⬆️⛈️',
    24472: '⬆️🌊⛈️',
    30048: '❄️',
    54596: '🌀',
    54852: '🌀☁️',
    55052: '🌀☁️☁️'
}


class EarthEngineService:
    """Serviço para interagir com Google Earth Engine"""

    @staticmethod
    def initialize():
        """Inicializa o Earth Engine usando conta de serviço"""
        try:
            creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if creds_path and os.path.exists(creds_path):
                print(f'📁 Usando chave: {creds_path}')

                with open(creds_path, 'r') as f:
                    creds_data = json.load(f)
                    client_email = creds_data.get('client_email')
                    print(f'📧 Client email: {client_email}')

                credentials = ee.ServiceAccountCredentials(
                    client_email,
                    creds_path
                )

                ee.Initialize(credentials, project=Config.PROJECT_ID)
                print(f'✅ Earth Engine autenticado com sucesso!')
                print(f'📁 Projeto: {Config.PROJECT_ID}')
                return True
            else:
                print('⚠️ Arquivo de chave não encontrado!')
                return False

        except Exception as e:
            print(f'❌ Erro ao inicializar Earth Engine: {e}')
            traceback.print_exc()
            return False

    @staticmethod
    def get_satellite_collection(satellite_name=None):
        """
        Retorna a coleção de imagens do satélite especificado
        """
        # 🔥 BUSCA SATÉLITE NO BANCO
        if satellite_name:
            satellite = SatelliteSource.query.filter_by(name=satellite_name, active=True).first()
        else:
            # Pega o primeiro ativo
            satellite = SatelliteSource.query.filter_by(active=True).first()

        if not satellite:
            print(f"⚠️ Nenhum satélite ativo encontrado, usando LANDSAT_8 padrão")
            return ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")

        # 🔥 USA A COLLECTION_ID DO SATÉLITE CADASTRADO
        collection_id = satellite.collection_id
        print(f"🛰️ Usando satélite: {satellite.name} -> {collection_id}")

        return ee.ImageCollection(collection_id)

    # services/earth_engine_service.py

    @staticmethod
    def get_latest_single_date(geometry, satellite_name=None):
        """Retorna a data mais recente completa (YYYY-MM-DDTHH:MM:SSZ)"""
        try:
            park_geom = ee.Geometry(geometry)

            collection = EarthEngineService.get_satellite_collection(satellite_name) \
                .filterBounds(park_geom)

            try:
                count = collection.size().getInfo()
                print(f'📊 Total de imagens na região: {count}')
            except Exception as e:
                print(f'⚠️ Erro ao contar imagens: {e}')
                return None

            if count == 0:
                print('⚠️ Nenhuma imagem disponível para esta região')
                return None

            latest_image = collection.sort('system:time_start', False).first()

            if latest_image is None:
                print('⚠️ Nenhuma imagem encontrada')
                return None

            # 🔥 RETORNA SÓ A DATA COMPLETA
            try:
                date_acquired = latest_image.get('DATE_ACQUIRED').getInfo()
                scene_time = latest_image.get('SCENE_CENTER_TIME').getInfo()
                scene_time = scene_time.split('.')[0]
                image_datetime = f"{date_acquired}T{scene_time}Z"

                print(f'📅 Data mais recente: {image_datetime}')
                return image_datetime

            except Exception as e:
                print(f'⚠️ Erro ao processar data da imagem: {e}')
                try:
                    timestamp = latest_image.get('system:time_start').getInfo()
                    from datetime import datetime
                    image_datetime = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%dT%H:%M:%SZ')
                    print(f'📅 Data mais recente: {image_datetime}')
                    return image_datetime
                except:
                    return None

        except Exception as e:
            print(f'⚠️ Erro ao buscar data mais recente: {e}')
            return None

    @staticmethod
    def list_image_datetimes(geometry, start_date, end_date, satellite_name=None):
        """Lista todas as datas/hora de imagens no período (ISO UTC)."""
        try:
            print(f"\n🔍 DEBUG: list_image_datetimes()")
            print(f"   start_date: {start_date}")
            print(f"   end_date: {end_date}")
            print(f"   satellite_name: {satellite_name}")

            park_geom = ee.Geometry(geometry)
            print(f"   ✅ Geometria criada")

            collection = EarthEngineService.get_satellite_collection(satellite_name).filterBounds(park_geom)
            print(f"   ✅ Coleção filtrada por bounds")

            # 🔥 CONTA TOTAL ANTES DO FILTRO DE DATA
            try:
                total_count = collection.size().getInfo()
                print(f"   📊 Total de imagens na região (sem filtro de data): {total_count}")
            except Exception as e:
                print(f"   ⚠️ Erro ao contar total: {e}")
                total_count = 0

            # 🔥 FILTRO DE DATA
            if start_date and end_date:
                print(f"   📅 Aplicando filtro de data: {start_date} a {end_date}")
                try:
                    inclusive_end = datetime.strptime(end_date, '%Y-%m-%d')
                    end_exclusive = (inclusive_end + timedelta(days=1)).strftime('%Y-%m-%d')
                    print(f"   📅 End_date exclusivo: {end_exclusive}")
                except ValueError:
                    end_exclusive = end_date
                    print(f"   ⚠️ End_date não é YYYY-MM-DD, usando como está: {end_exclusive}")
                collection = collection.filterDate(start_date, end_exclusive)
            elif start_date and not end_date:
                today_utc = datetime.now(timezone.utc).date()
                end_exclusive = (today_utc + timedelta(days=1)).strftime('%Y-%m-%d')
                print(f"   📅 Sem end_date, usando até hoje: {end_exclusive}")
                collection = collection.filterDate(start_date, end_exclusive)
            else:
                print(f"   ⚠️ Sem start_date e end_date, sem filtro de data")

            # 🔥 CONTA DEPOIS DO FILTRO
            try:
                filtered_count = collection.size().getInfo()
                print(f"   📊 Total de imagens após filtro de data: {filtered_count}")
            except Exception as e:
                print(f"   ⚠️ Erro ao contar após filtro: {e}")
                filtered_count = 0

            if filtered_count == 0:
                print(f"   ⚠️ NENHUMA IMAGEM ENCONTRADA no período!")
                return []

            # 🔥 PEGA OS TIMESTAMPS
            print(f"   🔍 Buscando timestamps das imagens...")
            timestamps = collection.aggregate_array('system:time_start').getInfo() or []
            print(f"   📊 Total de timestamps retornados: {len(timestamps)}")

            # 🔥 FILTRA E ORDENA
            timestamps = sorted({int(ts) for ts in timestamps if ts is not None})
            print(f"   📊 Timestamps únicos após filtro: {len(timestamps)}")

            # 🔥 CONVERTE PARA DATAS
            image_datetimes = [
                datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                for ts in timestamps
            ]

            print(f"   📅 Datas encontradas:")
            for i, dt in enumerate(image_datetimes):
                print(f"      {i + 1}. {dt}")

            print(f"   ✅ Total de imagens no período: {len(image_datetimes)}")
            return image_datetimes

        except Exception as e:
            print(f'❌ Erro ao listar imagens do período: {e}')
            traceback.print_exc()
            return []

    @staticmethod
    def calculate_lst_in_geometry(geometry):
        """Calcula o LST médio em uma geometria"""
        try:
            image = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                .filterBounds(geometry) \
                .filterDate("2023-01-01", "2023-12-31") \
                .median()

            lst_raw = image.select("ST_B10")
            lst_kelvin = lst_raw.multiply(0.00341802).add(149.0)

            result = lst_kelvin.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=30,
                maxPixels=1e9
            ).getInfo()

            return result.get('ST_B10')

        except Exception as e:
            print(f'⚠️ Erro ao calcular LST: {e}')
            return None

    @staticmethod
    def calculate_lst(geometry, start_date=None, end_date=None, num_buffers=11, buffer_distance=90,
                      satellite_name=None, image_datetime=None):
        """Calcula o LST e buffers para um parque usando o satélite especificado"""
        try:
            park_geom = ee.Geometry(geometry)
            print(f'🔍 Geometria processada')

            collection = EarthEngineService.get_satellite_collection(satellite_name)
            collection = collection.filterBounds(park_geom)

            # SE TEM image_datetime, USA UMA IMAGEM ESPECÍFICA
            if image_datetime:
                print(f'📅 Usando imagem específica: {image_datetime}')
                target_start = ee.Date(image_datetime)
                target_end = target_start.advance(1, 'second')
                collection = collection.filterDate(target_start, target_end)

                try:
                    count = collection.size().getInfo()
                    print(f'📊 Encontradas {count} imagens')
                except Exception as e:
                    print(f'⚠️ Erro ao contar imagens: {e}')
                    return {}

                if count == 0:
                    print(f'❌ Nenhuma imagem encontrada para {image_datetime}')
                    return {}

                image = collection.sort('system:time_start', False).first()
                qa_pixel_band = image.select('QA_PIXEL')
                st_qa_band = image.select('ST_QA')

                qa_pixel_data = None
                st_qa_data = None

                # EXTRAI A DATA
                try:
                    date_acquired = image.get('DATE_ACQUIRED').getInfo()
                    scene_time = image.get('SCENE_CENTER_TIME').getInfo()
                    scene_time = scene_time.split('.')[0]
                    image_datetime = f"{date_acquired}T{scene_time}Z"
                    print(f'📸 Data e hora da captura: {image_datetime}')
                except Exception as e:
                    print(f'⚠️ Erro ao extrair data/hora: {e}')
                    try:
                        timestamp = image.get('system:time_start').getInfo()
                        image_datetime = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime(
                            '%Y-%m-%dT%H:%M:%SZ')
                        print(f'📸 Data e hora (fallback): {image_datetime}')
                    except:
                        image_datetime = start_date
                        print(f'📸 Data e hora: {image_datetime} (fallback)')

                # CALCULA PARA UMA IMAGEM
                lst_raw = image.select("ST_B10")
                lst_kelvin = lst_raw.multiply(0.00341802).add(149.0)
                lst_celsius = lst_kelvin.subtract(273.15)

                park_lst = lst_celsius.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=park_geom,
                    scale=30,
                    maxPixels=1e9
                ).getInfo()

                park_lst_celsius = park_lst.get('ST_B10')
                print(f'🌡️ LST do parque: {park_lst_celsius}°C')

                # CALCULA BUFFERS
                buffer_distances = [buffer_distance * (i + 1) for i in range(num_buffers)]
                buffers = []

                for i, dist in enumerate(buffer_distances):
                    buffer_geom = park_geom.buffer(dist)

                    if i > 0:
                        prev_buffer = park_geom.buffer(buffer_distances[i - 1])
                        buffer_geom = buffer_geom.difference(prev_buffer)

                    sampled = lst_celsius.sampleRegions(
                        collection=ee.FeatureCollection([ee.Feature(buffer_geom)]),
                        scale=30,
                        geometries=True
                    )
                    # 🔥 AMOSTRAR QA_PIXEL
                    qa_sampled = qa_pixel_band.sampleRegions(
                        collection=ee.FeatureCollection([ee.Feature(buffer_geom)]),
                        scale=30,
                        geometries=True
                    )

                    # 🔥 AMOSTRAR ST_QA
                    st_qa_sampled = st_qa_band.sampleRegions(
                        collection=ee.FeatureCollection([ee.Feature(buffer_geom)]),
                        scale=30,
                        geometries=True
                    )
                    qa_pixels = qa_sampled.getInfo()
                    st_qa_pixels = st_qa_sampled.getInfo()
                    pixels = sampled.getInfo()

                    # 🔥 CRIAR DICIONÁRIOS PARA BUSCAR QA POR COORDENADA
                    qa_dict = {}
                    if qa_pixels and 'features' in qa_pixels:
                        for feature in qa_pixels['features']:
                            coords = feature.get('geometry', {}).get('coordinates', [])
                            if len(coords) >= 2:
                                key = f"{coords[0]:.6f},{coords[1]:.6f}"
                                qa_dict[key] = feature.get('properties', {}).get('QA_PIXEL')

                    st_qa_dict = {}
                    if st_qa_pixels and 'features' in st_qa_pixels:
                        for feature in st_qa_pixels['features']:
                            coords = feature.get('geometry', {}).get('coordinates', [])
                            if len(coords) >= 2:
                                key = f"{coords[0]:.6f},{coords[1]:.6f}"
                                st_qa_dict[key] = feature.get('properties', {}).get('ST_QA')

                    pixel_temps = []
                    if pixels and 'features' in pixels:
                        for feature in pixels['features']:
                            props = feature.get('properties', {})
                            temp = props.get('ST_B10')
                            coords = feature.get('geometry', {}).get('coordinates', [])

                            if temp is not None and len(coords) >= 2:
                                key = f"{coords[0]:.6f},{coords[1]:.6f}"

                                # 🔥 PEGAR QA_PIXEL E ST_QA
                                qa_value = qa_dict.get(key)
                                st_qa_value = st_qa_dict.get(key)

                                # 🔥 DECODIFICAR QA_PIXEL
                                qa_decoded = None
                                if qa_value is not None:
                                    # print(f"[{coords[1]},{coords[0]}] = {qa_value}, {st_qa_value}")
                                    qa_decoded = EarthEngineService._decode_qa_pixel_for_pixel(qa_value)

                                # 🔥 CONVERTER ST_QA PARA KELVIN
                                st_qa_kelvin = None
                                if st_qa_value is not None:
                                    st_qa_kelvin = st_qa_value * 0.01

                                pixel_temps.append({
                                    'lat': coords[1],
                                    'lon': coords[0],
                                    'temperature': temp,
                                    'qa_pixel': qa_decoded,  # 🔥 ADICIONADO
                                    'st_qa': st_qa_kelvin  # 🔥 ADICIONADO
                                })

                    temps = [p['temperature'] for p in pixel_temps if p['temperature'] is not None]

                    buffers.append({
                        'distance': dist,
                        'distance_prev': buffer_distances[i - 1] if i > 0 else 0,
                        'buffer_index': i + 1,
                        'pixels': pixel_temps,
                        'statistics': {
                            'count': len(temps),
                            'mean': sum(temps) / len(temps) if temps else None,
                            'min': min(temps) if temps else None,
                            'max': max(temps) if temps else None,
                            'std': EarthEngineService._calculate_std(temps) if temps else None
                        },
                        'area_ha': buffer_geom.area().getInfo() / 10000
                    })

                    print(f'📊 Buffer {i + 1}: {dist}m, {len(temps)} pixels')

                # ENCONTRA PCI, PCD, PCA
                pci = None
                pcd = None
                pca_ha = None

                for i in range(1, len(buffers)):
                    prev_mean = buffers[i - 1]['statistics']['mean']
                    curr_mean = buffers[i]['statistics']['mean']
                    if prev_mean is not None and curr_mean is not None:
                        diff = curr_mean - prev_mean
                        if diff < 0.1:
                            if park_lst_celsius is not None:
                                pci = prev_mean - park_lst_celsius
                            pcd = buffers[i - 1]['distance']
                            pca_ha = buffers[i - 1]['area_ha']
                            break

                if pci is None and buffers:
                    last = buffers[-1]
                    if last['statistics']['mean'] is not None and park_lst_celsius is not None:
                        pci = last['statistics']['mean'] - park_lst_celsius
                        pcd = last['distance']
                        pca_ha = last['area_ha']

                print(f'❄️ PCI: {pci}°C, PCD: {pcd}m, PCA: {pca_ha}ha')

                # 🔥 CONTAR TIPOS DE QA_PIXEL
                qa_pixel_counts = {}
                total_pixels_with_qa = 0
                st_qa_values = []

                for buffer in buffers:
                    for pixel in buffer.get('pixels', []):
                        qa = pixel.get('qa_pixel')
                        if qa:
                            total_pixels_with_qa += 1
                            qa_val = qa.get('valor')
                            if qa_val:
                                qa_pixel_counts[qa_val] = qa_pixel_counts.get(qa_val, 0) + 1

                        st_qa_val = pixel.get('st_qa')
                        if st_qa_val is not None:
                            st_qa_values.append(st_qa_val)

                # 🔥 CALCULAR PORCENTAGENS
                qa_pixel_percentages = {}
                if total_pixels_with_qa > 0:
                    for qa_val, count in qa_pixel_counts.items():
                        qa_pixel_percentages[qa_val] = round((count / total_pixels_with_qa) * 100, 2)

                # 🔥 CALCULAR MÉDIA DO ST_QA
                st_qa_mean = None
                if st_qa_values:
                    st_qa_mean = round(sum(st_qa_values) / len(st_qa_values), 2)

                print(f"\n📊 ESTATÍSTICAS QA:")
                print(f"   Total pixels com QA: {total_pixels_with_qa}")
                print(f"   ST_QA médio: {st_qa_mean} K")

                qa_stats = EarthEngineService._calculate_qa_statistics(buffers)

                return {
                    'park_lst': {
                        'kelvin': park_lst_celsius + 273.15 if park_lst_celsius is not None else None,
                        'celsius': park_lst_celsius
                    },
                    'buffers': buffers,
                    'pci': pci,
                    'pcd': pcd,
                    'pca': {
                        'ha': pca_ha,
                        'm2': pca_ha * 10000 if pca_ha else None
                    },
                    'start_date': start_date,
                    'end_date': end_date,
                    'image_date': image_datetime,
                    'num_images': 1,
                    'qa_pixel': qa_stats['qa_pixel'],
                    'st_qa': qa_stats['st_qa']
                }

            # SE NÃO TEM image_datetime, USA PERÍODO
            else:
                print(f'📅 Período: {start_date} a {end_date}')

                if start_date and end_date:
                    try:
                        inclusive_end = datetime.strptime(end_date, '%Y-%m-%d')
                        end_exclusive = (inclusive_end + timedelta(days=1)).strftime('%Y-%m-%d')
                    except ValueError:
                        end_exclusive = end_date
                    collection = collection.filterDate(start_date, end_exclusive)
                    print(f'📅 Filtro: {start_date} a {end_exclusive}')

                try:
                    count = collection.size().getInfo()
                    print(f'📊 Total de imagens no período: {count}')
                except Exception as e:
                    print(f'⚠️ Erro ao contar imagens: {e}')
                    return {}

                if count == 0:
                    print(f'❌ Nenhuma imagem encontrada para {start_date} a {end_date}')
                    return {}

                image = collection.sort('system:time_start', False).first()

                # EXTRAI DATA
                try:
                    date_acquired = image.get('DATE_ACQUIRED').getInfo()
                    scene_time = image.get('SCENE_CENTER_TIME').getInfo()
                    scene_time = scene_time.split('.')[0]
                    image_datetime = f"{date_acquired}T{scene_time}Z"
                    print(f'📸 Data e hora da captura: {image_datetime}')
                except Exception as e:
                    print(f'⚠️ Erro ao extrair data/hora: {e}')
                    try:
                        timestamp = image.get('system:time_start').getInfo()
                        image_datetime = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime(
                            '%Y-%m-%dT%H:%M:%SZ')
                        print(f'📸 Data e hora (fallback): {image_datetime}')
                    except:
                        image_datetime = start_date
                        print(f'📸 Data e hora: {image_datetime} (fallback)')

                # CALCULA LST
                lst_raw = image.select("ST_B10")
                lst_kelvin = lst_raw.multiply(0.00341802).add(149.0)
                lst_celsius = lst_kelvin.subtract(273.15)

                park_lst = lst_celsius.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=park_geom,
                    scale=30,
                    maxPixels=1e9
                ).getInfo()

                park_lst_celsius = park_lst.get('ST_B10')
                print(f'🌡️ LST do parque: {park_lst_celsius}°C')

                # BUFFERS
                buffer_distances = [buffer_distance * (i + 1) for i in range(num_buffers)]
                buffers = []

                for i, dist in enumerate(buffer_distances):
                    buffer_geom = park_geom.buffer(dist)

                    if i > 0:
                        prev_buffer = park_geom.buffer(buffer_distances[i - 1])
                        buffer_geom = buffer_geom.difference(prev_buffer)

                    sampled = lst_celsius.sampleRegions(
                        collection=ee.FeatureCollection([ee.Feature(buffer_geom)]),
                        scale=30,
                        geometries=True
                    )

                    pixels = sampled.getInfo()

                    pixel_temps = []
                    if pixels and 'features' in pixels:
                        for feature in pixels['features']:
                            props = feature.get('properties', {})
                            temp = props.get('ST_B10')
                            if temp is not None:
                                coords = feature.get('geometry', {}).get('coordinates', [])
                                pixel_temps.append({
                                    'lat': coords[1] if len(coords) > 1 else None,
                                    'lon': coords[0] if len(coords) > 0 else None,
                                    'temperature': temp
                                })

                    temps = [p['temperature'] for p in pixel_temps if p['temperature'] is not None]

                    buffers.append({
                        'distance': dist,
                        'distance_prev': buffer_distances[i - 1] if i > 0 else 0,
                        'buffer_index': i + 1,
                        'pixels': pixel_temps,
                        'statistics': {
                            'count': len(temps),
                            'mean': sum(temps) / len(temps) if temps else None,
                            'min': min(temps) if temps else None,
                            'max': max(temps) if temps else None,
                            'std': EarthEngineService._calculate_std(temps) if temps else None
                        },
                        'area_ha': buffer_geom.area().getInfo() / 10000
                    })

                    print(f'📊 Buffer {i + 1}: {dist}m, {len(temps)} pixels')

                # PCI, PCD, PCA
                pci = None
                pcd = None
                pca_ha = None

                for i in range(1, len(buffers)):
                    prev_mean = buffers[i - 1]['statistics']['mean']
                    curr_mean = buffers[i]['statistics']['mean']
                    if prev_mean is not None and curr_mean is not None:
                        diff = curr_mean - prev_mean
                        if diff < 0.1:
                            if park_lst_celsius is not None:
                                pci = prev_mean - park_lst_celsius
                            pcd = buffers[i - 1]['distance']
                            pca_ha = buffers[i - 1]['area_ha']
                            break

                if pci is None and buffers:
                    last = buffers[-1]
                    if last['statistics']['mean'] is not None and park_lst_celsius is not None:
                        pci = last['statistics']['mean'] - park_lst_celsius
                        pcd = last['distance']
                        pca_ha = last['area_ha']

                print(f'❄️ PCI: {pci}°C, PCD: {pcd}m, PCA: {pca_ha}ha')

                qa_stats = EarthEngineService._calculate_qa_statistics(buffers)

                return {
                    'park_lst': {
                        'kelvin': park_lst_celsius + 273.15 if park_lst_celsius is not None else None,
                        'celsius': park_lst_celsius
                    },
                    'buffers': buffers,
                    'pci': pci,
                    'pcd': pcd,
                    'pca': {
                        'ha': pca_ha,
                        'm2': pca_ha * 10000 if pca_ha else None
                    },
                    'start_date': start_date,
                    'end_date': end_date,
                    'image_date': image_datetime,
                    'num_images': count,
                    'qa_pixel': qa_stats['qa_pixel'],
                    'st_qa': qa_stats['st_qa']
                }

        except Exception as e:
            print(f'❌ Erro no cálculo LST: {e}')
            traceback.print_exc()
            return {}

    @staticmethod
    def _calculate_std(values):
        """Calcula o desvio padrão de uma lista de valores"""
        if not values or len(values) < 2:
            return None
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    @staticmethod
    def get_lst_at_point(lon, lat, start_date, end_date):
        """Obtém o LST para um ponto específico"""
        try:
            point = ee.Geometry.Point([lon, lat])

            image = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                .filterBounds(point) \
                .filterDate(start_date, end_date) \
                .median()

            lst_raw = image.select("ST_B10")
            lst_kelvin = lst_raw.multiply(0.00341802).add(149.0)

            result = lst_kelvin.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=30,
                maxPixels=1e9
            ).getInfo()

            kelvin = result.get('ST_B10')

            return {
                'kelvin': kelvin,
                'celsius': kelvin - 273.15 if kelvin else None
            }

        except Exception as e:
            print(f'❌ Erro ao obter LST no ponto: {e}')
            return {}

    @staticmethod
    def _decode_qa_pixel_for_pixel(qa_value: int) -> Dict:
        """
        Decodifica QA_PIXEL para um único pixel
        Retorna a descrição em português baseada na tabela 6-3
        """
        if qa_value is None:
            return None

        try:
            val = int(qa_value)

            # 🔥 SE FOR UM VALOR DA TABELA 6-3, USA ELA
            if val in TABLE_6_3:
                descricao = TABLE_6_3[val]
            else:
                # 🔥 DECODIFICA OS BITS PARA VALORES NÃO LISTADOS
                partes = []

                # Bit 0: Fill
                if val & 1:
                    partes.append('preenchimento')

                # Bit 1: Dilated Cloud
                if val & 2:
                    partes.append('nuvem dilatada')

                # Bit 2: Cirrus
                if val & 4:
                    partes.append('cirrus')

                # Bit 3: Cloud
                if val & 8:
                    partes.append('nuvem')

                # Bit 4: Cloud Shadow
                if val & 16:
                    partes.append('sombra de nuvem')

                # Bit 5: Snow
                if val & 32:
                    partes.append('neve')

                # Bit 6: Clear
                is_cloud = val & 8
                is_dilated = val & 2
                if not is_cloud and not is_dilated:
                    partes.append('limpo')

                # Bit 7: Water
                if val & 64:
                    partes.append('água')

                # Confianças
                cloud_conf = ['sem confiança', 'baixa', 'média', 'alta'][(val >> 8) & 3]
                shadow_conf = ['sem confiança', 'baixa', 'reservado', 'alta'][(val >> 10) & 3]
                snow_conf = ['sem confiança', 'baixa', 'reservado', 'alta'][(val >> 12) & 3]
                cirrus_conf = ['sem confiança', 'baixa', 'reservado', 'alta'][(val >> 14) & 3]

                if cloud_conf != 'sem confiança':
                    partes.append(f'confiança de nuvem {cloud_conf}')
                if shadow_conf != 'sem confiança' and shadow_conf != 'reservado':
                    partes.append(f'confiança de sombra {shadow_conf}')
                if snow_conf != 'sem confiança' and snow_conf != 'reservado':
                    partes.append(f'confiança de neve {snow_conf}')
                if cirrus_conf != 'sem confiança' and cirrus_conf != 'reservado':
                    partes.append(f'confiança de cirrus {cirrus_conf}')

                # Se não tiver nada, é desconhecido
                if not partes:
                    descricao = f'desconhecido (valor {val})'
                else:
                    descricao = ', '.join(partes)

            # 🔥 MONTAR RESULTADO COMPLETO
            return {
                'valor': val,
                'descricao': descricao,
                'emojis': TABLE_6_3_EMOJIS[val],
                'bits': {
                    'fill': bool(val & 1),
                    'dilated_cloud': bool(val & 2),
                    'cirrus': bool(val & 4),
                    'cloud': bool(val & 8),
                    'cloud_shadow': bool(val & 16),
                    'snow': bool(val & 32),
                    'clear': not (val & 8 or val & 2),
                    'water': bool(val & 64)
                },
                'confianca': {
                    'cloud': ['sem', 'baixa', 'média', 'alta'][(val >> 8) & 3],
                    'cloud_shadow': ['sem', 'baixa', 'reservado', 'alta'][(val >> 10) & 3],
                    'snow': ['sem', 'baixa', 'reservado', 'alta'][(val >> 12) & 3],
                    'cirrus': ['sem', 'baixa', 'reservado', 'alta'][(val >> 14) & 3]
                }
            }
        except Exception as e:
            print(f"⚠️ Erro ao decodificar QA_PIXEL: {e}")
            return None

    @staticmethod
    def _calculate_qa_statistics(buffers: list) -> Dict:

        # 🔥 INICIALIZAR CONTADORES
        qa_counts = {}
        total_pixels = 0
        st_qa_values = []

        # 🔥 PERCORRER TODOS OS BUFFERS
        for buffer in buffers:
            for pixel in buffer.get('pixels', []):
                # 🔥 QA_PIXEL
                qa = pixel.get('qa_pixel')
                if qa:
                    total_pixels += 1
                    qa_val = qa.get('valor')
                    if qa_val is not None:
                        qa_counts[qa_val] = qa_counts.get(qa_val, 0) + 1

                # 🔥 ST_QA
                st_qa = pixel.get('st_qa')
                if st_qa is not None:
                    st_qa_values.append(st_qa)

        # 🔥 MONTAR RESULTADO QA_PIXEL
        qa_result = {
            'total': total_pixels,
            'types': {}
        }

        if total_pixels > 0:
            for qa_val, count in qa_counts.items():
                percent = round((count / total_pixels) * 100, 2)
                qa_result['types'][str(qa_val)] = {
                    'count': count,
                    'percent': percent,
                    'description': TABLE_6_3.get(qa_val, f'Desconhecido ({qa_val})'),
                    'emoji': TABLE_6_3_EMOJIS.get(qa_val, '❓')
                }

        # 🔥 MONTAR RESULTADO ST_QA
        st_qa_result = {
            'count': len(st_qa_values),
            'mean_kelvin': round(sum(st_qa_values) / len(st_qa_values), 2) if st_qa_values else None,
            'min_kelvin': round(min(st_qa_values), 2) if st_qa_values else None,
            'max_kelvin': round(max(st_qa_values), 2) if st_qa_values else None
        }

        return {
            'qa_pixel': qa_result,
            'st_qa': st_qa_result
        }
