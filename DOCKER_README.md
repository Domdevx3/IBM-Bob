# 🐳 Guía de Despliegue con Docker

Esta guía te ayudará a desplegar el sistema de Chat Multi-Hilo usando Docker y Docker Compose en cualquier sistema operativo.

## 📋 Requisitos Previos

- **Docker Desktop** (Windows/macOS) o **Docker Engine** (Linux)
- **Docker Compose** v2.0+
- **Git Bash** (Windows) o terminal Unix (Linux/macOS)
- Mínimo 4GB RAM disponible
- (Opcional) GPU NVIDIA para aceleración de IA

## 🚀 Inicio Rápido

### 1. Generar Certificados SSL

Antes de iniciar los contenedores, debes generar los certificados SSL:

**En Linux/macOS:**
```bash
chmod +x generate_certs.sh
./generate_certs.sh
```

**En Windows (Git Bash):**
```bash
bash generate_certs.sh
```

**En Windows (PowerShell):**
```powershell
# Instalar OpenSSL si no lo tienes: https://slproweb.com/products/Win32OpenSSL.html
mkdir certs
openssl req -x509 -newkey rsa:4096 -nodes -keyout certs/server.key -out certs/server.crt -days 365 -subj "/C=MX/ST=Estado/L=Ciudad/O=ChatSeguro/OU=IT/CN=chat-server"
```

### 2. Iniciar los Servicios

```bash
docker-compose up -d
```

Esto iniciará:
- **chat-server** en puerto `5000` (servidor de sockets)
- **chat-client** en puerto `8550` (interfaz web Flet)
- **ollama** en puerto `11434` (IA opcional)

### 3. Acceder al Chat

Abre tu navegador en:
```
http://localhost:8550
```

## 📦 Estructura de Servicios

### Servidor de Chat (`chat-server`)
- **Puerto:** 5000
- **Protocolo:** Socket SSL/TLS
- **Datos persistentes:** `./data/` (usuarios, historial, salas)
- **Certificados:** `./certs/` (server.crt, server.key)

### Cliente Flet (`chat-client`)
- **Puerto:** 8550
- **Interfaz:** Web (Material Design 3)
- **Acceso:** http://localhost:8550

### Ollama IA (`ollama`)
- **Puerto:** 11434
- **Modelo:** llama3.2:3b
- **Comando IA:** `/resume` en el chat

## 🛠️ Comandos Útiles

### Ver logs en tiempo real
```bash
docker-compose logs -f
```

### Ver logs de un servicio específico
```bash
docker-compose logs -f chat-server
docker-compose logs -f chat-client
docker-compose logs -f ollama
```

### Reiniciar servicios
```bash
docker-compose restart
```

### Detener servicios
```bash
docker-compose down
```

### Detener y eliminar volúmenes (⚠️ borra datos)
```bash
docker-compose down -v
```

### Reconstruir imágenes
```bash
docker-compose build --no-cache
docker-compose up -d
```

## 🔧 Configuración Avanzada

### Cambiar Puertos

Edita `docker-compose.yml`:

```yaml
services:
  chat-server:
    ports:
      - "5000:5000"  # Cambia el primer número (host)
  
  chat-client:
    ports:
      - "8550:8550"  # Cambia el primer número (host)
```

### Configurar IP del Servidor

El servidor está configurado para escuchar en `192.168.1.100` por defecto. Para cambiar esto:

1. Edita `Host 0.0.3.py` línea 758:
```python
s.bind(("0.0.0.0", 5000))  # Escuchar en todas las interfaces
```

2. Reconstruye la imagen:
```bash
docker-compose build chat-server
docker-compose up -d
```

### Desactivar Ollama (IA)

Si no necesitas la funcionalidad de IA, comenta el servicio en `docker-compose.yml`:

```yaml
# ollama:
#   image: ollama/ollama:latest
#   ...
```

Y en el servicio `chat-server`, elimina la dependencia:

