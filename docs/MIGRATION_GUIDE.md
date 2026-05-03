# 🔄 Migration Guide - Old to New Structure

## Overview
This guide helps you transition from the old flat file structure to the new organized hierarchy.

## What Changed?

### Directory Structure
```
OLD STRUCTURE:                    NEW STRUCTURE:
├── flet_app.py                  ├── src/
├── Host 0.0.3.py                │   ├── client/
├── database.py                  │   │   ├── flet_app.py
├── design_constants.py          │   │   └── flet_app_backup.py
├── docker-compose.yml           │   ├── server/
├── Dockerfile.client            │   │   └── chat_server.py
├── requirements-*.txt           │   ├── database/
├── *.md                         │   │   ├── database.py
├── generate_certs.sh            │   │   ├── db_config.py
└── data/                        │   │   ├── migrate_to_postgres.py
    ├── usuarios.json            │   │   └── test_postgres_connection.py
    ├── salas.json               │   └── shared/
    └── ...                      │       └── design_constants.py
                                 ├── config/
                                 │   ├── docker-compose.yml
                                 │   ├── Dockerfile.client
                                 │   ├── Dockerfile.server
                                 │   ├── .env.example
                                 │   └── requirements-*.txt
                                 ├── scripts/
                                 │   ├── generate_certs.sh
                                 │   ├── start.sh
                                 │   └── start.bat
                                 ├── docs/
                                 │   └── *.md
                                 └── data/
                                     └── json/
                                         ├── usuarios.json
                                         └── ...
```

## Step-by-Step Migration

### 1. Update Your Environment

If you have a `.env` file in the root, it should be moved or referenced:
```bash
# Option 1: Keep in root (recommended)
cp .env config/.env.example  # Create template
# Keep your actual .env in root

# Option 2: Update paths in your code
# The app will look for .env in the project root
```

### 2. Update Import Statements

#### In Python Files
```python
# OLD
from design_constants import COLOR_BOTON
from database import db_manager

# NEW
from src.shared.design_constants import COLOR_BOTON
from src.database.database import db_manager
```

### 3. Update Docker Commands

#### Old Way
```bash
docker-compose up -d
```

#### New Way
```bash
cd config
docker-compose up -d
```

Or from root:
```bash
docker-compose -f config/docker-compose.yml up -d
```

### 4. Update Script Execution

#### Old Way
```bash
bash generate_certs.sh
python flet_app.py
```

#### New Way
```bash
bash scripts/generate_certs.sh
python src/client/flet_app.py
```

Or use the startup scripts:
```bash
# Linux/Mac
bash scripts/start.sh

# Windows
scripts\start.bat
```

### 5. Update File Paths in Code

If your code references files directly:

```python
# OLD
with open('data/usuarios.json', 'r') as f:
    users = json.load(f)

# NEW
with open('data/json/usuarios.json', 'r') as f:
    users = json.load(f)
```

### 6. Update Docker Volume Mounts

The docker-compose.yml has been updated, but if you have custom mounts:

```yaml
# OLD
volumes:
  - ./data:/app/data
  - ./certs:/app/certs

# NEW (already updated in config/docker-compose.yml)
volumes:
  - ../data:/app/data
  - ../certs:/app/certs
```

## Common Issues & Solutions

### Issue 1: Import Errors
```
ModuleNotFoundError: No module named 'design_constants'
```

**Solution**: Update imports to use `src.` prefix:
```python
from src.shared.design_constants import COLOR_BOTON
```

### Issue 2: File Not Found
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/usuarios.json'
```

**Solution**: Update path to include `json/` subdirectory:
```python
'data/json/usuarios.json'
```

### Issue 3: Docker Build Fails
```
ERROR: Cannot locate specified Dockerfile: Dockerfile.client
```

**Solution**: Run from config directory or specify full path:
```bash
cd config && docker-compose up
# OR
docker-compose -f config/docker-compose.yml up
```

### Issue 4: Python Path Issues
```
ModuleNotFoundError: No module named 'src'
```

**Solution**: Ensure you're running from project root:
```bash
cd /path/to/IBM-Bob
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python src/client/flet_app.py
```

### Issue 5: Environment Variables Not Loading
```
KeyError: 'WATSONX_API_KEY'
```

**Solution**: Ensure `.env` file is in project root:
```bash
# Check if .env exists
ls -la .env

# If not, copy from example
cp config/.env.example .env
# Then edit with your values
```

## Verification Checklist

After migration, verify everything works:

- [ ] Python imports work without errors
- [ ] Docker containers build successfully
- [ ] Application starts without file not found errors
- [ ] Database connections work (if using PostgreSQL)
- [ ] SSL certificates are found
- [ ] Data files are accessible
- [ ] Environment variables load correctly
- [ ] Scripts execute from new locations

## Quick Test Commands

```bash
# Test Python imports
python -c "from src.shared.design_constants import COLOR_BOTON; print('✅ Imports OK')"

# Test file access
python -c "import os; print('✅ Data files OK' if os.path.exists('data/json/usuarios.json') else '❌ Data files missing')"

# Test Docker build
cd config && docker-compose build --no-cache

# Test application startup
python src/client/flet_app.py
```

## Rollback Plan

If you need to revert to the old structure:

```bash
# 1. Move files back to root
mv src/client/flet_app.py .
mv src/server/chat_server.py "Host 0.0.3.py"
mv src/shared/design_constants.py .
mv src/database/*.py .

# 2. Move config files back
mv config/docker-compose.yml .
mv config/Dockerfile.* .
mv config/requirements-*.txt .

# 3. Move docs back
mv docs/*.md .

# 4. Move scripts back
mv scripts/*.sh .
mv scripts/*.bat .

# 5. Restore data structure
mv data/json/* data/
rmdir data/json

# 6. Remove new directories
rm -rf src/ config/ docs/ scripts/
```

## Benefits of New Structure

✅ **Better Organization**: Clear separation of concerns
✅ **Easier Navigation**: Find files faster
✅ **Scalability**: Easy to add new modules
✅ **Professional**: Industry-standard structure
✅ **Maintainability**: Easier to understand and modify
✅ **Docker-Friendly**: Better container builds
✅ **Documentation**: Centralized in docs/
✅ **Testing**: Dedicated test directory

## Next Steps

1. Read `PROJECT_STRUCTURE.md` for detailed structure documentation
2. Update any custom scripts or tools you've created
3. Update your IDE/editor workspace settings if needed
4. Inform team members about the new structure
5. Update any external documentation or wikis

## Need Help?

- Check `PROJECT_STRUCTURE.md` for detailed structure info
- Review `docs/README.md` for general documentation
- Check `docs/DOCKER_README.md` for Docker-specific help
- See `docs/POSTGRESQL_SETUP_GUIDE.md` for database setup

---

**Made with Bob** 🤖
Migration Date: 2026-05-03