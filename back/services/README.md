# 📍 ORDEM DE CHAMADA - ENDPOINT /api/park/analyze

## 1. ENDPOINT PRINCIPAL

**Arquivo:** `app.py`
**Função:** `analyze_park()`
**Rota:** `@app.route('/api/park/analyze', methods=['POST'])`

---

## 2. BUSCA/CRIA PARQUE

**Arquivo:** `services/analysis_service.py`
**Função:** `AnalysisService.find_or_create_park()`

**O que faz:**

- Busca parque por OSM_ID
- Se não achar, busca por geometria igual
- Se não achar, cria novo

**Chama:**

- `Park.query.filter_by(osm_id=...).first()`
- `shape(geometry)` para comparação
- `DatabaseService.save_park()` (se não existir)

---

## 3. PROCESSAR ANÁLISE

**Arquivo:** `services/analysis_service.py`
**Função:** `AnalysisService.process_analysis()`

### 3.1 LISTA DATAS DAS IMAGENS

**Arquivo:** `services/earth_engine_service.py`
**Função:** `EarthEngineService.list_image_datetimes()`

**O que faz:**

- Busca coleção do satélite
- Filtra por bounds e data
- Retorna lista de datetimes das imagens

**Chama:**

- `EarthEngineService.get_satellite_collection()`
- `collection.filterBounds()`
- `collection.filterDate()`
- `collection.aggregate_array('system:time_start')`

**Retorna:** `Lista de datetimes: ['2026-07-08T13:20:18Z', ...]`

---

### 3.2 CALCULA LST PARA CADA IMAGEM

**Arquivo:** `services/earth_engine_service.py`
**Função:** `EarthEngineService.calculate_lst()`

**O que faz:**

- Filtra imagem específica
- Calcula LST
- Calcula buffers
- Calcula PCI, PCD, PCA

**Chama:**

- `EarthEngineService.get_satellite_collection()`
- `collection.filterBounds()`
- `collection.filterDate()` com data específica
- `collection.sort().first()` (pega a imagem)

**Retorna:** Resultado da análise

---

### 3.3 SALVA ANÁLISE NO BANCO

**Arquivo:** `services/database_service.py`
**Função:** `DatabaseService.save_analysis()`

**O que faz:**

- Busca satellite_id pelo nome
- Cria objeto CoolingAnalysis
- Salva no banco

**Chama:**

- `SatelliteSource.query.filter_by(name=...).first()`
- `db.session.add()`
- `db.session.flush()`

**Retorna:** Analysis salvo

---

### 3.4 ATUALIZA DITTO (OPCIONAL)

**Arquivo:** `services/ditto_service.py`
**Função:** `DittoService.update_park_twin()`

---

## 4. RETORNA RESULTADO

**Arquivo:** `app.py`
**Função:** `analyze_park() -> jsonify(result)`

---

# 📋 DIAGRAMA DE FLUXO

┌─────────────────────────────────────────────────────────────────┐
│ @app.route('/api/park/analyze') │
│ analyze_park() │
└─────────────────────┬───────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ AnalysisService.find_or_create_park() │
│ ├── Busca por OSM_ID │
│ ├── Busca por geometria igual │
│ └── Cria novo se não encontrar │
└─────────────────────┬───────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ AnalysisService.process_analysis() │
│ │
│ ├── 1. EarthEngineService.list_image_datetimes() │
│ │ └── Retorna: ['2026-07-08T13:20:18Z', ...] │
│ │ │
│ ├── 2. Para cada datetime: │
│ │ └── EarthEngineService.calculate_lst() │
│ │ ├── Filtra imagem específica │
│ │ ├── Calcula LST │
│ │ ├── Calcula buffers │
│ │ ├── Calcula PCI, PCD, PCA │
│ │ └── Retorna resultado │
│ │ │
│ └── 3. DatabaseService.save_analysis() │
│ └── Salva no banco │
└─────────────────────┬───────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ Return: jsonify(result) │
└─────────────────────────────────────────────────────────────────┘


---

# 📂 FUNÇÕES AUXILIARES

| Ordem | Função                       | Arquivo                 | O que faz                                  |
|-------|------------------------------|-------------------------|--------------------------------------------|
| 1     | `get_satellite_collection()` | earth_engine_service.py | Busca coleção do satélite no banco         |
| 2     | `get_latest_single_date()`   | earth_engine_service.py | Pega data mais recente (se não tiver data) |
| 3     | `_calculate_std()`           | earth_engine_service.py | Calcula desvio padrão dos pixels           |
| 4     | `save_park()`                | database_service.py     | Salva parque (se novo)                     |
| 5     | `save_analysis()`            | database_service.py     | Salva análise                              |
| 6     | `update_park_twin()`         | ditto_service.py        | Atualiza Ditto (se ativo)                  |

---

