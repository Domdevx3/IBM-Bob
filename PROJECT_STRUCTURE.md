# 📁 Project Structure Documentation

## Overview
This document describes the organized directory structure of the IBM-Bob Chat Application with Watson AI integration.

## Directory Hierarchy

```
IBM-Bob/
├── src/                          # Source code
│   ├── client/                   # Client application (Flet UI)
│   │   ├── flet_app.py          # Main Flet application
│   │   └── flet_app_backup.py   # Backup version
│   ├── server/                   # Server application
│   │   └── chat_server.py       # Chat server with SSL/TLS
│   ├── database/                 # Database layer
│   │   ├── database.py          # PostgreSQL ORM models & operations
│   │   ├── db_config.py         # Database configuration
│   │   ├── migrate_to_postgres.py # Migration script from JSON to PostgreSQL
│   │   └── test_postgres_connection.py # Database connection tests
│   └── shared/                   # Shared modules
│       └── design_constants.py  # UI/UX design constants
│
├── config/                       # Configuration files
│   ├── docker-compose.yml       # Docker orchestration
│   ├── Dockerfile.client        # Client container definition
│   ├── Dockerfile.server        # Server container definition
│   ├── init_db.sql              # PostgreSQL initialization
│   ├── .env.example             # Environment variables template
│   ├── requirements-client.txt  # Client Python dependencies
│   ├── requirements-server.txt  # Server Python dependencies
│   └── requirements-postgres.txt # PostgreSQL Python dependencies
│
├── scripts/                      # Utility scripts
│   ├── generate_certs.sh        # SSL certificate generation
│   ├── start.sh                 # Linux/Mac startup script
│   ├── start.bat                # Windows startup script
│   ├── profile_imports.py       # Import profiling tool
│   └── profile_startup.py       # Startup profiling tool
│
├── docs/                         # Documentation
│   ├── README.md                # Main project documentation
│   ├── DOCKER_README.md         # Docker setup guide
│   ├── FEATURES_CHANGELOG.md    # Feature history
│   ├── FIXES_APPLIED.md         # Bug fixes log
│   ├── INTEGRATE_DATABASE.md    # Database integration guide
│   ├── OPTIMIZATION_GUIDE.md    # Performance optimization
│   ├── POSTGRESQL_SETUP_GUIDE.md # PostgreSQL setup
│   ├── POSTGRESQL_OPTIMIZATION_GUIDE.md # PostgreSQL performance
│   ├── FAST_STARTUP_INSTRUCTIONS.md # Quick start guide
│   ├── STARTUP_OPTIMIZATION.md  # Startup optimization details
│   ├── STARTUP_OPTIMIZATION_FINAL.md # Final optimization results
│   ├── SKILLS.md                # Development guidelines
│   └── UI_UX_UPGRADE_GUIDE.md   # UI/UX design guide
│
├── data/                         # Application data
│   ├── json/                    # JSON data files (legacy/fallback)
│   │   ├── usuarios.json        # User data
│   │   ├── salas.json           # Chat rooms
│   │   ├── historial.json       # Message history
│   │   └── pines.json           # Pinned messages
│   └── backups/                 # Data backups
│
├── certs/                        # SSL/TLS certificates
│   ├── server.crt               # Server certificate
│   └── server.key               # Server private key
│
├── logs/                         # Application logs
│
├── tests/                        # Test files
│
└── .venv/                        # Python virtual environment

```

## Component Descriptions

### 📱 Client (`src/client/`)
- **flet_app.py**: Main Flet application with Material Design 3 UI
  - User authentication
  - Chat interface
  - IBM Watson AI integration
  - Emoji & GIF pickers
  - File attachments
  - Settings management

### 🖥️ Server (`src/server/`)
- **chat_server.py**: Multi-threaded chat server
  - SSL/TLS encryption
  - User authentication
  - Room management
  - Message broadcasting
  - Command processing

### 🗄️ Database (`src/database/`)
- **database.py**: PostgreSQL integration with SQLAlchemy
  - Lazy loading for fast startup
  - Async operations
  - ORM models for Users, Rooms, Messages, Pinned Messages
- **db_config.py**: Database configuration toggle
  - Switch between PostgreSQL and JSON files
  - Environment-based configuration
