@echo off
REM Script de inicio rápido para Windows
REM Chat Multi-Hilo - Docker

echo.
echo ========================================
echo   Chat Multi-Hilo - Inicio Rapido
echo ========================================
echo.

REM Verificar Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no esta instalado.
    echo Instala Docker Desktop desde: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Verificar Docker Compose
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose no esta disponible.
    echo Asegurate de tener Docker Desktop actualizado.
    pause
    exit /b 1
)

echo [OK] Docker detectado correctamente
echo.

REM Verificar certificados SSL
if not exist "certs\server.crt" (
    echo [INFO] Generando certificados SSL...
    if not exist "certs" mkdir certs
    
    REM Verificar si OpenSSL está disponible
    openssl version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] OpenSSL no encontrado.
        echo.
        echo Opciones:
        echo 1. Instala OpenSSL desde: https://slproweb.com/products/Win32OpenSSL.html
        echo 2. Usa Git Bash y ejecuta: bash generate_certs.sh
        echo 3. Genera manualmente los certificados
        pause
        exit /b 1
    )
    
    openssl req -x509 -newkey rsa:4096 -nodes -keyout certs\server.key -out certs\server.crt -days 365 -subj "/C=MX/ST=Estado/L=Ciudad/O=ChatSeguro/OU=IT/CN=chat-server" 2>nul
    echo [OK] Certificados generados
) else (
    echo [OK] Certificados SSL encontrados
)

echo.
echo [INFO] Construyendo imagenes Docker...
docker compose build

echo.
echo [INFO] Iniciando servicios...
docker compose up -d

echo.
echo [INFO] Esperando que los servicios esten listos...
timeout /t 5 /nobreak >nul

echo.
echo [INFO] Estado de los servicios:
docker compose ps

echo.
echo ========================================
echo   Sistema iniciado correctamente
echo ========================================
echo.
echo Accesos:
echo   - Cliente Web: http://localhost:8550
echo   - Servidor:    localhost:5000
echo   - Ollama IA:   http://localhost:11434
echo.
echo Comandos utiles:
echo   - Ver logs:    docker compose logs -f
echo   - Detener:     docker compose down
echo   - Reiniciar:   docker compose restart
echo.
echo Documentacion: DOCKER_README.md
echo.
pause

@REM Made with Bob
