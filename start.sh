#!/bin/bash

# Script de inicio rápido para Chat Multi-Hilo
# Compatible con Linux, macOS y Windows (Git Bash)

set -e

echo "🚀 Chat Multi-Hilo - Inicio Rápido"
echo "===================================="
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado."
    echo "   Instala Docker Desktop desde: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Verificar Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose no está disponible."
    echo "   Asegúrate de tener Docker Desktop actualizado."
    exit 1
fi

echo "✅ Docker detectado correctamente"
echo ""

# Verificar certificados SSL
if [ ! -f "certs/server.crt" ] || [ ! -f "certs/server.key" ]; then
    echo "🔐 Generando certificados SSL..."
    
    if [ -f "generate_certs.sh" ]; then
        chmod +x generate_certs.sh
        ./generate_certs.sh
    else
        echo "⚠️  Script de certificados no encontrado. Generando manualmente..."
        mkdir -p certs
        openssl req -x509 -newkey rsa:4096 -nodes \
            -keyout certs/server.key \
            -out certs/server.crt \
            -days 365 \
            -subj "/C=MX/ST=Estado/L=Ciudad/O=ChatSeguro/OU=IT/CN=chat-server" \
            2>/dev/null
        echo "✅ Certificados generados"
    fi
else
    echo "✅ Certificados SSL encontrados"
fi

echo ""
echo "📦 Construyendo imágenes Docker..."
docker compose build

echo ""
echo "🚀 Iniciando servicios..."
docker compose up -d

echo ""
echo "⏳ Esperando que los servicios estén listos..."
sleep 5

# Verificar estado
echo ""
echo "📊 Estado de los servicios:"
docker compose ps

echo ""
echo "✨ ¡Listo! El sistema está corriendo."
echo ""
echo "📍 Accesos:"
echo "   🌐 Cliente Web: http://localhost:8550"
echo "   🔌 Servidor:    localhost:5000"
echo "   🤖 Ollama IA:   http://localhost:11434"
echo ""
echo "📝 Comandos útiles:"
echo "   Ver logs:       docker compose logs -f"
echo "   Detener:        docker compose down"
echo "   Reiniciar:      docker compose restart"
echo ""
echo "📚 Documentación completa: DOCKER_README.md"

# Made with Bob
