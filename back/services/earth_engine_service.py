# services/earth_engine_service.py
import datetime
import json
import os
import traceback
from datetime import datetime, timedelta

import ee

from config import Config


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
    def get_latest_single_date(geometry):
        """Retorna a data mais recente (como intervalo de 1 dia)"""
        try:
            park_geom = ee.Geometry(geometry)

            collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                .filterBounds(park_geom)

            try:
                count = collection.size().getInfo()
                print(f'📊 Total de imagens na região: {count}')
            except Exception as e:
                print(f'⚠️ Erro ao contar imagens: {e}')
                return None, None

            if count == 0:
                print('⚠️ Nenhuma imagem Landsat disponível para esta região')
                return None, None

            # 🔥 PEGA A IMAGEM MAIS RECENTE
            latest_image = collection.sort('system:time_start', False).first()

            if latest_image is None:
                print('⚠️ Nenhuma imagem encontrada (latest_image é None)')
                return None, None

            # 🔥 EXTRAI A DATA USANDO O METODO CORRETO
            try:
                # Tenta pegar a data como string
                date_str = ee.Date(latest_image.get('system:time_start')).format('YYYY-MM-dd').getInfo()

                if date_str is None:
                    print('⚠️ Data da imagem é None')
                    return None, None

                start = date_str
                end = ee.Date(date_str).advance(1, 'day').format('YYYY-MM-dd').getInfo()

                print(f'📅 Data mais recente: {date_str}')
                print(f'📅 Intervalo: {start} a {end}')
                return start, end

            except Exception as e:
                print(f'⚠️ Erro ao processar data da imagem: {e}')

                # 🔥 TENTA OUTRA FORMA DE PEGAR A DATA
                try:
                    # Pega a data como timestamp
                    timestamp = latest_image.get('system:time_start').getInfo()
                    date_obj = datetime.fromtimestamp(timestamp / 1000)
                    date_str = date_obj.strftime('%Y-%m-%d')

                    start = date_str
                    end = (date_obj + timedelta(days=1)).strftime('%Y-%m-%d')

                    print(f'📅 Data mais recente (timestamp): {date_str}')
                    print(f'📅 Intervalo: {start} a {end}')
                    return start, end

                except Exception as e2:
                    print(f'⚠️ Falha ao extrair data da imagem: {e2}')
                    return None, None

        except Exception as e:
            print(f'⚠️ Erro ao buscar data mais recente: {e}')
            return None, None

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
    def calculate_lst(geometry, start_date=None, end_date=None, num_buffers=11, buffer_distance=90):
        """Calcula o LST e buffers para um parque"""
        try:
            park_geom = ee.Geometry(geometry)
            print(f'🔍 Geometria processada')

            # 🔥 SE NÃO TIVER DATA, BUSCA A MAIS RECENTE (INTERVALO DE 1 DIA)
            if not start_date or not end_date:
                start_date, end_date = EarthEngineService.get_latest_single_date(geometry)
                if start_date and end_date:
                    print(f'📅 Usando intervalo de 1 dia: {start_date} a {end_date}')
                else:
                    today = datetime.now()
                    one_month_ago = today - timedelta(days=30)

                    start_date = one_month_ago.strftime('%Y-%m-%d')
                    end_date = today.strftime('%Y-%m-%d')
                    print(f'⚠️ Usando data padrão: {start_date} a {end_date}')

            print(f'📅 Datas finais: {start_date} a {end_date}')

            # 🔥 CRIA A COLEÇÃO
            collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                .filterBounds(park_geom) \
                .filterDate(start_date, end_date)

            # 🔥 VERIFICA SE EXISTEM IMAGENS
            try:
                count = collection.size().getInfo()
                print(f'📊 Encontradas {count} imagens')
            except Exception as e:
                print(f'⚠️ Erro ao contar imagens: {e}')
                return {}

            if count == 0:
                print(f'❌ Nenhuma imagem encontrada para {start_date} a {end_date}')
                return {}

            # 🔥 PEGA A IMAGEM MAIS RECENTE (NÃO A MEDIANA!)
            image = collection.sort('system:time_start', False).first()
            print(image.getInfo())

            # 🔥 EXTRAI A DATA DA IMAGEM USADA
            try:
                # 1. Pega a data da captura
                date_acquired = image.get('DATE_ACQUIRED').getInfo()

                # 2. Pega a hora exata da captura
                scene_time = image.get('SCENE_CENTER_TIME').getInfo()
                # SCENE_CENTER_TIME vem como "13:20:42.7876610Z"
                # Remove os milissegundos e o Z
                scene_time = scene_time.split('.')[0]  # "13:20:42"

                # 3. Combina data + hora
                image_datetime = f"{date_acquired}T{scene_time}Z"

                print(f'📸 Data e hora da captura: {image_datetime}')

            except Exception as e:
                print(f'⚠️ Erro ao extrair data/hora: {e}')

                # Fallback: usa system:time_start
                try:
                    timestamp = image.get('system:time_start').getInfo()
                    from datetime import datetime
                    image_datetime = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%dT%H:%M:%SZ')
                    print(f'📸 Data e hora (fallback): {image_datetime}')

                except:
                    image_datetime = start_date
                    print(f'📸 Data e hora: {image_datetime} (fallback)')

            # 🔥 CALCULA LST
            lst_raw = image.select("ST_B10")
            lst_kelvin = lst_raw.multiply(0.00341802).add(149.0)
            lst_celsius = lst_kelvin.subtract(273.15)

            # 🔥 CALCULA O LST DO PARQUE
            park_lst = lst_celsius.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=park_geom,
                scale=30,
                maxPixels=1e9
            ).getInfo()

            park_lst_celsius = park_lst.get('ST_B10')
            print(f'🌡️ LST do parque: {park_lst_celsius}°C')

            # 🔥 CALCULA BUFFERS (DINÂMICOS)
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

            # 🔥 ENCONTRA PCI, PCD, PCA
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

            # 🔥 RETORNA COM A DATA DA LEITURA
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
                'num_images': count
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
