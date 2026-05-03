# PostgreSQL Setup Guide for Real-Time Messages

## 🎉 Setup Complete!

Your chat application is now configured to use PostgreSQL for handling real-time messages. Here's what has been set up:

## 📦 What Was Created

### 1. **Database Configuration**
- **docker-compose.yml**: Added PostgreSQL 16 service
- **init_db.sql**: Database schema with tables for users, rooms, messages, pins, and notifications
- **.env**: Database credentials and connection settings

### 2. **Database Module**
- **database.py**: Complete ORM module with SQLAlchemy
  - User management
  - Room/channel management
  - Message CRUD operations
  - Real-time message retrieval
  - Search functionality
  - Pinned messages support

### 3. **Migration Tools**
- **migrate_to_postgres.py**: Script to migrate existing JSON data to PostgreSQL
- **test_postgres_connection.py**: Connection testing utility

## 🗄️ Database Schema

### Tables Created:
1. **users** - User accounts and authentication
2. **rooms** - Chat rooms/channels
3. **messages** - All chat messages with media support
4. **pinned_messages** - Pinned messages per room
5. **room_members** - Room membership tracking
6. **user_sessions** - Active user sessions
7. **notifications** - User notifications

### Features:
- ✅ UUID primary keys for scalability
- ✅ Timestamps with timezone support
- ✅ Soft delete for messages
- ✅ Indexed queries for performance
- ✅ Foreign key relationships
- ✅ Support for text, images, GIFs, stickers

## 🚀 Getting Started

### Step 1: Start PostgreSQL
```bash
docker-compose up -d postgres
```

### Step 2: Install Dependencies
```bash
# Activate your virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install PostgreSQL dependencies
pip install -r requirements-server.txt
```

### Step 3: Test Connection
```bash
python3 test_postgres_connection.py
```

### Step 4: Migrate Existing Data (Optional)
If you have existing data in JSON files:
```bash
python3 migrate_to_postgres.py
```

### Step 5: Start Your Application
```bash
# Start all services
docker-compose up -d

# Or start without Docker
python3 flet_app.py
```

## 🔧 Configuration

### Environment Variables (.env)
```env
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5433          # Using 5433 to avoid conflict with local PostgreSQL
DB_NAME=chatdb
DB_USER=chatuser
DB_PASSWORD=chatpass123
```

### Docker Configuration
- **Host Port**: 5433 (mapped to container port 5432)
- **Volume**: `postgres_data` for data persistence
- **Network**: `chat-network` for service communication
- **Health Check**: Automatic health monitoring

## 💻 Using the Database Module

### Example: Create a Message
```python
from database import db_manager
import asyncio

async def send_message():
    message = await db_manager.create_message(
        room_id=room_uuid,
        user_id=user_uuid,
        username="john_doe",
        content="Hello, World!",
        message_type="text"
    )
    print(f"Message created: {message.id}")

asyncio.run(send_message())
```

### Example: Get Room Messages
```python
async def get_messages():
    messages = await db_manager.get_room_messages(
        room_id=room_uuid,
        limit=50
    )
    for msg in messages:
        print(f"[{msg.username}]: {msg.content}")

asyncio.run(get_messages())
```

### Example: Search Messages
```python
async def search():
    results = await db_manager.search_messages(
        room_id=room_uuid,
        query="hello",
        limit=20
    )
    print(f"Found {len(results)} messages")

asyncio.run(search())
```

## 🔍 Database Management

### Connect to PostgreSQL CLI
```bash
docker exec -it chat-postgres psql -U chatuser -d chatdb
```

### Useful SQL Commands
```sql
-- View all tables
\dt

-- View table structure
\d messages

-- Count messages
SELECT COUNT(*) FROM messages;

-- View recent messages
SELECT username, content, created_at 
FROM messages 
ORDER BY created_at DESC 
LIMIT 10;

-- Search messages
SELECT * FROM messages 
WHERE content ILIKE '%search_term%';
```

### Backup Database
```bash
docker exec chat-postgres pg_dump -U chatuser chatdb > backup.sql
```

### Restore Database
```bash
docker exec -i chat-postgres psql -U chatuser chatdb < backup.sql
```

## 📊 Performance Features

### Indexes Created:
- Message room and timestamp indexes for fast retrieval
- User and room lookup indexes
- Search optimization indexes
- Notification filtering indexes

### Query Optimization:
- Async operations for non-blocking I/O
- Connection pooling with SQLAlchemy
- Prepared statements for security
- Efficient pagination support

## 🔐 Security Features

- Password hashing for user authentication
- SQL injection prevention via ORM
- Parameterized queries
- Session token management
- Soft delete for data recovery

## 🐛 Troubleshooting

### Port Already in Use
If port 5432 is already in use (local PostgreSQL):
- The setup uses port 5433 on the host
- Update `.env` if needed: `DB_PORT=5433`

### Connection Refused
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# View logs
docker logs chat-postgres

# Restart container
docker-compose restart postgres
```

### Migration Issues
```bash
# Check existing data
ls -la data/

# Verify JSON files
cat data/usuarios.json
cat data/salas.json
cat data/historial.json
```

## 📈 Next Steps

1. **Integrate with Flet App**: Update `flet_app.py` to use `database.py` instead of JSON files
2. **Add Real-Time Updates**: Implement WebSocket notifications for new messages
3. **Add User Presence**: Track online/offline status in real-time
4. **Implement Typing Indicators**: Show when users are typing
5. **Add Message Reactions**: Store emoji reactions in the database
6. **File Uploads**: Store file metadata and URLs
7. **Message Threading**: Implement reply chains
8. **User Profiles**: Expand user information and settings

## 🎯 Benefits of PostgreSQL

✅ **Scalability**: Handle millions of messages efficiently
✅ **ACID Compliance**: Data integrity and consistency
✅ **Real-Time Queries**: Fast message retrieval and search
✅ **Concurrent Users**: Support multiple simultaneous connections
✅ **Data Persistence**: Reliable storage with backups
✅ **Advanced Features**: Full-text search, JSON support, triggers
✅ **Production Ready**: Battle-tested database system

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Docker PostgreSQL](https://hub.docker.com/_/postgres)
- [Async PostgreSQL with Python](https://www.psycopg.org/psycopg3/docs/)

---

**Made with ❤️ by Bob**

For questions or issues, check the logs:
```bash
docker logs chat-postgres
docker logs chat-server
docker logs chat-client-flet