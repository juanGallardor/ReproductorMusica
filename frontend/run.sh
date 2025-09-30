#!/bin/bash
# Script para ejecutar el frontend

echo "🎵 Iniciando Vinyl Music Player Frontend..."

# Instalar dependencias si node_modules no existe
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependencias..."
    npm install
fi

# Ejecutar en modo desarrollo
npm run dev