# Digital Twin - Backend

Sistema de gerenciamento de ilhas de calor e análise de parques urbanos.

## 🚀 Tecnologias

- Python 3.12.3
- Flask 2.3.3
- PostgreSQL + PostGIS
- Google Earth Engine
- GeoAlchemy2, Shapely, PyProj

## 📋 Pré-requisitos

- Python 3.12 ou superior
- pip 26.2.1 ou superior
- PostgreSQL com extensão PostGIS
- Conta do Google Earth Engine (para autenticação)

## 🔧 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/VVSRevolution/Digital_twin
cd Digital_twin/back
```
### 2. Crie e ative o ambiente virtual
Windows (PowerShell):

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/Mac:

```bash
python3 -m venv venv
source venv/bin/activate
```
### 3. Atualize o pip para a versão 26.2.1

```bash
python -m pip install --upgrade pip==26.2.1
```
### 4. Instale as dependências
```bash
pip install -r requirements.txt
```
### 5. Inicie o servidor

```bash
python app.py
```
## Dependências
```
# 🔥 WEB FRAMEWORK
Flask==2.3.3
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5

# 🔥 BANCO DE DADOS
psycopg2-binary==2.9.9
GeoAlchemy2==0.20.0
SQLAlchemy==2.0.51

# 🔥 GEOPROCESSAMENTO (NECESSÁRIO!)
Shapely==2.1.2
pyproj==3.7.2
numpy==2.5.1

# 🔥 GOOGLE EARTH ENGINE
earthengine-api==0.1.376
google-auth==2.23.4
google-auth-oauthlib==1.1.0

# 🔥 VALIDAÇÃO E CONFIGURAÇÃO
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0

# 🔥 REQUISIÇÕES
requests==2.34.0
httpx==0.25.2

# 🔥 UTILITÁRIOS
python-dateutil==2.8.2
geojson==3.3.0

# 🔥 (Opcional) Para melhor performance
geographiclib==2.0
```
# 📁 ESTRUTURA DO BACKEND - DIGITAL TWIN
``` text
back/
├── app.py # 🔥 PONTO DE ENTRADA (Flask)
├── config.py # ⚙️ CONFIGURAÇÕES (URLs, chaves, variáveis)
├── extensions.py # 🔌 EXTENSÕES (db, migrate, cors)
├── requirements.txt # 📦 DEPENDÊNCIAS
├── .env # 🔐 VARIÁVEIS DE AMBIENTE
│
├── database/ # 🗄️ SCRIPTS SQL
│ ├── init.sql # Estrutura inicial do banco
│ └── seeds/ # Dados iniciais
│ └── satellites.sql # Satélites padrão
│
├── models/ # 🧠 MODELOS DE DADOS
│ ├── init.py
│ ├── satellite_source.py # 🛰️ Satélites (LANDSAT, Sentinel, etc)
│ ├── park.py # 🌳 Parques (geometria, nome, cidade)
│ └── analysis.py # 📊 Análises (PCI, PCD, PCA, LST)
│
├── services/ # 📦 SERVIÇOS (LÓGICA DE NEGÓCIO)
│ ├── init.py
│ ├── park_service.py # 🌍 Busca parques no Overpass/Nominatim
│ ├── earth_engine_service.py # 🛰️ Cálculos de LST e buffers (Google Earth Engine)
│ ├── ditto_service.py # 📡 Comunicação com Eclipse Ditto (gêmeo digital)
│ └── database_service.py # 💾 Operações no banco (salvar, buscar, popular)
│
├── utils/ # 🛠️ UTILITÁRIOS
│ ├── init.py
│ └── validators.py # ✅ Validação de dados
│
└── migrations/ # 📂 MIGRAÇÕES (gerado automaticamente)
└── versions/ # Arquivos de migração do Alembic
```

---

## 📋 DESCRIÇÃO DOS ARQUIVOS

| Arquivo/Pasta       | Função                                                                              |
|---------------------|-------------------------------------------------------------------------------------|
| **`app.py`**        | Ponto de entrada do servidor. Inicializa Flask, rotas, banco, Earth Engine e Ditto. |
| **`config.py`**     | Configurações: URL do banco, chaves do Earth Engine, URL do Ditto, etc.             |
| **`extensions.py`** | Instâncias do SQLAlchemy (`db`), Migrate (`migrate`) e CORS (`cors`).               |
| **`models/`**       | Definição das tabelas do banco de dados (SQLAlchemy).                               |
| **`services/`**     | Lógica de negócio: busca parques, calcula LST, comunica com Ditto, salva no banco.  |
| **`database/`**     | Scripts SQL para estrutura inicial e dados de seed.                                 |
| **`utils/`**        | Funções auxiliares (validação, formatação, etc).                                    |
| **`migrations/`**   | Controle de versão do banco (gerado pelo Alembic).                                  |

---

## 🔥 FLUXO DE DADOS
``` text
Frontend → POST /api/park/analyze
↓

app.py (recebe requisição)
↓

park_service.py (busca dados do parque no OSM)
↓

earth_engine_service.py (calcula LST e buffers)
↓

database_service.py (salva parque e análise no PostGIS)
↓

ditto_service.py (atualiza gêmeo digital)
↓

app.py → Retorna resultado para o Frontend

```

---

## 🗄️ TABELAS DO BANCO

| Tabela                  | Descrição                                         |
|-------------------------|---------------------------------------------------|
| **`satellite_sources`** | Satélites disponíveis (LANDSAT_8, LANDSAT_9, etc) |
| **`parks`**             | Parques cadastrados (nome, cidade, geometria)     |
| **`cooling_analyses`**  | Análises de cooling island (PCI, PCD, PCA, LST)   |

---

## 🔗 RELACIONAMENTOS
```text
satellite_sources (1) ────── (N) cooling_analyses
parks (1) ────────────────── (N) cooling_analyses
```


---

