# 🤖 IBM-Bob Chat Application

A modern, feature-rich chat application with IBM Watson AI integration, built with Python and Flet.

## ✨ Features

- 💬 Real-time multi-room chat
- 🤖 IBM Watson AI chat summarization
- 🔐 User authentication (login/register)
- 🎨 Material Design 3 UI
- 😊 Emoji picker with categories
- 🎬 GIF picker (Giphy integration)
- 📎 File attachments
- 📌 Message pinning
- 🔍 Search functionality
- ⚙️ Customizable settings
- 🔒 SSL/TLS encryption
- 🗄️ PostgreSQL support (optional)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd IBM-Bob
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   
   # Activate it:
   # Linux/Mac:
   source .venv/bin/activate
   # Windows:
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r config/requirements-client.txt
   pip install -r config/requirements-server.txt
   ```

4. **Configure environment**
   ```bash
   # Copy the example file
   cp config/.env.example .env
   
   # Edit .env with your credentials
   nano .env  # or use your favorite editor
   ```

   Required variables:
   ```env
   WATSONX_API_KEY=your_actual_api_key
   WATSONX_PROJECT_ID=your_actual_project_id
   ```

5. **Generate SSL certificates**
   ```bash
   bash scripts/generate_certs.sh
   ```

### 🎯 Run the Application

#### Option 1: One-Command Launch (Recommended)
```bash
python main.py
```

This will:
- ✅ Check prerequisites
- ✅ Start the chat server
- ✅ Start the Flet client
- ✅ Open in your browser automatically

Press `Ctrl+C` to stop all services.

#### Option 2: Manual Launch

**Terminal 1 - Start Server:**
```bash
python src/server/chat_server.py
```

**Terminal 2 - Start Client:**
```bash
python src/client/flet_app.py
```

#### Option 3: Docker (Production)
```bash
cd config
docker-compose up -d
```

Access at: `http://localhost:8550`

## 📁 Project Structure

```
IBM-Bob/
├── main.py                 # 🚀 One-command launcher
├── src/
│   ├── client/            # Flet UI application
│   ├── server/            # Chat server
│   ├── database/          # PostgreSQL integration
│   └── shared/            # Shared modules
├── config/                # Configuration files
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── data/                  # Application data
├── certs/                 # SSL certificates
└── logs/                  # Application logs
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed structure.

## 📚 Documentation

- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Complete project structure guide
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migration from old structure
- **[SECURITY.md](SECURITY.md)** - Security guidelines
- **[docs/FEATURES_CHANGELOG.md](docs/FEATURES_CHANGELOG.md)** - Feature history
- **[docs/DOCKER_README.md](docs/DOCKER_README.md)** - Docker setup guide
- **[docs/POSTGRESQL_SETUP_GUIDE.md](docs/POSTGRESQL_SETUP_GUIDE.md)** - Database setup

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# IBM Watson AI (Required)
WATSONX_API_KEY=your_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com/

# Giphy API (Optional)
GIPHY_API_KEY=your_giphy_key

# Database (Optional - for PostgreSQL)
USE_POSTGRES=false
DB_HOST=localhost
DB_PORT=5433
DB_NAME=chatdb
DB_USER=chatuser
DB_PASSWORD=chatpass123
```

### Fast Startup Mode (Default)

By default, the app uses JSON files for data storage (fast startup):
```env
USE_POSTGRES=false
```

### Production Mode (PostgreSQL)

For production, enable PostgreSQL:
```env
USE_POSTGRES=true
```

Then start PostgreSQL:
```bash
cd config
docker-compose up postgres -d
```

## 🎮 Usage

### First Time Setup

1. **Register an account**
   - Click "Register" on the login screen
   - Enter username, password, and email
   - Click "Register"

2. **Login**
   - Enter your credentials
   - Click "Login"

3. **Start chatting!**
   - Select a room from the sidebar
   - Type your message
   - Use emoji 😊 and GIF 🎬 buttons for fun!

### Features Guide

#### Chat Commands
- `/help` - Show available commands
- `/status` - Show your status
- `/rooms` - List all rooms

#### AI Summarization
1. Click the "Summarize" button in the header
2. Watson AI will analyze the conversation
3. Get a concise summary of the chat

#### Pin Messages
1. Hover over a message
2. Click the pin icon
3. Pinned message appears at the top

#### Search Messages
1. Click the search icon in the header
2. Enter your search term
3. View matching messages

#### Send GIFs
1. Click the GIF button (🎬)
2. Search for a GIF
3. Click to send

#### Send Emojis
1. Click the emoji button (😊)
2. Browse categories
3. Click to insert

## 🐳 Docker Deployment

### Build and Run
```bash
cd config
docker-compose up -d
```

### View Logs
```bash
docker-compose logs -f
```

### Stop Services
```bash
docker-compose down
```

### Rebuild
```bash
docker-compose build --no-cache
docker-compose up -d
```

## 🔒 Security

- ✅ SSL/TLS encryption for all connections
- ✅ Password hashing (SHA-256)
- ✅ Environment variable configuration
- ✅ No hardcoded credentials
- ✅ `.gitignore` protects sensitive files

See [SECURITY.md](SECURITY.md) for detailed security guidelines.

## 🛠️ Development

### Run Tests
```bash
python -m pytest tests/
```

### Profile Startup
```bash
python scripts/profile_startup.py
```

### Database Migration
```bash
python src/database/migrate_to_postgres.py
```

### Generate Certificates
```bash
bash scripts/generate_certs.sh
```

## 📊 Performance

- **Startup Time**: < 2 seconds (JSON mode)
- **Startup Time**: ~5 seconds (PostgreSQL mode)
- **Memory Usage**: ~50-100 MB
- **Concurrent Users**: 100+ supported

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **IBM Watson AI** - AI-powered chat summarization
- **Flet** - Modern Python UI framework
- **Giphy** - GIF integration
- **PostgreSQL** - Robust database support

## 📞 Support

- 📖 Check the [documentation](docs/)
- 🐛 Report issues on GitHub
- 💬 Join our community chat

## 🎯 Roadmap

- [ ] Voice messages
- [ ] Video calls
- [ ] Mobile app (iOS/Android)
- [ ] End-to-end encryption
- [ ] Message reactions
- [ ] Thread replies
- [ ] User presence indicators
- [ ] Rich text formatting

## 📈 Version History

- **v1.0.0** - Initial release with core features
- **v1.1.0** - Added PostgreSQL support
- **v1.2.0** - Performance optimizations
- **v2.0.0** - Project restructure & security improvements

---

**Made with ❤️ and Bob** 🤖

Last Updated: 2026-05-03