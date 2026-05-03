# 🔌 Integrate PostgreSQL with Your Flet App

## Current Status

Your app currently:
- ✅ Has PostgreSQL fully set up and ready
- ✅ Has a complete database module (`database.py`)
- ❌ **Does NOT save messages** - they're only in memory
- ❌ Messages disappear when app restarts

## Quick Integration Guide

### Step 1: Enable PostgreSQL

Edit `.env`:
```bash
USE_POSTGRES=true
```

### Step 2: Install PostgreSQL Dependencies

```bash
pip install -r requirements-postgres.txt
```

### Step 3: Start PostgreSQL

```bash
docker-compose up -d postgres
```

### Step 4: Add Database Integration to flet_app.py

Add this at the top of `flet_app.py` (after line 24):

```python
# Import database configuration
from db_config import USE_POSTGRES, get_db_manager

# Initialize database manager if enabled
db_manager = get_db_manager() if USE_POSTGRES else None
```

### Step 5: Modify `_on_send_message` Method

Replace the TODO comment (line 1574) with actual database saving:

```python
def _on_send_message(self, e):
    """Handle message sending with validation and smooth animation"""
    if not self.message_input.value or not self.message_input.value.strip():
        return
    
    message_text = self.message_input.value.strip()
    
    # Batch UI updates for better performance
    self.send_button.scale = 0.8
    
    # Check for commands
    if message_text.startswith("/"):
        self._handle_command(message_text)
        self.message_input.value = ""
        self.send_button.scale = 1.0
        self.page.update()
        return
    
    # Add message to list
    new_message = MessageBubble(
        self.alias or "Guest",
        message_text,
        datetime.now().strftime("%H:%M"),
        is_own=True,
        on_pin=self._on_pin_message
    )
    self.message_list.controls.append(new_message)
    
    # Clear input and reset button
    self.message_input.value = ""
    self.send_button.scale = 1.0
    
    # Single update call for better performance
    self.page.update()
    
    # Save to database (async, non-blocking)
    if db_manager:
        asyncio.create_task(self._save_message_to_db(message_text))
    else:
        # Fallback to JSON or just print
        print(f"[{self.current_room}] {self.alias}: {message_text}")
```

### Step 6: Add Database Save Method

Add this new method to the `FletChatApp` class:

```python
async def _save_message_to_db(self, message_text: str):
    """Save message to PostgreSQL database"""
    try:
        if not db_manager:
            return
        
        # Get current room
        room = await db_manager.get_room_by_name(self.current_room)
        if not room:
            # Create room if it doesn't exist
            room = await db_manager.create_room(
                name=self.current_room,
                description=f"Chat room {self.current_room}",
                icon="💬"
            )
        
        # Get current user (if logged in)
        user = None
        if self.alias:
            user = await db_manager.get_user_by_username(self.alias)
        
        # Save message
        await db_manager.create_message(
            room_id=room.id,
            user_id=user.id if user else None,
            username=self.alias or "Guest",
            content=message_text,
            message_type='text'
        )
        
        print(f"✅ Message saved to database: [{self.current_room}] {self.alias}: {message_text}")
        
    except Exception as e:
        print(f"❌ Error saving message to database: {e}")
```

### Step 7: Load Messages When Switching Rooms

Modify `_on_room_click` to load messages from database:

```python
def _on_room_click(self, room_name: str):
    """Handle room/channel switching"""
    # Update current room
    old_room = self.current_room
    self.current_room = room_name
    
    # Update room buttons
    for room, button in self.room_buttons.items():
        button.is_active = (room == room_name)
    
    # Clear messages
    self.message_list.controls.clear()
    
    # Load messages from database
    if db_manager:
        asyncio.create_task(self._load_room_messages(room_name))
    else:
        # Show system message
        self.message_list.controls.append(
            self._create_system_message(f"Cambiaste al canal #{room_name}")
        )
    
    self._show_notification(f"Canal cambiado a #{room_name}", "info")
    self.page.update()

async def _load_room_messages(self, room_name: str):
    """Load messages from database for a room"""
    try:
        if not db_manager:
            return
        
        # Get room
        room = await db_manager.get_room_by_name(room_name)
        if not room:
            self.message_list.controls.append(
                self._create_system_message(f"Cambiaste al canal #{room_name}")
            )
            self.page.update()
            return
        
        # Get messages
        messages = await db_manager.get_room_messages(room.id, limit=50)
        
        # Add system message
        self.message_list.controls.append(
            self._create_system_message(f"Cambiaste al canal #{room_name}")
        )
        
        # Add messages to UI
        for msg in messages:
            is_own = (msg.username == self.alias)
            message_bubble = MessageBubble(
                msg.username,
                msg.content,
                msg.created_at.strftime("%H:%M"),
                is_own=is_own,
                on_pin=self._on_pin_message
            )
            self.message_list.controls.append(message_bubble)
        
        self.page.update()
        print(f"✅ Loaded {len(messages)} messages from database")
        
    except Exception as e:
        print(f"❌ Error loading messages: {e}")
        self.message_list.controls.append(
            self._create_system_message(f"Cambiaste al canal #{room_name}")
        )
        self.page.update()
```

## 🎯 Complete Integration Example

Here's a minimal working example you can copy:

```python
# At the top of flet_app.py, after imports
from db_config import USE_POSTGRES, get_db_manager
db_manager = get_db_manager() if USE_POSTGRES else None

# In FletChatApp class, add these methods:

async def _save_message_to_db(self, message_text: str):
    """Save message to database"""
    if not db_manager:
        return
    try:
        room = await db_manager.get_room_by_name(self.current_room)
        if not room:
            room = await db_manager.create_room(self.current_room)
        
        await db_manager.create_message(
            room_id=room.id,
            user_id=None,
            username=self.alias or "Guest",
            content=message_text
        )
    except Exception as e:
        print(f"DB Error: {e}")

async def _load_room_messages(self, room_name: str):
    """Load messages from database"""
    if not db_manager:
        return
    try:
        room = await db_manager.get_room_by_name(room_name)
        if room:
            messages = await db_manager.get_room_messages(room.id, limit=50)
            for msg in messages:
                self.message_list.controls.append(
                    MessageBubble(
                        msg.username,
                        msg.content,
                        msg.created_at.strftime("%H:%M"),
                        is_own=(msg.username == self.alias)
                    )
                )
            self.page.update()
    except Exception as e:
        print(f"DB Error: {e}")

# Modify _on_send_message to call:
if db_manager:
    asyncio.create_task(self._save_message_to_db(message_text))

# Modify _on_room_click to call:
if db_manager:
    asyncio.create_task(self._load_room_messages(room_name))
```

## ✅ Testing

After integration:

```bash
# 1. Start PostgreSQL
docker-compose up -d postgres

# 2. Run your app
python3 flet_app.py

# 3. Send messages - they should be saved!

# 4. Check database
docker exec -it chat-postgres psql -U chatuser -d chatdb
SELECT * FROM messages;
```

## 🎉 Result

After integration:
- ✅ Messages persist in PostgreSQL
- ✅ Messages load when switching rooms
- ✅ Message history survives app restarts
- ✅ Real-time chat with database backing

---

**Note**: The database module is ready, you just need to call it from your app!