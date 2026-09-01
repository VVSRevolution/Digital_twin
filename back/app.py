# app.py
import traceback
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import Config
from extensions import db, migrate
from models import Park, CoolingAnalysis, SatelliteSource
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
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        is_up_to_date = data.get('isUpToDate', True)

        # 🔥 VALIDA
        if not osm_id and not geometry:
            return jsonify({'error': 'É necessário fornecer osm_id ou geometry'}), 400

        if is_up_to_date and end_date:
            return jsonify({
                'error': 'Quando isUpToDate=true, endDate deve ser null'
            }), 400

        satellites = data.get('satellites', ['Landsat 8'])
        if isinstance(satellites, str):
            satellites = [satellites]
        if not satellites or not isinstance(satellites, list):
            satellites = ['Landsat 8']

        # 🔥 BUSCA OU CRIA PARQUE
        park, geometry = AnalysisService.find_or_create_park(
            geometry, osm_id, name, city, country, park_id, is_up_to_date
        )

        if not park:
            return jsonify({'error': 'Erro ao encontrar ou criar parque'}), 500

        # 🔥 PROCESSAR ANÁLISE
        metadata = {
            'numBuffers': num_buffers,
            'bufferDistance': buffer_distance,
            'satellites': satellites,
            'id': park_id,
            'startDate': data.get('startDate'),
            'endDate': data.get('endDate'),
            'isUpToDate': data.get('isUpToDate', False)
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

# ============================================================
# 🔥 ENDPOINT: DELETAR PARQUE E TODAS AS ANÁLISES
# ============================================================
@app.route('/api/parks/<int:park_id>', methods=['DELETE'])
def delete_park(park_id):
    """Deleta um parque e todas as suas análises"""
    try:
        from models import Park, CoolingAnalysis

        # 🔥 BUSCA O PARQUE
        park = Park.query.get(park_id)
        if not park:
            return jsonify({
                'success': False,
                'error': 'Parque não encontrado'
            }), 404

        park_name = park.name

        # 🔥 DELETA AS ANÁLISES PRIMEIRO
        analyses = CoolingAnalysis.query.filter_by(park_id=park_id).all()
        analysis_count = len(analyses)

        for analysis in analyses:
            db.session.delete(analysis)

        # 🔥 DELETA O PARQUE
        db.session.delete(park)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Parque "{park_name}" e {analysis_count} análises deletados com sucesso',
            'park_id': park_id,
            'park_name': park_name,
            'analyses_deleted': analysis_count
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao deletar parque: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/parks/<int:park_id>/analyses/list', methods=['GET'])
def get_park_analyses(park_id):
    """Retorna lista de análises do parque (apenas metadados, sem buffers)"""
    try:
        # Verifica se o parque existe
        park = Park.query.get(park_id)
        if not park:
            return jsonify({
                'success': False,
                'error': 'Parque não encontrado'
            }), 404

        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 50)  # Limite de segurança

        # Query paginada (mais recentes primeiro)
        pagination = CoolingAnalysis.query.filter_by(park_id=park_id) \
            .order_by(CoolingAnalysis.image_date.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        # Monta resposta com metadados (sem buffers/pixels)
        analyses = []
        for analysis in pagination.items:
            # Busca o nome do satélite
            satellite_name = None
            if analysis.satellite_id:
                satellite = SatelliteSource.query.get(analysis.satellite_id)
                if satellite:
                    satellite_name = satellite.name
            qa_summary = None
            if analysis.qa_pixel:
                qa_summary = {
                    'cloud_coverage_percent': analysis.qa_pixel.get('cloud_coverage_percent'),
                    'clear_pixels_percent': analysis.qa_pixel.get('clear_pixels_percent'),
                    'status': analysis.qa_pixel.get('status')
                }
            analyses.append({
                'analysis_id': analysis.id,
                'park_id': park_id,
                'image_date': analysis.image_date,
                'analyzed_at': analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
                'park_lst_celsius': analysis.park_lst_celsius,
                'park_lst_kelvin': analysis.park_lst_kelvin,
                'pci': analysis.pci,
                'pcd': analysis.pcd,
                'pca_ha': analysis.pca_ha,
                'pca_m2': analysis.pca_m2,
                'num_buffers': analysis.num_buffers,
                'buffer_distance': analysis.buffer_distance,
                'satellite_name': satellite_name,
                'ditto_updated': analysis.ditto_updated,
                'has_buffers': bool(analysis.buffers_data),  # Indica se tem dados
                'qa_summary': qa_summary
            })

        return jsonify({
            'success': True,
            'park_id': park_id,
            'park_name': park.name,
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'total_pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'analyses': analyses
        })

    except Exception as e:
        print(f"❌ Erro: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/parks/<int:park_id>/analyses', methods=['GET'])
def get_latest_analysis_detail(park_id):
    """Retorna o detalhe completo da análise mais recente (com buffers/pixels)"""
    try:
        # Verifica se o parque existe
        park = Park.query.get(park_id)
        if not park:
            return jsonify({
                'success': False,
                'error': 'Parque não encontrado'
            }), 404

        # 🔥 BUSCA A ANÁLISE MAIS RECENTE POR image_date
        analysis = CoolingAnalysis.query.filter_by(park_id=park_id) \
            .order_by(CoolingAnalysis.image_date.desc()) \
            .first()

        if not analysis:
            return jsonify({
                'success': False,
                'error': 'Nenhuma análise encontrada para este parque'
            }), 404

        # Busca o nome do satélite
        satellite_name = None
        if analysis.satellite_id:
            satellite = SatelliteSource.query.get(analysis.satellite_id)
            if satellite:
                satellite_name = satellite.name

        # Parâmetro opcional para limitar buffers
        buffer_limit = request.args.get('buffer_limit', type=int)
        include_stats = request.args.get('include_stats', 'true').lower() == 'true'

        # Prepara buffers
        buffers = analysis.buffers_data or []

        # Aplica limite de buffers se especificado
        if buffer_limit and buffer_limit > 0:
            buffers = buffers[:buffer_limit]

        # Se não quiser estatísticas agregadas
        if not include_stats:
            for buffer in buffers:
                buffer.pop('statistics', None)

        # Calcula total de pixels
        total_pixels = sum(len(b.get('pixels', [])) for b in buffers)

        return jsonify({
            'success': True,
            'analysis_id': analysis.id,
            'park_id': park_id,
            'park_name': park.name,
            'image_date': analysis.image_date,
            'analyzed_at': analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
            'satellite_name': satellite_name,
            'park_lst': {
                'celsius': analysis.park_lst_celsius,
                'kelvin': analysis.park_lst_kelvin
            },
            'pci': analysis.pci,
            'pcd': analysis.pcd,
            'pca': {
                'ha': analysis.pca_ha,
                'm2': analysis.pca_m2
            },
            'num_buffers': analysis.num_buffers,
            'buffer_distance': analysis.buffer_distance,
            'ditto_updated': analysis.ditto_updated,
            'buffers': buffers,
            'total_pixels': total_pixels,
            'qa_pixel': analysis.qa_pixel,
            'st_qa': analysis.st_qa
        })

    except Exception as e:
        print(f"❌ Erro: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================
# 🔥 ENDPOINT: DELETAR TODAS AS ANÁLISES DE UM PARQUE
# ============================================================
@app.route('/api/parks/<int:park_id>/analyses', methods=['DELETE'])
def delete_all_analyses(park_id):
    """Deleta todas as análises de um parque"""
    try:
        from models import Park, CoolingAnalysis

        # 🔥 VERIFICA SE O PARQUE EXISTE
        park = Park.query.get(park_id)
        if not park:
            return jsonify({
                'success': False,
                'error': 'Parque não encontrado'
            }), 404

        # 🔥 BUSCA TODAS AS ANÁLISES
        analyses = CoolingAnalysis.query.filter_by(park_id=park_id).all()
        analysis_count = len(analyses)

        if analysis_count == 0:
            return jsonify({
                'success': True,
                'message': f'Nenhuma análise encontrada para o parque "{park.name}"',
                'park_id': park_id,
                'park_name': park.name,
                'analyses_deleted': 0
            })

        # 🔥 DELETA TODAS
        for analysis in analyses:
            db.session.delete(analysis)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'{analysis_count} análises deletadas do parque "{park.name}"',
            'park_id': park_id,
            'park_name': park.name,
            'analyses_deleted': analysis_count
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao deletar análises: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/parks/<int:park_id>/analyses/<int:analysis_id>', methods=['GET'])
def get_analysis_detail(park_id, analysis_id):
    """Retorna detalhes completos de uma análise específica (com buffers/pixels)"""
    try:
        # Verifica se o parque existe
        park = Park.query.get(park_id)
        if not park:
            return jsonify({
                'success': False,
                'error': 'Parque não encontrado'
            }), 404

        # Busca a análise específica
        analysis = CoolingAnalysis.query.filter_by(
            park_id=park_id,
            id=analysis_id
        ).first()

        if not analysis:
            return jsonify({
                'success': False,
                'error': 'Análise não encontrada'
            }), 404

        # Busca o nome do satélite
        satellite_name = None
        if analysis.satellite_id:
            satellite = SatelliteSource.query.get(analysis.satellite_id)
            if satellite:
                satellite_name = satellite.name

        # Parâmetro opcional para limitar buffers
        buffer_limit = request.args.get('buffer_limit', type=int)
        include_stats = request.args.get('include_stats', 'true').lower() == 'true'

        # Prepara buffers
        buffers = analysis.buffers_data or []

        # Aplica limite de buffers se especificado
        if buffer_limit and buffer_limit > 0:
            buffers = buffers[:buffer_limit]

        # Se não quiser estatísticas agregadas
        if not include_stats:
            for buffer in buffers:
                buffer.pop('statistics', None)

        # Calcula total de pixels
        total_pixels = sum(len(b.get('pixels', [])) for b in buffers)

        return jsonify({
            'success': True,
            'analysis_id': analysis.id,
            'park_id': park_id,
            'park_name': park.name,
            'image_date': analysis.image_date,
            'analyzed_at': analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
            'satellite_name': satellite_name,
            'park_lst': {
                'celsius': analysis.park_lst_celsius,
                'kelvin': analysis.park_lst_kelvin
            },
            'pci': analysis.pci,
            'pcd': analysis.pcd,
            'pca': {
                'ha': analysis.pca_ha,
                'm2': analysis.pca_m2
            },
            'num_buffers': analysis.num_buffers,
            'buffer_distance': analysis.buffer_distance,
            'ditto_updated': analysis.ditto_updated,
            'buffers': buffers,  # Aqui vêm os pixels!
            'total_pixels': total_pixels,
            'qa_pixel': analysis.qa_pixel,
            'st_qa': analysis.st_qa
        })

    except Exception as e:
        print(f"❌ Erro: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# 🔥 ENDPOINT: DELETAR UMA ANÁLISE ESPECÍFICA
# ============================================================
@app.route('/api/parks/<int:park_id>/analyses/<int:analysis_id>', methods=['DELETE'])
def delete_analysis(park_id, analysis_id):
    """Deleta uma análise específica"""
    try:
        from models import Park, CoolingAnalysis

        # 🔥 VERIFICA SE O PARQUE EXISTE
        park = Park.query.get(park_id)
        if not park:
            return jsonify({
                'success': False,
                'error': 'Parque não encontrado'
            }), 404

        # 🔥 BUSCA A ANÁLISE
        analysis = CoolingAnalysis.query.filter_by(
            park_id=park_id,
            id=analysis_id
        ).first()

        if not analysis:
            return jsonify({
                'success': False,
                'error': 'Análise não encontrada'
            }), 404

        # 🔥 DELETA
        db.session.delete(analysis)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Análise {analysis_id} deletada com sucesso',
            'analysis_id': analysis_id,
            'park_id': park_id,
            'park_name': park.name
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao deletar análise: {e}")
        traceback.print_exc()
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
        geometry = data.get('geometry')

        if not query or len(query) < 2:
            return jsonify({'results': []})

        # 🔥 SE TIVER GEOMETRIA, USA ELA DIRETO
        if geometry:
            print(f"📐 Usando geometria manual para: {query}")
            # 🔥 CRIA UM PARQUE COM A GEOMETRIA MANUAL
            park = DatabaseService.save_park(
                name=query,
                country=country or "Brazil",
                geometry=geometry,
                city=city,
                osm_id=osm_id or None,
                osm_type='manual',
                tags={'name': query, 'source': 'manual'}
            )
            return jsonify({
                'success': True,
                'source': 'manual',
                'results': [park.to_dict()]
            })
        if osm_id:
            osm_id = str(osm_id)

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

        # 🔥 IMPORTA DO CAMINHO CORRETO
        from test.sensor_service import SensorService
        result = SensorService.import_all_if_empty()
        print(f"📊 Sensores: {result['sensors']['message']}")
        print(f"📊 Temperaturas: {result['temperatures']['message']}")

    print('')
    print('=' * 50)
    print('🚀 Iniciando servidor Digital Twin (DESENVOLVIMENTO)')
    print(f'📁 Projeto: {Config.PROJECT_ID}')
    print(f'📡 Ditto: {Config.DITTO_URL}')
    print('=' * 50)
    print('')
    print('🔄 Servidor: FLASK (desenvolvimento)')
    print('📝 Auto-reload ATIVADO - modifique e salve que reinicia!')
    print('🧪 Teste: http://localhost:3001/health')
    print('=' * 50)
    print('')



    # 🔥 USA FLASK PARA DESENVOLVIMENTO LOCAL
    app.run(
        host='0.0.0.0',
        port=3001,
        debug=True,
        threaded=True
    )
