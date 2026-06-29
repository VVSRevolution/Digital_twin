#!/bin/bash
echo "Iniciando servidor Earth Engine (Python)..."

export GOOGLE_APPLICATION_CREDENTIALS="./digital-twin-500823-f9b35f328839.json"
echo "Variavel configurada"

if ! command -v python3 &> /dev/null; then
    echo "Python nao encontrado."
    exit 1
fi

echo "Python: $(python3 --version)"
pip3 install -r requirements.txt
python3 server.py
