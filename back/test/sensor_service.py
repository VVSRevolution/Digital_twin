# services/sensor_service.py
import csv
import os

from datetime import datetime
from typing import Dict, Optional

from geoalchemy2 import WKTElement
from shapely.geometry import Point
from extensions import db
from models.sensor import Sensor, TemperatureReading


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
        """Importa sensores de um CSV genérico."""
        try:
            imported = 0
            updated = 0

            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    name = row.get(mapping.get('name', ''), '').strip()
                    if not name:
                        continue

                    lat = float(row.get(mapping.get('latitude', ''), 0))
                    lon = float(row.get(mapping.get('longitude', ''), 0))

                    altitude = None
                    if mapping.get('altitude'):
                        alt_val = row.get(mapping.get('altitude', ''), '').strip()
                        if alt_val:
                            altitude = float(alt_val)

                    description_parts = []
                    mapped_cols = list(mapping.values())

                    for col, value in row.items():
                        if col not in mapped_cols and value and value.strip():
                            description_parts.append(f"{col}: {value.strip()}")

                    description = ' | '.join(description_parts) if description_parts else None

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
            print(f"❌ Erro: {e}", flush=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def import_temperatures(csv_path: str, sensor_id_mapping=None) -> dict:
        """
        Importa temperaturas de um CSV.

        Carrega sensores e leituras existentes uma única vez, compara
        todos os CSV em memória e só faz INSERT/COMMIT depois de terminar
        toda a comparação.
        """
        try:
            if sensor_id_mapping is None:
                sensor_id_mapping = {}

            print("🔎 Carregando sensores do banco...", flush=True)
            sensors = {sensor.name: sensor.id for sensor in Sensor.query.all()}
            print(f"✅ {len(sensors):,} sensores carregados.", flush=True)

            print("🔎 Carregando histórico de temperaturas existente...", flush=True)
            existing_readings = {
                (reading.sensor_id, reading.timestamp)
                for reading in TemperatureReading.query.all()
            }
            print(f"✅ {len(existing_readings):,} leituras existentes carregadas.", flush=True)

            print(f"📂 Analisando arquivo: {csv_path}", flush=True)

            with open(csv_path, 'r', encoding='utf-8') as file:
                total_rows = max(sum(1 for _ in file) - 1, 0)

            print(f"📊 Total de linhas no CSV: {total_rows:,}", flush=True)

            readings_to_insert = []
            imported = 0
            already_exists = 0
            skipped = 0
            invalid = 0
            processed_rows = 0

            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                sensor_columns = [col for col in reader.fieldnames if col not in ('Time', 'timestamp')]

                print(f"🌡️ Sensores encontrados no CSV: {len(sensor_columns):,}", flush=True)
                print("🔄 Iniciando comparação com o banco...", flush=True)

                for row_number, row in enumerate(reader, start=1):
                    processed_rows += 1

                    if row_number % 1000 == 0 or row_number == total_rows:
                        percentual = (row_number / total_rows * 100) if total_rows else 100
                        print(
                            f"⏳ Processando: {row_number:,}/{total_rows:,} ({percentual:.2f}%) | "
                            f"🆕 novas: {imported:,} | ✓ existentes: {already_exists:,} | ⚠️ ignoradas: {skipped:,}",
                            flush=True
                        )

                    time_str = row.get('Time', row.get('timestamp', '')).strip()
                    if not time_str:
                        invalid += 1
                        continue

                    try:
                        timestamp = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            timestamp = datetime.fromisoformat(time_str)
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

                        key = (sensor_id, timestamp)

                        if key in existing_readings:
                            already_exists += 1
                            continue

                        readings_to_insert.append({
                            'sensor_id': sensor_id,
                            'timestamp': timestamp,
                            'temperature': temperature
                        })
                        existing_readings.add(key)
                        imported += 1

            print("🏁 Comparação do CSV concluída.", flush=True)
            print(f"   📊 Linhas processadas: {processed_rows:,}", flush=True)
            print(f"   🆕 Novas leituras: {imported:,}", flush=True)
            print(f"   ✓ Já existentes: {already_exists:,}", flush=True)
            print(f"   ⚠️ Ignoradas: {skipped:,}", flush=True)
            print(f"   ❌ Inválidas: {invalid:,}", flush=True)

            if readings_to_insert:
                print(f"📥 Inserindo {len(readings_to_insert):,} novas leituras no banco...", flush=True)
                db.session.bulk_insert_mappings(TemperatureReading, readings_to_insert)
            else:
                print("ℹ️ Nenhuma leitura nova para inserir.", flush=True)

            print("💾 Fazendo COMMIT...", flush=True)
            db.session.commit()
            print("✅ COMMIT concluído. Importação finalizada!", flush=True)

            return {
                'success': True,
                'imported': imported,
                'updated': 0,
                'skipped': skipped,
                'already_exists': already_exists,
                'invalid': invalid,
                'total': imported
            }

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro durante importação: {e}", flush=True)
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def get_sensors(limit: int = 100, offset: int = 0) -> Dict:
        try:
            sensors = Sensor.query.order_by(Sensor.name).limit(limit).offset(offset).all()
            total = Sensor.query.count()

            return {
                'success': True,
                'count': len(sensors),
                'total': total,
                'sensors': [s.to_dict() for s in sensors]
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_temperatures(
            sensor_name: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            limit: int = 100
    ) -> Dict:
        try:
            sensor = Sensor.query.filter_by(name=sensor_name).first()
            if not sensor:
                return {'success': False, 'error': 'Sensor não encontrado'}

            query = TemperatureReading.query.filter_by(sensor_id=sensor.id)

            if start_date:
                start = datetime.fromisoformat(start_date)
                query = query.filter(TemperatureReading.timestamp >= start)

            if end_date:
                end = datetime.fromisoformat(end_date)
                query = query.filter(TemperatureReading.timestamp <= end)

            readings = query.order_by(
                TemperatureReading.timestamp.desc()
            ).limit(limit).all()

            return {
                'success': True,
                'sensor': sensor.to_dict(),
                'count': len(readings),
                'readings': [r.to_dict() for r in readings]
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
