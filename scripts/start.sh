#!/bin/bash

# Script de inicio optimizado para Chat Multi-Hilo con JSON Storage
# Compatible con Linux, macOS y Windows (Git Bash)
# Arranque instantáneo - Sin esperas de base de datos

set -e

# Colores ANSI
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear

echo -e "${CYAN}${BOLD}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        🚀  IBM BOB CHAT - AI SCAFFOLDER  🚀              ║
║                                                           ║
║         Powered by IBM watsonx.ai + JSON Storage          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BLUE}[1/5]${NC} Verificando Docker..."

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

echo -e "${BLUE}[2/5]${NC} Limpiando contenedores previos..."
docker compose -f config/docker-compose.yml down 2>/dev/null || true
docker rm -f chat-server chat-client-flet 2>/dev/null || true
echo -e "${GREEN}✅ Limpieza completada${NC}"
echo ""

echo -e "${BLUE}[3/5]${NC} Verificando certificados SSL..."
if [ ! -f "certs/server.crt" ] || [ ! -f "certs/server.key" ]; then
    echo "🔐 Generando certificados SSL..."
    
    mkdir -p certs
    openssl req -x509 -newkey rsa:4096 -nodes \
        -keyout certs/server.key \
        -out certs/server.crt \
        -days 365 \
        -subj "/C=MX/ST=Estado/L=Ciudad/O=IBMChat/OU=IT/CN=chat-server" \
        2>/dev/null
    
    echo -e "${GREEN}✅ Certificados generados${NC}"
else
    echo -e "${GREEN}✅ Certificados SSL encontrados${NC}"
fi
echo ""

echo -e "${BLUE}[4/5]${NC} Creando estructura de datos JSON..."
mkdir -p data/json
if [ ! -f "data/json/usuarios.json" ]; then
    echo "{}" > data/json/usuarios.json
fi
if [ ! -f "data/json/salas.json" ]; then
    echo '["General", "Desarrollo", "Soporte"]' > data/json/salas.json
fi
if [ ! -f "data/json/historial.json" ]; then
    echo '{"General": [], "Desarrollo": [], "Soporte": []}' > data/json/historial.json
fi
if [ ! -f "data/json/pines.json" ]; then
    echo '{"General": "", "Desarrollo": "", "Soporte": ""}' > data/json/pines.json
fi
echo -e "${GREEN}✅ Estructura JSON inicializada${NC}"
echo ""

echo -e "${BLUE}[5/5]${NC} Iniciando servicios (arranque instantáneo)..."
docker compose -f config/docker-compose.yml up -d --build
echo -e "${GREEN}✅ Servicios iniciados${NC}"
echo ""

# Espera mínima solo para que Docker reporte el estado
sleep 2

echo ""
echo -e "${CYAN}${BOLD}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║          ✨  SISTEMA LISTO EN <3 SEGUNDOS  ✨            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${GREEN}📊 Estado de los servicios:${NC}"
docker compose -f config/docker-compose.yml ps
echo ""

echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║${NC}                  ${BOLD}${CYAN}ACCESO AL SISTEMA${NC}                        ${YELLOW}║${NC}"
echo -e "${YELLOW}╠═══════════════════════════════════════════════════════════╣${NC}"
echo -e "${YELLOW}║${NC}                                                           ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}  ${BOLD}${GREEN}🌐 Abre tu navegador en:${NC}                              ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}     ${CYAN}${BOLD}http://localhost:8550${NC}                              ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}                                                           ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}  ${GREEN}🔌 Servidor Chat:${NC}     localhost:5001                    ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}  ${GREEN}🤖 AI Scaffolder:${NC}     /scaffold [descripción]          ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}  ${GREEN}💾 Almacenamiento:${NC}    100% JSON (data/json/)           ${YELLOW}║${NC}"
echo -e "${YELLOW}║${NC}                                                           ${YELLOW}║${NC}"
echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📝 Comandos útiles:${NC}"
echo "   Ver logs:       docker compose -f config/docker-compose.yml logs -f"
echo "   Detener:        docker compose -f config/docker-compose.yml down"
echo "   Reiniciar:      docker compose -f config/docker-compose.yml restart"
echo ""

echo -e "${BLUE}🎯 Prueba el AI Scaffolder:${NC}"
echo "   1. Abre http://localhost:8550"
echo "   2. Inicia sesión"
echo "   3. Escribe: ${CYAN}/scaffold API REST con Node.js y Express${NC}"
echo ""

echo -e "${BLUE}📚 Documentación:${NC}"
echo "   - JSON Migration: docs/JSON_MIGRATION_COMPLETE.md"
echo "   - AI Scaffolder:  docs/AI_SCAFFOLDER_FEATURE.md"
echo "   - Docker Setup:   docs/DOCKER_README.md"
echo ""

echo -e "${GREEN}${BOLD}✅ Sistema listo para producción - Arranque en <3 segundos${NC}"
echo ""

# Made with Bob - DevOps Optimized
