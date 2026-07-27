# app.py
import traceback
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import Config
from extensions import db, migrate
from services.analysis_service import AnalysisService
from services.database_service import DatabaseService
from services.earth_engine_service import EarthEngineService
from services.park_search_service import ParkSearchService

# 🔥 INICIALIZAÇÃO
app = Flask(__name__)

app.config.from_object(Config)
db.init_app(app)
migrate.init_app(app, db)
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
        osm_id = data.get('osm_id')
        park_id = data.get('id', 'unknown')
        name = data.get('name', '')
        city = data.get('city', '')
        country = data.get('country', 'BR')
        num_buffers = data.get('numBuffers', 11)
        buffer_distance = data.get('bufferDistance', 90)

        # 🔥 VALIDA
        if not osm_id and not geometry:
            return jsonify({'error': 'É necessário fornecer osm_id ou geometry'}), 400

        satellites = data.get('satellites', ['Landsat 8'])
        if isinstance(satellites, str):
            satellites = [satellites]
        if not satellites or not isinstance(satellites, list):
            satellites = ['Landsat 8']

        # 🔥 BUSCA OU CRIA PARQUE
        park, geometry = AnalysisService.find_or_create_park(
            geometry, osm_id, name, city, country, park_id
        )

        if not park:
            return jsonify({'error': 'Erro ao encontrar ou criar parque'}), 500

        # 🔥 PROCESSAR ANÁLISE
        metadata = {
            'numBuffers': num_buffers,
            'bufferDistance': buffer_distance,
            'satellites': satellites,
            'id': park_id
        }

        result = AnalysisService.process_analysis(park, geometry, metadata)

        if not result:
            return jsonify({'error': 'Falha no cálculo LST'}), 500

        return jsonify(result)

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================
# 🔥 ENDPOINT: COMPATIBILIDADE COM O FRONTEND ANTIGO
# ============================================================
@app.route('/park-cooling', methods=['POST'])
def park_cooling():
    """Mantém compatibilidade com o frontend antigo"""
    return analyze_park()


@app.route('/api/satellites', methods=['GET'])
def get_satellites():
    """Retorna a lista de satélites disponíveis do banco"""
    try:
        from models import SatelliteSource

        # Buscar do banco
        satellites = SatelliteSource.query.filter_by(active=True).all()

        return jsonify({
            'success': True,
            'count': len(satellites),
            'satellites': [s.to_dict() for s in satellites]
        })

    except Exception as e:
        print(f"❌ Erro ao listar satélites: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/parks', methods=['GET'])
def get_parks():
    """Retorna a lista de parques disponíveis no banco"""
    try:
        from models import Park

        # Buscar todos os parques
        parks = Park.query.order_by(Park.name).all()

        return jsonify({
            'success': True,
            'count': len(parks),
            'parks': [p.to_dict() for p in parks]
        })

    except Exception as e:
        print(f"❌ Erro ao listar parques: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# 🔥 ENDPOINT: DETALHES DE UM PARQUE
# ============================================================
@app.route('/api/parks/<int:park_id>', methods=['GET'])
def get_park_detail(park_id):
    """Retorna detalhes de um parque específico"""
    try:
        from models import Park

        park = Park.query.get(park_id)
        if not park:
            return jsonify({
                'success': False,
                'error': 'Parque não encontrado'
            }), 404

        return jsonify({
            'success': True,
            'park': park.to_dict()
        })

    except Exception as e:
        print(f"❌ Erro ao buscar parque: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/parks/<int:park_id>/analyses', methods=['GET'])
def get_park_analyses(park_id):
    """Retorna todas as análises de um parque"""
    try:
        from models import Park, CoolingAnalysis

        park = Park.query.get(park_id)
        if not park:
            return jsonify({
                'success': False,
                'error': 'Parque não encontrado'
            }), 404

        analyses = CoolingAnalysis.query.filter_by(park_id=park_id) \
            .order_by(CoolingAnalysis.analyzed_at.desc()) \
            .all()

        return jsonify({
            'success': True,
            'park_id': park_id,
            'park_name': park.name,
            'count': len(analyses),
            'analyses': [a.to_dict() for a in analyses]
        })

    except Exception as e:
        print(f"❌ Erro ao buscar análises: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/park/search', methods=['POST'])
def search_park():
    try:
        data = request.get_json()
        query = data.get('query', '')
        city = data.get('city', '')
        country = data.get('country', 'Brasil')
        osm_id = data.get('osm_id')

        if osm_id:
            osm_id = str(osm_id)

        if not query or len(query) < 2:
            return jsonify({'results': []})

        result = ParkSearchService.search(query, city, country, osm_id)

        # 🔥 SE TIVER ERRO, RETORNA COM status 500
        if not result.get('success', True):
            return jsonify(result), 500

        return jsonify(result)

    except Exception as e:
        print(f"❌ Erro: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'results': []
        }), 500


# ============================================================
# 🔥 INICIA SERVIDOR
# ============================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Tabelas verificadas/criadas!")
        DatabaseService.seed_satellites()
        print("✅ Satélites populados!")

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
