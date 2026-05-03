@echo off
REM Script de inicio rápido para Windows
REM Chat Multi-Hilo - Docker Auto-Scaffolder

cls

echo.
echo ===============================================================
echo.
echo        CHAT MULTI-HILO AUTO-SCAFFOLDER
echo.
echo              Powered by IBM watsonx.ai
echo.
echo ===============================================================
echo.

echo [1/6] Verificando Docker...

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

echo [2/6] Limpiando contenedores previos...
docker compose down >nul 2>&1
docker rm -f chat-server chat-client-flet >nul 2>&1
echo [OK] Limpieza completada
echo.

echo [3/6] Verificando certificados SSL...
if not exist "certs\server.crt" (
    echo Generando certificados SSL...
    if not exist "certs" mkdir certs
    
    REM Verificar si OpenSSL está disponible
    openssl version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] OpenSSL no encontrado.
        echo.
        echo Opciones:
        echo 1. Instala OpenSSL desde: https://slproweb.com/products/Win32OpenSSL.html
        echo 2. Usa Git Bash y ejecuta: bash generate_certs.sh
        pause
        exit /b 1
    )
    
    openssl req -x509 -newkey rsa:4096 -nodes -keyout certs\server.key -out certs\server.crt -days 365 -subj "/C=MX/ST=Estado/L=Ciudad/O=ChatSeguro/OU=IT/CN=chat-server" 2>nul
    echo [OK] Certificados generados
) else (
    echo [OK] Certificados SSL encontrados
)
echo.

echo [4/6] Construyendo imagenes Docker...
docker compose build --no-cache
echo [OK] Imagenes construidas
echo.

echo [5/6] Iniciando servicios...
docker compose up -d --build
echo [OK] Servicios iniciados
echo.

echo [6/6] Esperando que los servicios esten listos...
timeout /t 8 /nobreak >nul
echo.

echo ===============================================================
echo.
echo     ENTORNO SCAFFOLDEADO EXITOSAMENTE
echo.
echo ===============================================================
echo.

echo Estado de los servicios:
docker compose ps
echo.

echo ===============================================================
echo                  ACCESO AL SISTEMA
echo ===============================================================
echo.
echo   Cliente Web:  http://localhost:8550
echo   Servidor:     localhost:5000
echo   IA:           IBM watsonx.ai (configurar .env)
echo.
echo ===============================================================
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
