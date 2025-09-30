#!/bin/bash
# Script para ejecutar el backend

echo "🎵 Iniciando Vinyl Music Player Backend..."

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Instalar dependencias si es necesario
pip install -r requirements.txt

# Crear carpetas necesarias
mkdir -p data
mkdir -p frontend/static/uploads/covers

# Ejecutar el servidor
python run.py