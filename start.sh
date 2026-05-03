#!/bin/bash

# Script de inicio rápido para Chat Multi-Hilo
# Compatible con Linux, macOS y Windows (Git Bash)

set -e

# Colores ANSI
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear

echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        🚀  CHAT MULTI-HILO AUTO-SCAFFOLDER  🚀           ║
║                                                           ║
║              Powered by IBM watsonx.ai                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BLUE}[1/6]${NC} Verificando Docker..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker no está instalado.${NC}"
    echo "   Instala Docker Desktop desde: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Error: Docker Compose no está disponible.${NC}"
    echo "   Asegúrate de tener Docker Desktop actualizado."
    exit 1
fi

echo -e "${GREEN}✅ Docker detectado correctamente${NC}"
echo ""

echo -e "${BLUE}[2/6]${NC} Limpiando contenedores previos..."
docker compose down 2>/dev/null || true
docker rm -f chat-server chat-client-flet 2>/dev/null || true
echo -e "${GREEN}✅ Limpieza completada${NC}"
echo ""

echo -e "${BLUE}[3/6]${NC} Verificando certificados SSL..."
if [ ! -f "certs/server.crt" ] || [ ! -f "certs/server.key" ]; then
    echo "🔐 Generando certificados SSL..."
    
    if [ -f "generate_certs.sh" ]; then
        chmod +x generate_certs.sh
        ./generate_certs.sh
    else
        mkdir -p certs
        openssl req -x509 -newkey rsa:4096 -nodes \
            -keyout certs/server.key \
            -out certs/server.crt \
            -days 365 \
            -subj "/C=MX/ST=Estado/L=Ciudad/O=ChatSeguro/OU=IT/CN=chat-server" \
            2>/dev/null
    fi
    echo -e "${GREEN}✅ Certificados generados${NC}"
else
    echo -e "${GREEN}✅ Certificados SSL encontrados${NC}"
fi
echo ""

echo -e "${BLUE}[4/6]${NC} Construyendo imágenes Docker..."
docker compose build --no-cache
echo -e "${GREEN}✅ Imágenes construidas${NC}"
echo ""

echo -e "${BLUE}[5/6]${NC} Iniciando servicios..."
docker compose up -d --build
echo -e "${GREEN}✅ Servicios iniciados${NC}"
echo ""

echo -e "${BLUE}[6/6]${NC} Esperando que los servicios estén listos..."
sleep 8

echo ""
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     ✨  ENTORNO SCAFFOLDEADO EXITOSAMENTE  ✨            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${GREEN}📊 Estado de los servicios:${NC}"
docker compose ps
echo ""

echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║                  ACCESO AL SISTEMA                        ║${NC}"
echo -e "${YELLOW}╠═══════════════════════════════════════════════════════════╣${NC}"
echo -e "${YELLOW}║${NC}                                                           ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}  ${CYAN}🌐 Cliente Web:${NC}  http://localhost:8550                ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}  ${CYAN}🔌 Servidor:${NC}     localhost:5000                       ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}  ${CYAN}🤖 IA:${NC}           IBM watsonx.ai (configurar .env)     ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}                                                           ${YELLOW}║${NC}"
echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📝 Comandos útiles:${NC}"
echo "   Ver logs:       docker compose logs -f"
echo "   Detener:        docker compose down"
echo "   Reiniciar:      docker compose restart"
echo ""
echo -e "${BLUE}📚 Documentación:${NC} DOCKER_README.md"
echo ""

# Made with Bob
