# 🐳 Deployment Guide with Docker

This guide will help you deploy the Multi-Thread Chat system using Docker and Docker Compose on any operating system.

## 📋 Prerequisites

- **Docker Desktop** (Windows/macOS) or **Docker Engine** (Linux)
- **Docker Compose** v2.0+
- **Git Bash** (Windows) or a Unix terminal (Linux/macOS)
- At least 4GB RAM available
- (Optional) NVIDIA GPU for AI acceleration

## 🚀 Quick Start

### 1. Generate SSL Certificates

Before starting the containers, you must generate the SSL certificates:

**On Linux/macOS:**
```bash
chmod +x generate_certs.sh
./generate_certs.sh
```

**On Windows (Git Bash):**
```bash
bash generate_certs.sh
```

**On Windows (PowerShell):**
```powershell
# Install OpenSSL if you don't have it: https://slproweb.com/products/Win32OpenSSL.html
mkdir certs
openssl req -x509 -newkey rsa:4096 -nodes -keyout certs/server.key -out certs/server.crt -days 365 -subj "/C=MX/ST=Estado/L=Ciudad/O=ChatSeguro/OU=IT/CN=chat-server"
```

### 2. Start the Services

```bash
docker-compose up -d
```

This will start:
- **chat-server** on port `5000` (socket server)
- **chat-client** on port `8550` (Flet web interface)
- **ollama** on port `11434` (optional AI)

### 3. Access the Chat

Open your browser at:
```
http://localhost:8550
```

## 📦 Service Structure

### Chat Server (`chat-server`)
- **Port:** 5000
- **Protocol:** SSL/TLS Socket
- **Persistent data:** `./data/` (users, history, rooms)
- **Certificates:** `./certs/` (server.crt, server.key)

### Flet Client (`chat-client`)
- **Port:** 8550
- **Interface:** Web (Material Design 3)
- **Access:** http://localhost:8550

### Ollama AI (`ollama`)
- **Port:** 11434
- **Model:** llama3.2:3b
- **AI command:** `/resume` in the chat

## 🛠️ Useful Commands

### View logs in real time
```bash
docker-compose logs -f
```

### View logs for a specific service
```bash
docker-compose logs -f chat-server
docker-compose logs -f chat-client
docker-compose logs -f ollama
```

### Restart services
```bash
docker-compose restart
```

### Stop services
```bash
docker-compose down
```

### Stop and remove volumes (⚠️ deletes data)
```bash
docker-compose down -v
```

### Rebuild images
```bash
docker-compose build --no-cache
docker-compose up -d
```

## 🔧 Advanced Configuration

### Change Ports

Edit `docker-compose.yml`:

```yaml
services:
  chat-server:
    ports:
      - "5000:5000"  # Change the first number (host)
  
  chat-client:
    ports:
      - "8550:8550"  # Change the first number (host)
```

### Configure Server IP

The server is configured to listen on `192.168.1.100` by default. To change this:

1. Edit `Host 0.0.3.py` line 758:
```python
s.bind(("0.0.0.0", 5000))  # Listen on all interfaces
```

2. Rebuild the image:
```bash
docker-compose build chat-server
docker-compose up -d
```

### Disable Ollama (AI)

If you don't need the AI functionality, comment out the service in `docker-compose.yml`:

```yaml
# ollama:
#   image: ollama/ollama:latest
#   ...
```

And in the `chat-server` service, remove the dependency:

```yaml
chat-server:
  # depends_on:
  #   - ollama
```

### Configure GPU for Ollama

If you have an NVIDIA GPU, make sure you have installed:
- NVIDIA Docker Runtime
- NVIDIA Container Toolkit

The `docker-compose.yml` already includes GPU configuration. If you don't have a GPU, comment out the `deploy` section in the `ollama` service.

## 🌐 Access from Other Devices

To access from other devices on your local network:

1. Find your local IP:
   - **Windows:** `ipconfig`
   - **Linux/macOS:** `ifconfig` or `ip addr`

2. Access from another device:
   ```
   http://YOUR_IP:8550
   ```

3. Configure the firewall to allow ports 5000 and 8550.

## 📊 Monitoring and Health

### Check service status
```bash
docker-compose ps
```

### Server healthcheck
The server includes an automatic healthcheck every 30 seconds. Check the status:
```bash
docker inspect chat-server | grep -A 10 Health
```

## 🔒 Security

### SSL Certificates
- Self-signed certificates are valid for 365 days
- For production, use certificates from a trusted CA (Let's Encrypt)
- Certificates are stored in `./certs/`

### Persistent Data
- Users: `./data/usuarios.json`
- History: `./data/historial.json`
- Rooms: `./data/salas.json`
- Pins: `./data/pines.json`

### Backup
```bash
# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz data/ certs/

# Restore backup
tar -xzf backup-YYYYMMDD.tar.gz
```

## 🐛 Troubleshooting

### Server won't start
```bash
# Check logs
docker-compose logs chat-server

# Check certificates
ls -la certs/

# Regenerate certificates
./generate_certs.sh
```

### Client won't connect
```bash
# Verify server is running
docker-compose ps

# Check connectivity
docker exec chat-client ping chat-server

# Restart services
docker-compose restart
```

### Ollama not responding
```bash
# Manually download the model
docker exec -it chat-ollama ollama pull llama3.2:3b

# Check installed models
docker exec -it chat-ollama ollama list
```

### Port already in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS
lsof -i :5000
kill -9 <PID>
```

## 🔄 Update

To update to a new version:

```bash
# Stop services
docker-compose down

# Update code
git pull

# Rebuild images
docker-compose build --no-cache

# Start services
docker-compose up -d
```

## 📝 Environment Variables

You can create a `.env` file to customize configuration:

```env
# Ports
CHAT_SERVER_PORT=5000
CHAT_CLIENT_PORT=8550
OLLAMA_PORT=11434

# AI
OLLAMA_MODEL=llama3.2:3b

# Network
SUBNET=172.20.0.0/16
```

## 🎯 Production

For production deployment:

1. **Use valid certificates** (Let's Encrypt)
2. **Set up a reverse proxy** (Nginx/Traefik)
3. **Enable HTTPS** on the client
4. **Configure resource limits**:

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

5. **Use Docker Swarm or Kubernetes** for high availability

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Flet Documentation](https://flet.dev/)
- [Ollama Models](https://ollama.ai/library)

## 🆘 Support

If you find issues:
1. Check the logs: `docker-compose logs`
2. Review the technical documentation: `Manual Técnico.pdf`
3. Consult the main README: `README.md`

---
