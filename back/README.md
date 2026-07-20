# 📁 ESTRUTURA DO BACKEND - DIGITAL TWIN

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

text

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

text

---

## 🗄️ TABELAS DO BANCO

| Tabela                  | Descrição                                         |
|-------------------------|---------------------------------------------------|
| **`satellite_sources`** | Satélites disponíveis (LANDSAT_8, LANDSAT_9, etc) |
| **`parks`**             | Parques cadastrados (nome, cidade, geometria)     |
| **`cooling_analyses`**  | Análises de cooling island (PCI, PCD, PCA, LST)   |

---

## 🔗 RELACIONAMENTOS

satellite_sources (1) ────── (N) cooling_analyses
parks (1) ────────────────── (N) cooling_analyses

text

---

**Backend organizado e pronto para crescer!** 🚀
