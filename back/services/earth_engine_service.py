# services/earth_engine_service.py
import json
import os
import traceback
from datetime import datetime, timedelta, timezone

import ee

from config import Config
from models import SatelliteSource


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
            print(f"\n🔍 DEBUG: calculate_lst()")
            print(f"   start_date: {start_date}")
            print(f"   end_date: {end_date}")
            print(f"   image_datetime: {image_datetime}")
            print(f"   satellite_name: {satellite_name}")
            print(f"   num_buffers: {num_buffers}")
            print(f"   buffer_distance: {buffer_distance}")

            park_geom = ee.Geometry(geometry)
            print(f'   ✅ Geometria processada')

            # 🔥 USA A COLEÇÃO DO SATÉLITE
            collection = EarthEngineService.get_satellite_collection(satellite_name)
            print(f"   ✅ Coleção obtida")

            # 🔥 SE NÃO TIVER DATA, BUSCA A MAIS RECENTE
            if not image_datetime and (not start_date or not end_date):
                print(f"   ⚠️ Sem data, buscando a mais recente...")
                image_datetime = EarthEngineService.get_latest_single_date(geometry, satellite_name)

                if image_datetime:
                    start_date = image_datetime[:10]
                    end_date = image_datetime[:10]
                    print(f'   📅 Usando data mais recente: {start_date}')
                    print(f'   📅 Data completa (para salvar): {image_datetime}')
                else:
                    today = datetime.now()
                    one_month_ago = today - timedelta(days=30)
                    start_date = one_month_ago.strftime('%Y-%m-%d')
                    end_date = today.strftime('%Y-%m-%d')
                    print(f'   ⚠️ Usando data padrão: {start_date} a {end_date}')
                    image_datetime = start_date

            # 🔥 FILTRA POR DATA
            print(f"   📅 Aplicando filtro na coleção...")
            collection = collection.filterBounds(park_geom)

            if image_datetime:
                print(f"   📅 Usando imagem específica: {image_datetime}")
                target_start = ee.Date(image_datetime)
                target_end = target_start.advance(1, 'second')
                collection = collection.filterDate(target_start, target_end)
                print(f"   📅 Filtro: {image_datetime} a {image_datetime} + 1s")
            else:
                end_exclusive = end_date
                if start_date and end_date:
                    try:
                        inclusive_end = datetime.strptime(end_date, '%Y-%m-%d')
                        end_exclusive = (inclusive_end + timedelta(days=1)).strftime('%Y-%m-%d')
                        print(f"   📅 End_date exclusivo: {end_exclusive}")
                    except ValueError:
                        end_exclusive = end_date
                        print(f"   ⚠️ End_date não é YYYY-MM-DD: {end_exclusive}")
                collection = collection.filterDate(start_date, end_exclusive)
                print(f"   📅 Filtro: {start_date} a {end_exclusive}")

            # 🔥 VERIFICA SE EXISTEM IMAGENS
            try:
                count = collection.size().getInfo()
                print(f'   📊 Encontradas {count} imagens')
            except Exception as e:
                print(f'   ⚠️ Erro ao contar imagens: {e}')
                return {}

            if count == 0:
                print(f'   ❌ Nenhuma imagem encontrada para {start_date} a {end_date}')
                return {}

            # 🔥 PEGA A IMAGEM MAIS RECENTE
            print(f"   🔍 Pegando a imagem mais recente...")
            image = collection.sort('system:time_start', False).first()
            print(f"   ✅ Imagem obtida")

            # 🔥 EXTRAI A DATA DA IMAGEM USADA
            try:
                date_acquired = image.get('DATE_ACQUIRED').getInfo()
                scene_time = image.get('SCENE_CENTER_TIME').getInfo()
                scene_time = scene_time.split('.')[0]
                image_datetime = f"{date_acquired}T{scene_time}Z"
                print(f'   📸 Data e hora da captura: {image_datetime}')

            except Exception as e:
                print(f'   ⚠️ Erro ao extrair data/hora: {e}')
                try:
                    timestamp = image.get('system:time_start').getInfo()
                    image_datetime = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime(
                        '%Y-%m-%dT%H:%M:%SZ')
                    print(f'   📸 Data e hora (fallback): {image_datetime}')
                except:
                    image_datetime = start_date
                    print(f'   📸 Data e hora: {image_datetime} (fallback)')

            # 🔥 CALCULA LST
            print(f"   🔍 Calculando LST...")
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
            print(f'   🌡️ LST do parque: {park_lst_celsius}°C')

            # 🔥 CALCULA BUFFERS (DINÂMICOS)
            print(f"   🔍 Calculando {num_buffers} buffers...")
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

                print(f'   📊 Buffer {i + 1}: {dist}m, {len(temps)} pixels')

            # 🔥 ENCONTRA PCI, PCD, PCA
            print(f"   🔍 Calculando PCI, PCD, PCA...")
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

            print(f'   ❄️ PCI: {pci}°C, PCD: {pcd}m, PCA: {pca_ha}ha')

            # 🔥 RETORNA COM A DATA DA LEITURA
            result = {
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

            print(f"   ✅ RESULTADO FINAL:")
            print(f"      image_date: {result['image_date']}")
            print(f"      park_lst: {result['park_lst']['celsius']}°C")
            print(f"      pci: {result['pci']}")
            print(f"      pcd: {result['pcd']}")
            print(f"      pca: {result['pca']['ha']}ha")

            return result

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