- **migrate_to_postgres.py**: Migration utility from JSON to PostgreSQL
- **test_postgres_connection.py**: Database connection testing

### 🎨 Shared (`src/shared/`)
- **design_constants.py**: Centralized UI/UX constants
  - Color schemes
  - Typography
  - Spacing values

### ⚙️ Configuration (`config/`)
- **docker-compose.yml**: Multi-container orchestration
  - PostgreSQL database
  - Chat server
  - Flet client
- **Dockerfiles**: Container definitions for client and server
- **Requirements files**: Python dependencies separated by component
- **.env.example**: Environment variables template

### 🔧 Scripts (`scripts/`)
- **generate_certs.sh**: Generate self-signed SSL certificates
- **start.sh/bat**: Platform-specific startup scripts
- **profile_*.py**: Performance profiling tools

### 📚 Documentation (`docs/`)
Comprehensive guides for setup, features, optimization, and development

### 💾 Data (`data/`)
- **json/**: Legacy JSON storage (fallback mode)
- **backups/**: Automated data backups

## Import Paths

### From Client Code
```python
from src.shared.design_constants import COLOR_BOTON
```

### From Database Code
```python
from src.database.database import db_manager
```

### From Server Code
```python
# Server is standalone, no cross-imports needed
```

## Running the Application

### Development Mode (Fast Startup)
```bash
# Use JSON files instead of PostgreSQL
export USE_POSTGRES=false
python src/client/flet_app.py
```

### Production Mode (with Docker)
```bash
cd config
docker-compose up -d
```

### Generate SSL Certificates
```bash
bash scripts/generate_certs.sh
```

## Environment Variables

Create a `.env` file in the project root (copy from `config/.env.example`):

```env
# IBM Watson AI
WATSONX_API_KEY=your_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Database (optional - set to 'true' for PostgreSQL)
USE_POSTGRES=false
DB_HOST=localhost
DB_PORT=5433
DB_NAME=chatdb
DB_USER=chatuser
DB_PASSWORD=chatpass123

# Giphy API (optional)
GIPHY_API_KEY=your_giphy_key
```

## Key Features by Component

### Client Features
- ✅ Material Design 3 UI
- ✅ User authentication (login/register)
- ✅ Real-time chat
- ✅ IBM Watson AI chat summarization
- ✅ Emoji picker with categories
- ✅ GIF picker (Giphy integration)
- ✅ File attachments
- ✅ Message pinning
- ✅ Search functionality
- ✅ Settings panel
- ✅ Notifications

### Server Features
- ✅ SSL/TLS encryption
- ✅ Multi-threaded architecture
- ✅ User authentication
- ✅ Room management
- ✅ Message broadcasting
- ✅ Admin commands
- ✅ Auto-save mechanism

### Database Features
- ✅ PostgreSQL support (optional)
- ✅ JSON file fallback
- ✅ Lazy loading for performance
- ✅ Async operations
- ✅ Migration tools
- ✅ Full-text search

## Performance Optimizations

1. **Lazy Loading**: Heavy dependencies loaded only when needed
2. **Caching**: LRU cache for frequently accessed data
3. **Async Operations**: Non-blocking database operations
4. **Batch Processing**: Efficient bulk operations
5. **Connection Pooling**: Reusable database connections

## Development Guidelines

- Follow the structure when adding new features
- Keep imports relative to project root
- Use environment variables for configuration
- Document new features in `docs/`
- Update this file when structure changes

## Migration Notes

### From Old Structure
Files have been reorganized from flat structure to modular hierarchy:
- Python files → `src/` subdirectories
- Config files → `config/`
- Documentation → `docs/`
- Scripts → `scripts/`
- Data files → `data/json/`

### Import Path Updates
All imports now use the new `src/` structure:
```python
# Old
from design_constants import COLOR_BOTON

# New
from src.shared.design_constants import COLOR_BOTON
```

## Troubleshooting

### Import Errors
Ensure you're running from the project root and Python can find the `src/` directory:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Docker Build Issues
Make sure to run docker-compose from the `config/` directory or adjust paths accordingly.

### Database Connection Issues
Check that PostgreSQL is running and environment variables are set correctly.

---

**Made with Bob** 🤖
Last Updated: 2026-05-03