```yaml
chat-server:
  # depends_on:
  #   - ollama
```

### Configurar GPU para Ollama

Si tienes GPU NVIDIA, asegúrate de tener instalado:
- NVIDIA Docker Runtime
- NVIDIA Container Toolkit

El `docker-compose.yml` ya incluye la configuración GPU. Si no tienes GPU, comenta la sección `deploy` en el servicio `ollama`.

## 🌐 Acceso desde Otros Dispositivos

Para acceder desde otros dispositivos en tu red local:

1. Encuentra tu IP local:
   - **Windows:** `ipconfig`
   - **Linux/macOS:** `ifconfig` o `ip addr`

2. Accede desde otro dispositivo:
   ```
   http://TU_IP:8550
   ```

3. Configura el firewall para permitir los puertos 5000 y 8550.

## 📊 Monitoreo y Salud

### Verificar estado de servicios
```bash
docker-compose ps
```

### Healthcheck del servidor
El servidor incluye un healthcheck automático cada 30 segundos. Verifica el estado:
```bash
docker inspect chat-server | grep -A 10 Health
```

## 🔒 Seguridad

### Certificados SSL
- Los certificados autofirmados son válidos por 365 días
- Para producción, usa certificados de una CA confiable (Let's Encrypt)
- Los certificados se almacenan en `./certs/`

### Datos Persistentes
- Usuarios: `./data/usuarios.json`
- Historial: `./data/historial.json`
- Salas: `./data/salas.json`
- Pines: `./data/pines.json`

### Backup
```bash
# Backup de datos
tar -czf backup-$(date +%Y%m%d).tar.gz data/ certs/

# Restaurar backup
tar -xzf backup-YYYYMMDD.tar.gz
```

## 🐛 Solución de Problemas

### El servidor no inicia
```bash
# Verificar logs
docker-compose logs chat-server

# Verificar certificados
ls -la certs/

# Regenerar certificados
./generate_certs.sh
```

### El cliente no se conecta
```bash
# Verificar que el servidor esté corriendo
docker-compose ps

# Verificar conectividad
docker exec chat-client ping chat-server

# Reiniciar servicios
docker-compose restart
```

### Ollama no responde
```bash
# Descargar modelo manualmente
docker exec -it chat-ollama ollama pull llama3.2:3b

# Verificar modelos instalados
docker exec -it chat-ollama ollama list
```

### Puerto ya en uso
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS
lsof -i :5000
kill -9 <PID>
```

## 🔄 Actualización

Para actualizar a una nueva versión:

```bash
# Detener servicios
docker-compose down

# Actualizar código
git pull

# Reconstruir imágenes
docker-compose build --no-cache

# Iniciar servicios
docker-compose up -d
```

## 📝 Variables de Entorno

Puedes crear un archivo `.env` para personalizar la configuración:

```env
# Puertos
CHAT_SERVER_PORT=5000
CHAT_CLIENT_PORT=8550
OLLAMA_PORT=11434

# IA
OLLAMA_MODEL=llama3.2:3b

# Red
SUBNET=172.20.0.0/16
```

## 🎯 Producción

Para despliegue en producción:

1. **Usa certificados válidos** (Let's Encrypt)
2. **Configura un proxy reverso** (Nginx/Traefik)
3. **Habilita HTTPS** en el cliente
4. **Configura límites de recursos**:

```yaml
services:
  chat-server:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

5. **Usa Docker Swarm o Kubernetes** para alta disponibilidad

## 📚 Recursos Adicionales

- [Documentación de Docker](https://docs.docker.com/)
- [Documentación de Flet](https://flet.dev/)
- [Ollama Models](https://ollama.ai/library)

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs: `docker-compose logs`
2. Verifica la documentación técnica: `Manual Técnico.pdf`
3. Consulta el README principal: `README.md`

---

**Hecho con ❤️ por el equipo de Chat-Multihilo-DChat**