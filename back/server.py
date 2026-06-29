import ee
import json
import os
import traceback
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite todas as origens (para desenvolvimento)

PROJECT_ID = 'digital-twin-500823'


# Inicializa o Earth Engine
def init_earth_engine():
    try:
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path and os.path.exists(creds_path):
            print(f'📁 Usando chave: {creds_path}')

        ee.Initialize(project=PROJECT_ID)
        print(f'✅ Earth Engine inicializado com sucesso!')
        print(f'📁 Projeto: {PROJECT_ID}')
        return True
    except Exception as e:
        print(f'❌ Erro ao inicializar Earth Engine: {e}')
        return False


if not init_earth_engine():
    print('💥 Falha na inicializacao. Verifique suas credenciais.')
    exit(1)


# ===== FUNÇÃO AUXILIAR =====
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
        print(f'Erro ao calcular LST: {e}')
        return None


# ===== ENDPOINT: PARK COOLING =====
@app.route('/park-cooling', methods=['POST'])
def analyze_park_cooling():
    """Analisa o cooling island de um parque específico"""
    try:
        data = request.get_json()
        if not data or 'geometry' not in data:
            return jsonify({'error': 'Geometria do parque é obrigatória'}), 400

        geojson = data['geometry']
        park_geom = ee.Geometry(geojson)

        # 🔥 OBTÉM A IMAGEM LANDSAT
        image = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(park_geom) \
            .filterDate("2023-01-01", "2023-12-31") \
            .median()

        # 🔥 CALCULA LST
        lst_raw = image.select("ST_B10")
        lst_kelvin = lst_raw.multiply(0.00341802).add(149.0)
        lst_celsius = lst_kelvin.subtract(273.15)

        # 🔥 DEFINE OS BUFFERS
        buffer_distances = [90, 180, 270, 360, 450, 540, 630, 720, 810, 900, 990]

        results = []

        for i, dist in enumerate(buffer_distances):
            buffer_geom = park_geom.buffer(dist)

            # Remove o buffer anterior (cria anel)
            if i > 0:
                prev_buffer = park_geom.buffer(buffer_distances[i - 1])
                buffer_geom = buffer_geom.difference(prev_buffer)

            # 🔥 EXTRAI OS PIXELS DE LST DENTRO DO BUFFER
            # Amostra a imagem para obter todos os pixels
            sampled = lst_celsius.sampleRegions(
                collection=ee.FeatureCollection([ee.Feature(buffer_geom)]),
                scale=30,
                geometries=True
            )

            # Obtém os dados
            pixels = sampled.getInfo()

            # 🔥 EXTRAI AS TEMPERATURAS DE CADA PIXEL
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

            # 🔥 CALCULA ESTATÍSTICAS DO BUFFER
            temps = [p['temperature'] for p in pixel_temps if p['temperature'] is not None]

            results.append({
                'distance': dist,
                'distance_prev': buffer_distances[i - 1] if i > 0 else 0,
                'buffer_index': i + 1,
                'pixels': pixel_temps,  # 🔥 TODOS OS PIXELS COM TEMPERATURA
                'statistics': {
                    'count': len(temps),
                    'mean': sum(temps) / len(temps) if temps else None,
                    'min': min(temps) if temps else None,
                    'max': max(temps) if temps else None,
                    'std': calculate_std(temps) if temps else None
                },
                'area_ha': buffer_geom.area().getInfo() / 10000
            })

        # 🔥 CALCULA LST DO PARQUE (MÉDIA)
        park_lst = lst_celsius.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=park_geom,
            scale=30,
            maxPixels=1e9
        ).getInfo()

        park_lst_celsius = park_lst.get('ST_B10')

        # 🔥 ENCONTRA PCI, PCD, PCA
        pci = None
        pcd = None
        pca_ha = None

        for i in range(1, len(results)):
            prev_mean = results[i - 1]['statistics']['mean']
            curr_mean = results[i]['statistics']['mean']
            if prev_mean is not None and curr_mean is not None:
                diff = curr_mean - prev_mean
                if diff < 0.1:
                    if park_lst_celsius is not None:
                        pci = prev_mean - park_lst_celsius
                    pcd = results[i - 1]['distance']
                    pca_ha = results[i - 1]['area_ha']
                    break

        if pci is None and results:
            last = results[-1]
            if last['statistics']['mean'] is not None and park_lst_celsius is not None:
                pci = last['statistics']['mean'] - park_lst_celsius
                pcd = last['distance']
                pca_ha = last['area_ha']

        return jsonify({
            'success': True,
            'park_lst': {
                'kelvin': park_lst_celsius + 273.15 if park_lst_celsius is not None else None,
                'celsius': park_lst_celsius
            },
            'buffers': results,  # 🔥 CADA BUFFER TEM TODOS OS PIXELS
            'pci': pci,
            'pcd': pcd,
            'pca': {
                'ha': pca_ha,
                'm2': pca_ha * 10000 if pca_ha else None
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f'❌ Erro: {e}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


def calculate_std(values):
    """Calcula o desvio padrão de uma lista de valores"""
    if not values or len(values) < 2:
        return None
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


# ===== ENDPOINT: LST =====
@app.route('/lst', methods=['GET'])
def get_lst():
    try:
        print('🌡️ Processando LST...')

        point = ee.Geometry.Point([-49.2648, -16.6869])

        image = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(point) \
            .filterDate("2023-01-01", "2023-12-31") \
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

        return jsonify({
            'success': True,
            'source': 'landsat-8',
            'location': 'goiania',
            'coordinates': [-49.2648, -16.6869],
            'kelvin': kelvin,
            'celsius': kelvin - 273.15 if kelvin else None,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f'❌ Erro: {e}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== ENDPOINT: HEALTH =====
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'project': PROJECT_ID,
        'method': 'Python Flask',
        'timestamp': datetime.now().isoformat()
    })


# ===== ENDPOINT: ROOT =====
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'Earth Engine API (Python/Flask)',
        'project': PROJECT_ID,
        'endpoints': {
            'health': '/health',
            'lst': '/lst',
            'park-cooling': '/park-cooling (POST)'
        }
    })


# ===== INICIA SERVIDOR =====
if __name__ == '__main__':
    print('')
    print('=' * 50)
    print('🚀 Iniciando servidor Python Flask...')
    print(f'📁 Projeto: {PROJECT_ID}')
    print('=' * 50)
    print('')
    print('✅ Servidor rodando em http://localhost:3001')
    print('')
    print('📡 Endpoints disponiveis:')
    print('   - GET /              (informacoes)')
    print('   - GET /health        (status)')
    print('   - GET /lst           (temperatura LST)')
    print('   - POST /park-cooling (analise de cooling island)')
    print('')
    print('🧪 Teste: http://localhost:3001/lst')
    print('=' * 50)
    print('')

    app.run(host='0.0.0.0', port=3001, debug=True)
