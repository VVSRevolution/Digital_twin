# server.py
import json
import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

from config import Config
from services.ditto_service import DittoService
from services.earth_engine_service import EarthEngineService
from services.park_service import ParkService

# 🔥 INICIALIZAÇÃO
app = Flask(__name__)
CORS(app)

# 🔥 INICIALIZA EARTH ENGINE
if not EarthEngineService.initialize():
    print("💥 Falha ao inicializar Earth Engine")
    exit(1)

# ============================================================
# 🔥 ENDPOINTS
# ============================================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'project': Config.PROJECT_ID,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/park/search', methods=['GET'])
def search_park():
    """Busca parques pelo nome (autocomplete)"""
    query = request.args.get('q', '')
    country = request.args.get('country', 'BR')

    if not query or len(query) < 2:
        return jsonify({'results': []})

    results = ParkService.search_park_by_name(query, country)
    return jsonify({'results': results})

@app.route('/api/park/polygon', methods=['POST'])
def get_park_polygon():
    """Busca o polígono de um parque"""
    data = request.get_json()
    park_name = data.get('name')
    city = data.get('city')

    if not park_name:
        return jsonify({'error': 'Nome do parque é obrigatório'}), 400

    polygon = ParkService.fetch_park_polygon(park_name, city)
    return jsonify({'polygon': polygon})

# ============================================================
# 🔥 ENDPOINT: PARK COOLING (COM DATA DA IMAGEM)
# ============================================================
@app.route('/api/park/analyze', methods=['POST'])
def analyze_park():
    """Analisa o cooling island de um parque"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Corpo da requisição vazio'}), 400

        geometry = data.get('geometry')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        park_id = data.get('id', 'unknown')
        name = data.get('name', '')
        city = data.get('city', '')
        country = data.get('country', 'Brasil')
        num_buffers = data.get('numBuffers', 10)
        buffer_distance = data.get('bufferDistance', 90)

        if not geometry:
            return jsonify({'error': 'Geometria do parque é obrigatória'}), 400

        # 🔥 CALCULA LST
        result = EarthEngineService.calculate_lst(
            geometry=geometry,
            start_date=start_date,
            end_date=end_date,
            num_buffers=num_buffers,
            buffer_distance=buffer_distance
        )

        if not result:
            return jsonify({'error': 'Falha no cálculo LST'}), 500

        # 🔥 ATUALIZA O DITTO
        park_data = {
            'name': name,
            'city': city,
            'country': country,
            'park_lst': result['park_lst']['celsius'],
            'pci': result['pci'],
            'pcd': result['pcd'],
            'pca': result['pca'],
            'buffers': result['buffers'],
            'geometry': geometry
        }

        ditto_success = DittoService.update_park_twin(park_id, park_data)

        # 🔥 RETORNA COM A DATA DA IMAGEM
        return jsonify({
            'success': True,
            'park_lst': result['park_lst'],
            'pci': result['pci'],
            'pcd': result['pcd'],
            'pca': result['pca'],
            'buffers': result['buffers'],
            'image_date': result.get('image_date'),  # 🔥 SÓ ISSO FOI ADICIONADO!
            'ditto_updated': ditto_success,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"❌ Erro: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# 🔥 ENDPOINT: COMPATIBILIDADE COM O FRONTEND ANTIGO
# ============================================================
@app.route('/park-cooling', methods=['POST'])
def park_cooling():
    """Mantém compatibilidade com o frontend antigo"""
    return analyze_park()

# ============================================================
# 🔥 INICIA SERVIDOR
# ============================================================
if __name__ == '__main__':
    print('')
    print('=' * 50)
    print('🚀 Iniciando servidor Digital Twin...')
    print(f'📁 Projeto: {Config.PROJECT_ID}')
    print(f'📡 Ditto: {Config.DITTO_URL}')
    print('=' * 50)
    print('')
    print('📡 Endpoints disponíveis:')
    print('   - GET  /                    (informações)')
    print('   - GET  /health              (status)')
    print('   - GET  /api/park/search     (buscar parques)')
    print('   - POST /api/park/polygon    (buscar polígono)')
    print('   - POST /api/park/analyze    (analisar cooling island)')
    print('   - POST /park-cooling        (compatibilidade)')
    print('')
    print('🧪 Teste: http://localhost:3001/health')
    print('=' * 50)
    print('')

    app.run(host='0.0.0.0', port=3001, debug=True)