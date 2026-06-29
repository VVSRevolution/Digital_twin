from flask import Flask, jsonify
from flask_cors import CORS
import ee
from datetime import datetime
import traceback
import os

app = Flask(__name__)
CORS(app)

PROJECT_ID = 'digital-twin-500823'

# Inicializa o Earth Engine
def init_earth_engine():
    try:
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path and os.path.exists(creds_path):
            print(f'Usando chave: {creds_path}')

        ee.Initialize(project=PROJECT_ID)
        print(f'Earth Engine inicializado com sucesso!')
        print(f'Projeto: {PROJECT_ID}')
        return True
    except Exception as e:
        print(f'Erro ao inicializar Earth Engine: {e}')
        return False

if not init_earth_engine():
    print('Falha na inicializacao. Verifique suas credenciais.')
    exit(1)

# ===== NOVOS ENDPOINTS PARA O SEU ESTUDO =====

@app.route('/park-cooling', methods=['POST'])
def analyze_park_cooling():
    """Analisa o cooling island de um parque específico"""
    try:
        data = request.get_json()
        if not data or 'geometry' not in data:
            return jsonify({'error': 'Geometria do parque é obrigatória'}), 400

        # Converte a geometria do parque (GeoJSON) para ee.Geometry
        geojson = data['geometry']

        # Cria a geometria no Earth Engine
        park_geom = ee.Geometry(geojson)

        # Define os buffers (11 anéis de 90m)
        buffer_distances = [90, 180, 270, 360, 450, 540, 630, 720, 810, 900, 990]

        results = []

        # Para cada buffer, calcula o LST médio
        for i, dist in enumerate(buffer_distances):
            buffer_geom = park_geom.buffer(dist)

            # Remove o buffer anterior (cria anel)
            if i > 0:
                prev_buffer = park_geom.buffer(buffer_distances[i-1])
                buffer_geom = buffer_geom.difference(prev_buffer)

            # Calcula o LST médio no buffer
            lst = calculate_lst_in_geometry(buffer_geom)

            results.append({
                'distance': dist,
                'lst': lst,
                'area': buffer_geom.area().getInfo()
            })

        # Calcula o LST interno do parque
        park_lst = calculate_lst_in_geometry(park_geom)

        # Encontra o primeiro ponto de inflexão (PCI)
        pci, pcd, pca = find_cooling_indicators(results, park_lst)

        return jsonify({
            'success': True,
            'park_lst': park_lst,
            'buffers': results,
            'pci': pci,  # Park Cooling Intensity
            'pcd': pcd,  # Park Cooling Distance
            'pca': pca,  # Park Cooling Area
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f'❌ Erro: {e}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_lst_in_geometry(geometry):
    """Calcula o LST médio em uma geometria"""
    try:
        # Usa a mesma lógica do endpoint /lst
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

def find_cooling_indicators(buffer_results, park_lst):
    """Encontra PCI, PCD e PCA baseado nos buffers"""
    if not buffer_results or park_lst is None:
        return None, None, None

    # PCI = diferença entre o primeiro ponto de inflexão e o parque
    # PCD = distância do primeiro ponto de inflexão
    # PCA = área do buffer no ponto de inflexão

    # Encontra o primeiro ponto onde a variação é < 0.1°C
    pci = None
    pcd = None
    pca = None

    for i in range(1, len(buffer_results)):
        diff = buffer_results[i]['lst'] - buffer_results[i-1]['lst']
        if diff < 0.1:  # Ponto de inflexão
            pci = buffer_results[i-1]['lst'] - park_lst
            pcd = buffer_results[i-1]['distance']
            pca = buffer_results[i-1]['area']
            break

    # Se não encontrou, usa o último buffer
    if pci is None and buffer_results:
        last = buffer_results[-1]
        pci = last['lst'] - park_lst
        pcd = last['distance']
        pca = last['area']

    return pci, pcd, pca

@app.route('/park-lst-timeseries', methods=['POST'])
def get_park_lst_timeseries():
    """Obtém série temporal de LST para um parque"""
    try:
        data = request.get_json()
        if not data or 'geometry' not in data:
            return jsonify({'error': 'Geometria do parque é obrigatória'}), 400

        geojson = data['geometry']
        park_geom = ee.Geometry(geojson)

        # Obtém todas as imagens disponíveis
        collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(park_geom) \
            .filterDate("2017-01-01", "2023-12-31")

        # Função para extrair LST de cada imagem
        def extract_lst(image):
            lst = image.select("ST_B10").multiply(0.00341802).add(149.0)
            mean = lst.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=park_geom,
                scale=30,
                maxPixels=1e9
            )
            return ee.Feature(None, {
                'date': image.date().format('YYYY-MM-dd'),
                'lst': mean.get('ST_B10')
            })

        # Mapeia sobre a coleção
        features = collection.map(extract_lst)

        # Obtém os dados
        result = features.getInfo()

        timeseries = []
        for feature in result['features']:
            props = feature['properties']
            if props.get('lst') is not None:
                timeseries.append({
                    'date': props['date'],
                    'lst': props['lst']
                })

        return jsonify({
            'success': True,
            'timeseries': timeseries,
            'count': len(timeseries),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f'❌ Erro: {e}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/lst', methods=['GET'])
def get_lst():
    try:
        print('Processando LST...')

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
        print(f'Erro: {e}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/lst/stats', methods=['GET'])
def get_lst_stats():
    try:
        print('Processando estatisticas...')

        point = ee.Geometry.Point([-49.2648, -16.6869])

        collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(point) \
            .filterDate("2023-01-01", "2023-12-31")

        def get_temp(image):
            lst = image.select("ST_B10").multiply(0.00341802).add(149.0)
            return lst.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=30,
                maxPixels=1e9
            )

        temps = collection.map(get_temp)

        result = {
            'count': temps.size().getInfo(),
            'mean': temps.reduce(ee.Reducer.mean()).getInfo(),
            'min': temps.reduce(ee.Reducer.min()).getInfo(),
            'max': temps.reduce(ee.Reducer.max()).getInfo()
        }

        stats = {}
        for key in ['mean', 'min', 'max']:
            if result.get(key) and 'ST_B10' in result[key]:
                val = result[key]['ST_B10']
                stats[key] = val
                stats[f'{key}_celsius'] = val - 273.15

        stats['count'] = result.get('count', {}).get('ST_B10', 0)

        return jsonify({
            'success': True,
            'location': 'goiania',
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f'Erro: {e}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'project': PROJECT_ID,
        'method': 'Python Flask',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'Earth Engine API (Python/Flask)',
        'project': PROJECT_ID,
        'endpoints': {
            'health': '/health',
            'lst': '/lst',
            'stats': '/lst/stats'
        }
    })

if __name__ == '__main__':
    print('')
    print('='*50)
    print('Iniciando servidor Python Flask...')
    print(f'Projeto: {PROJECT_ID}')
    print('='*50)
    print('')
    print('Servidor rodando em http://localhost:3001')
    print('')
    print('Endpoints disponiveis:')
    print('   - GET /          (informacoes)')
    print('   - GET /health    (status)')
    print('   - GET /lst       (temperatura LST)')
    print('   - GET /lst/stats (estatisticas)')
    print('')
    print('Teste: http://localhost:3001/lst')
    print('='*50)
    print('')

    app.run(host='0.0.0.0', port=3001, debug=False)
