# app.py
import traceback
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import Config
from extensions import db, migrate
from services.database_service import DatabaseService
from services.ditto_service import DittoService
from services.earth_engine_service import EarthEngineService
from services.park_service import ParkService

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

        # 🔥 PEGAR SATELLITES CORRETAMENTE
        satellites = data.get('satellites', ['Landsat 8'])
        # Se for string, converter para lista
        if isinstance(satellites, str):
            satellites = [satellites]
        # Se for None ou vazio, usar padrão
        if not satellites or not isinstance(satellites, list):
            satellites = ['Landsat 8']

        is_up_to_date = data.get('isUpToDate', True)

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

        # 🔥 2. SALVA NO BANCO (USANDO O SERVIÇO)
        from services.database_service import DatabaseService

        # Salvar parque
        park = DatabaseService.save_park(
            name=name,
            city=city,
            country=country,
            geometry=geometry,
            tags={'source': 'api', 'park_id': park_id}
        )

        # Salvar análise
        satellite_name = satellites[0] if satellites and isinstance(satellites, list) else 'Landsat 8'
        print(f"🛰️ Usando satélite: {satellite_name}")
        analysis = DatabaseService.save_analysis(
            park_id=park.id,
            satellite_name=satellite_name,
            image_date=result.get('image_date'),
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
            ditto_updated=False
        )

        # 🔥 3. ATUALIZA O DITTO
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

        # Atualizar status do Ditto no banco
        if ditto_success:
            DatabaseService.update_ditto_status(analysis.id, True)

        db.session.commit()

        # 🔥 4. RETORNA
        return jsonify({
            'success': True,
            'park_id': park.id,
            'analysis_id': analysis.id,
            'park_lst': result['park_lst'],
            'pci': result['pci'],
            'pcd': result['pcd'],
            'pca': result['pca'],
            'buffers': result['buffers'],
            'image_date': result.get('image_date'),
            'ditto_updated': ditto_success,
            'timestamp': datetime.now().isoformat()
        })

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
