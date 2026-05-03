#!/bin/bash

# Script para generar certificados SSL autofirmados
# Compatible con Linux, macOS y Windows (Git Bash/WSL)

set -e

CERT_DIR="./certs"
DAYS_VALID=365

echo "🔐 Generador de Certificados SSL para Chat Seguro"
echo "=================================================="

# Crear directorio si no existe
mkdir -p "$CERT_DIR"

# Verificar si ya existen certificados
if [ -f "$CERT_DIR/server.crt" ] && [ -f "$CERT_DIR/server.key" ]; then
    echo ""
    echo "⚠️  Ya existen certificados en $CERT_DIR"
    read -p "¿Deseas regenerarlos? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
        echo "✅ Manteniendo certificados existentes."
        exit 0
    fi
    echo "🔄 Regenerando certificados..."
fi

# Generar clave privada y certificado autofirmado
echo ""
echo "📝 Generando certificado SSL autofirmado..."
echo "   Válido por $DAYS_VALID días"
echo ""

openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.crt" \
    -days $DAYS_VALID \
    -subj "/C=MX/ST=Estado/L=Ciudad/O=ChatSeguro/OU=IT/CN=chat-server" \
    2>/dev/null

# Verificar que se crearon correctamente
if [ -f "$CERT_DIR/server.crt" ] && [ -f "$CERT_DIR/server.key" ]; then
    echo ""
    echo "✅ Certificados generados exitosamente:"
    echo "   📄 Certificado: $CERT_DIR/server.crt"
    echo "   🔑 Clave privada: $CERT_DIR/server.key"
    echo ""
    
    # Mostrar información del certificado
    echo "📋 Información del certificado:"
    openssl x509 -in "$CERT_DIR/server.crt" -noout -subject -dates 2>/dev/null
    
    # Establecer permisos seguros
    chmod 600 "$CERT_DIR/server.key"
    chmod 644 "$CERT_DIR/server.crt"
    
    echo ""
    echo "🔒 Permisos de seguridad aplicados."
    echo ""
    echo "✨ ¡Listo! Puedes iniciar el servidor con docker-compose."
else
    echo ""
    echo "❌ Error: No se pudieron generar los certificados."
    exit 1
fi

# Made with Bob
