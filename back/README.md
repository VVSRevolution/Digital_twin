back/
├── server.py                 # 🔥 PONTO DE ENTRADA (Flask)
├── services/
│   ├── __init__.py
│   ├── park_service.py       # Busca parques no Overpass/Nominatim
│   ├── earth_engine_service.py # Cálculos de LST e buffers
│   ├── ditto_service.py      # Comunicação com Eclipse Ditto
│   └── database_service.py   # Salvamento no banco (InfluxDB/PostgreSQL)
├── models/
│   ├── __init__.py
│   └── park.py               # Estrutura de dados do parque
├── utils/
│   ├── __init__.py
│   └── validators.py         # Validação de dados
└── config.py                 # Configurações (URLs, chaves, etc.)