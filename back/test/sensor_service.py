# services/sensor_service.py
from __future__ import annotations

import csv
import os
from typing import Dict, Optional, Any
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from geoalchemy2 import WKTElement
from shapely.geometry import Point
from extensions import db
from models.sensor import Sensor, TemperatureReading
from pyproj import Transformer


class SensorService:
    def __init__(self):
        pass

    @staticmethod
    def import_all_if_empty():
        """Importa todos os dados se o banco estiver vazio."""
        from models import Sensor, TemperatureReading

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sensors_csv = os.path.join(base_dir, 'test', 'Aranet_OscarBrousse_EastLondon_SensorLoc.csv')
        temps_csv = os.path.join(base_dir, 'test', 'EastLondon_Temperature_DegC_perSensor_2024-06-20_2025-06-21.csv')

        sensors_exist = Sensor.query.count() > 0

        results = {
            'sensors': {'imported': 0, 'message': ''},
            'temperatures': {'imported': 0, 'message': ''}
        }

        if not sensors_exist:
            print(f"📥 Importando sensores de: {sensors_csv}", flush=True)
            result = SensorService.import_sensors(
                csv_path=sensors_csv,
                mapping={
                    'name': 'SensorID',
                    'latitude': 'Y',
                    'longitude': 'X',
                    'altitude': 'Altitude'
                }
            )
            if result.get('success'):
                results['sensors']['imported'] = result.get('imported', 0)
                results['sensors']['message'] = f"{result.get('imported', 0)} sensores importados"
            else:
                results['sensors']['message'] = f"Erro: {result.get('error')}"
        else:
            results['sensors']['message'] = f"Sensores já existem ({Sensor.query.count()} registros)"

        print(f"📥 Verificando/importando temperaturas de: {temps_csv}", flush=True)
        result = SensorService.import_temperatures(
            csv_path=temps_csv,
            sensor_id_mapping={}
        )

        if result.get('success'):
            results['temperatures']['imported'] = result.get('imported', 0)
            results['temperatures']['message'] = (
                f"{result.get('imported', 0)} novas leituras importadas | "
                f"{result.get('already_exists', 0)} já existiam"
            )
        else:
            results['temperatures']['message'] = f"Erro: {result.get('error')}"

        return results

    @staticmethod
    def import_sensors(csv_path: str, mapping: Dict[str, str]) -> Dict:
        """
        Importa sensores de um CSV genérico
        Converte coordenadas de EPSG:27700 para EPSG:4326
        """
        try:
            imported = 0
            updated = 0

            # 🔥 TRANSFORMADOR: EPSG:27700 (British National Grid) -> EPSG:4326 (WGS84)
            transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    name = row.get(mapping.get('name', '')).strip()
                    if not name:
                        continue

                    # 🔥 COORDENADAS ORIGINAIS (EPSG:27700 - metros)
                    x = float(row.get(mapping.get('longitude', ''), 0))  # Easting
                    y = float(row.get(mapping.get('latitude', ''), 0))   # Northing

                    # 🔥 CONVERTE PARA EPSG:4326 (graus)
                    lon, lat = transformer.transform(x, y)

                    altitude = None
                    if mapping.get('altitude'):
                        alt_val = row.get(mapping.get('altitude', ''), '').strip()
                        if alt_val:
                            altitude = float(alt_val)

                    # 🔥 DESCRIÇÃO: JUNTA TUDO QUE NÃO FOI MAPEADO
                    description_parts = []
                    mapped_cols = list(mapping.values())
                    for col, value in row.items():
                        if col not in mapped_cols:
                            if value and value.strip():
                                description_parts.append(f"{col}: {value.strip()}")

                    description = ' | '.join(description_parts) if description_parts else None

                    # 🔥 CRIA OU ATUALIZA
                    sensor = Sensor.query.filter_by(name=name).first()

                    if sensor:
                        sensor.latitude = lat
                        sensor.longitude = lon
                        sensor.altitude = altitude
                        sensor.description = description
                        sensor.geometry = WKTElement(Point(lon, lat).wkt, srid=4326)
                        sensor.updated_at = datetime.utcnow()
                        updated += 1
                    else:
                        sensor = Sensor(
                            name=name,
                            latitude=lat,
                            longitude=lon,
                            altitude=altitude,
                            description=description,
                            geometry=WKTElement(Point(lon, lat).wkt, srid=4326)
                        )
                        db.session.add(sensor)
                        imported += 1

            db.session.commit()

            return {
                'success': True,
                'imported': imported,
                'updated': updated,
                'total': imported + updated
            }

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro: {e}")
            return {'success': False, 'error': str(e)}


    @staticmethod
    def import_temperatures(csv_path: str, sensor_id_mapping=None) -> dict:
        """
        Importa temperaturas de um CSV.
        Só importa se não houver dados no banco.
        """
        try:
            import pytz

            # 🔥 VERIFICA SE JÁ TEM DADOS
            existing_count = TemperatureReading.query.count()
            if existing_count > 0:
                print(f"✅ Já existem {existing_count:,} leituras no banco. Pulando importação.", flush=True)
                return {
                    'success': True,
                    'imported': 0,
                    'updated': 0,
                    'skipped': 0,
                    'already_exists': existing_count,
                    'invalid': 0,
                    'total': existing_count,
                    'message': f'Já existem {existing_count:,} leituras no banco'
                }

            if sensor_id_mapping is None:
                sensor_id_mapping = {}

            # 🔥 TIMEZONE DE LONDRES (UK)
            london_tz = pytz.timezone('Europe/London')

            # 🔥 1. CARREGA SENSORES UMA VEZ
            print("🔎 Carregando sensores do banco...", flush=True)
            sensors = {sensor.name: sensor.id for sensor in Sensor.query.all()}
            print(f"✅ {len(sensors):,} sensores carregados.", flush=True)

            print(f"📂 Analisando arquivo: {csv_path}", flush=True)

            with open(csv_path, 'r', encoding='utf-8') as file:
                total_rows = max(sum(1 for _ in file) - 1, 0)

            print(f"📊 Total de linhas no CSV: {total_rows:,}", flush=True)

            readings_to_insert = []
            imported = 0
            skipped = 0
            invalid = 0
            processed_rows = 0
            insert_batch_size = 1000

            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                sensor_columns = [col for col in reader.fieldnames if col not in ('Time', 'timestamp')]

                print(f"🌡️ Sensores encontrados no CSV: {len(sensor_columns):,}", flush=True)
                print("🔄 Iniciando processamento em memória...", flush=True)

                for row_number, row in enumerate(reader, start=1):
                    processed_rows += 1

                    if row_number % 1000 == 0 or row_number == total_rows:
                        percentual = (row_number / total_rows * 100) if total_rows else 100
                        print(
                            f"⏳ Processando: {row_number:,}/{total_rows:,} ({percentual:.2f}%) | "
                            f"🆕 novas: {imported:,}",
                            flush=True
                        )

                    time_str = row.get('Time', row.get('timestamp', '')).strip()
                    if not time_str:
                        invalid += 1
                        continue

                    try:
                        naive_datetime = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                        local_datetime = london_tz.localize(naive_datetime)
                        timestamp_utc = local_datetime.astimezone(pytz.UTC)
                    except ValueError:
                        try:
                            naive_datetime = datetime.fromisoformat(time_str)
                            local_datetime = london_tz.localize(naive_datetime)
                            timestamp_utc = local_datetime.astimezone(pytz.UTC)
                        except ValueError:
                            invalid += 1
                            continue

                    for col in sensor_columns:
                        temp_str = row.get(col, '').strip()
                        if not temp_str:
                            continue

                        try:
                            temperature = float(temp_str)
                        except ValueError:
                            invalid += 1
                            continue

                        sensor_name = sensor_id_mapping.get(col, col)
                        sensor_id = sensors.get(sensor_name)

                        if sensor_id is None:
                            skipped += 1
                            continue

                        readings_to_insert.append({
                            'sensor_id': sensor_id,
                            'timestamp': timestamp_utc,
                            'temperature': temperature
                        })
                        imported += 1

                        # 🔥 INSERE EM LOTE
                        if len(readings_to_insert) >= insert_batch_size:
                            db.session.bulk_insert_mappings(TemperatureReading, readings_to_insert)
                            db.session.commit()
                            print(f"💾 Inseridas {imported:,} leituras...", flush=True)
                            readings_to_insert = []

            # 🔥 INSERE O RESTANTE
            if readings_to_insert:
                db.session.bulk_insert_mappings(TemperatureReading, readings_to_insert)
                db.session.commit()

            print("🏁 Importação concluída!", flush=True)
            print(f"   📊 Linhas processadas: {processed_rows:,}", flush=True)
            print(f"   🆕 Novas leituras: {imported:,}", flush=True)

            return {
                'success': True,
                'imported': imported,
                'updated': 0,
                'skipped': skipped,
                'already_exists': 0,
                'invalid': invalid,
                'total': imported
            }

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro durante importação: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

