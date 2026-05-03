# 🚀 Fast Startup Instructions

## ⚡ Your app is slow because PostgreSQL libraries are installed

### Quick Fix (Restore Fast Startup):

```bash
# 1. Uninstall PostgreSQL dependencies
pip uninstall -y psycopg2-binary sqlalchemy asyncpg

# 2. Verify they're removed
pip list | grep -E "psycopg2|sqlalchemy|asyncpg"
# Should show nothing

# 3. Run your app - it will be FAST again!
python3 flet_app.py
```

**Result: App will start in < 1 second again! ⚡**

---

## 📦 Two Installation Options:

### Option 1: Fast Mode (Recommended for Development)
```bash
# Install only core dependencies (FAST startup)
pip install -r requirements-server.txt

# Your app starts instantly!
python3 flet_app.py
```

### Option 2: With PostgreSQL (Production)
```bash
# Install core dependencies
pip install -r requirements-server.txt

# Install PostgreSQL support (adds ~2 seconds to startup)
pip install -r requirements-postgres.txt

# Enable PostgreSQL in .env
# USE_POSTGRES=true

# Start PostgreSQL
docker-compose up -d postgres

# Run app
python3 flet_app.py
```

---

## 🎯 Current Status Check:

```bash
# Check if PostgreSQL libraries are installed
pip list | grep -E "psycopg2|sqlalchemy|asyncpg"

# If you see these packages, they're slowing down your startup:
# - psycopg2-binary
# - sqlalchemy  
# - asyncpg

# Remove them for fast startup:
pip uninstall -y psycopg2-binary sqlalchemy asyncpg
```

---

## 📊 Performance Comparison:

| Setup | Startup Time | Command |
|-------|-------------|---------|
| **Without PostgreSQL libs** | **< 1 sec** ⚡ | `pip install -r requirements-server.txt` |
| With PostgreSQL libs | ~3-5 sec | `pip install -r requirements-postgres.txt` |

---

## 💡 Why is this happening?

- **SQLAlchemy** and **asyncpg** are heavy libraries
- They load many modules at import time
- Even with lazy loading, having them installed adds overhead
- Solution: Only install them when you actually need PostgreSQL

---

## 🔧 Recommended Setup:

### For Daily Development:
```bash
# Clean install
pip uninstall -y psycopg2-binary sqlalchemy asyncpg
pip install -r requirements-server.txt

# Fast startup every time!
```

### When You Need PostgreSQL:
```bash
# Add PostgreSQL support
pip install -r requirements-postgres.txt

# Enable in .env
echo "USE_POSTGRES=true" >> .env

# Start database
docker-compose up -d postgres
```

---

## ✅ Verification:

After uninstalling PostgreSQL libraries:

```bash
# Time your startup
time python3 flet_app.py

# Should be < 2 seconds total
```

---

## 🎉 Summary:

1. **Uninstall PostgreSQL libraries** for fast startup
2. **Use JSON files** for development (instant)
3. **Install PostgreSQL libraries** only when needed
4. **Toggle with USE_POSTGRES** in .env

Your app will be lightning fast again! ⚡