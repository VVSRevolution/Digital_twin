# run.ps1 - Script para iniciar o servidor Python
Write-Host "Iniciando servidor Earth Engine (Python)..." -ForegroundColor Cyan

# Configura a variavel de ambiente
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\Users\vinic\WebstormProjects\Digital_twin\back\credentials.json"
Write-Host "Variavel configurada" -ForegroundColor Green

# Verifica Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python nao encontrado. Instale o Python primeiro." -ForegroundColor Red
    exit 1
}
Write-Host "Python: $pythonVersion" -ForegroundColor Yellow

# Instala dependencias
Write-Host "Instalando dependencias..." -ForegroundColor Cyan
pip install -r requirements.txt

# Inicia o servidor
Write-Host "Iniciando servidor..." -ForegroundColor Cyan
python server.py
