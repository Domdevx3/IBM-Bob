"""
JSON-Based Database Manager
100% Static JSON Storage - No External Database Required
Optimized for fast deployment in hackathons
Thread-safe with asyncio.Lock for concurrent operations
"""

import os
import json
import asyncio
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JSONDatabaseManager:
    """
    JSON-based database manager with async support.
    Stores all data in data/json/ directory.
    Thread-safe with locks to prevent write collisions.
    """
    
    def __init__(self, data_dir: str = "data/json"):
        """Initialize JSON database manager"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.users_file = self.data_dir / "usuarios.json"
        self.rooms_file = self.data_dir / "salas.json"
        self.messages_file = self.data_dir / "historial.json"
        self.pins_file = self.data_dir / "pines.json"
        
        # Async locks for thread-safe operations
        self._users_lock = asyncio.Lock()
        self._rooms_lock = asyncio.Lock()
        self._messages_lock = asyncio.Lock()
        self._pins_lock = asyncio.Lock()
        
        # Initialize files if they don't exist
        self._initialize_files()
        
        logger.info(f"✅ JSON Database initialized at {self.data_dir}")
    
    def _initialize_files(self):
        """Create empty JSON files if they don't exist"""
        # Users file
        if not self.users_file.exists():
            self._write_json(self.users_file, {})
            logger.info("Created usuarios.json")
        
        # Rooms file - with default rooms
        if not self.rooms_file.exists():
            default_rooms = [
                {
                    "id": self._generate_id(),
                    "name": "General",
                    "description": "General discussion channel",
                    "icon": "💬",
                    "created_at": datetime.utcnow().isoformat(),
                    "is_private": False
                },
                {
                    "id": self._generate_id(),
                    "name": "Random",
                    "description": "Random conversations and fun",
                    "icon": "🎲",
                    "created_at": datetime.utcnow().isoformat(),
                    "is_private": False
                },
                {
                    "id": self._generate_id(),
                    "name": "Tech",
                    "description": "Technology discussions",
                    "icon": "💻",
                    "created_at": datetime.utcnow().isoformat(),
                    "is_private": False
                }
            ]
            self._write_json(self.rooms_file, default_rooms)
            logger.info("Created salas.json with default rooms")
        
        # Messages file
        if not self.messages_file.exists():
            self._write_json(self.messages_file, {})
            logger.info("Created historial.json")
        
        # Pins file
        if not self.pins_file.exists():
            self._write_json(self.pins_file, {})
            logger.info("Created pines.json")
    
    def _generate_id(self) -> str:
        """Generate a unique ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _read_json(self, file_path: Path) -> Any:
        """Read JSON file safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error reading {file_path}: {e}")
            return {} if file_path != self.rooms_file else []
    
    def _write_json(self, file_path: Path, data: Any):
        """Write JSON file safely"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing {file_path}: {e}")
            raise
    
    # ============================================================================
    # USER OPERATIONS
    # ============================================================================
    
    async def create_user(self, username: str, password_hash: str, email: Optional[str] = None) -> Optional[Dict]:
        """Create a new user"""
        async with self._users_lock:
            try:
                users = self._read_json(self.users_file)
                
                if username in users:
                    logger.warning(f"User {username} already exists")
                    return None
                
                user = {
                    "id": self._generate_id(),
                    "username": username,
                    "password_hash": password_hash,
                    "email": email,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_login": None,
                    "is_active": True,
                    "profile_picture": None,
                    "status": "offline"
                }
                
                users[username] = user
                self._write_json(self.users_file, users)
                
                logger.info(f"✅ User created: {username}")
                return user
            except Exception as e:
                logger.error(f"Error creating user: {e}")
                return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        async with self._users_lock:
            try:
                users = self._read_json(self.users_file)
                return users.get(username)
            except Exception as e:
                logger.error(f"Error getting user: {e}")
                return None
    
    async def update_user_status(self, username: str, status: str):
        """Update user status (online/offline)"""
        async with self._users_lock:
            try:
                users = self._read_json(self.users_file)
                if username in users:
                    users[username]["status"] = status
                    users[username]["last_login"] = datetime.utcnow().isoformat()
                    self._write_json(self.users_file, users)
                    logger.info(f"User {username} status updated to {status}")
            except Exception as e:
                logger.error(f"Error updating user status: {e}")
    
    # ============================================================================
    # ROOM OPERATIONS
    # ============================================================================
    
    async def get_all_rooms(self) -> List[Dict]:
        """Get all rooms"""
        async with self._rooms_lock:
            try:
                rooms = self._read_json(self.rooms_file)
                return rooms if isinstance(rooms, list) else []
            except Exception as e:
                logger.error(f"Error getting rooms: {e}")
                return []
    
    async def get_room_by_name(self, name: str) -> Optional[Dict]:
        """Get room by name"""
        async with self._rooms_lock:
            try:
                rooms = self._read_json(self.rooms_file)
                for room in rooms:
                    if room.get("name") == name:
                        return room
                return None
            except Exception as e:
                logger.error(f"Error getting room: {e}")
                return None
    
    async def get_room_by_id(self, room_id: str) -> Optional[Dict]:
        """Get room by ID"""
        async with self._rooms_lock:
            try:
                rooms = self._read_json(self.rooms_file)
                for room in rooms:
                    if room.get("id") == room_id:
                        return room
                return None
            except Exception as e:
                logger.error(f"Error getting room by ID: {e}")
                return None
    
    async def create_room(self, name: str, description: str = "", icon: str = "💬", 
                         created_by: Optional[str] = None) -> Optional[Dict]:
        """Create a new room"""
        async with self._rooms_lock:
            try:
                rooms = self._read_json(self.rooms_file)
                
                # Check if room already exists
                for room in rooms:
                    if room.get("name") == name:
                        logger.warning(f"Room {name} already exists")
                        return None
                
                room = {
                    "id": self._generate_id(),
                    "name": name,
                    "description": description,
                    "icon": icon,
                    "created_by": created_by,
                    "created_at": datetime.utcnow().isoformat(),
                    "is_private": False
                }
                
                rooms.append(room)
                self._write_json(self.rooms_file, rooms)
                
                # Initialize empty message history for this room
                async with self._messages_lock:
                    messages = self._read_json(self.messages_file)
                    if room["id"] not in messages:
                        messages[room["id"]] = []
                        self._write_json(self.messages_file, messages)
                
                logger.info(f"✅ Room created: {name}")
                return room
            except Exception as e:
                logger.error(f"Error creating room: {e}")
                return None
    
    # ============================================================================
    # MESSAGE OPERATIONS
    # ============================================================================
    
    async def create_message(self, room_id: str, user_id: Optional[str], username: str, 
                            content: str, message_type: str = 'text', 
                            media_url: Optional[str] = None) -> Optional[Dict]:
        """Create a new message"""
        async with self._messages_lock:
            try:
                messages = self._read_json(self.messages_file)
                
                # Ensure room exists in messages
                if room_id not in messages:
                    messages[room_id] = []
                
                message = {
                    "id": self._generate_id(),
                    "room_id": room_id,
                    "user_id": user_id,
                    "username": username,
                    "content": content,
                    "message_type": message_type,
                    "media_url": media_url,
                    "created_at": datetime.utcnow().isoformat(),
                    "edited_at": None,
                    "is_deleted": False,
                    "reply_to": None
                }
                
                messages[room_id].append(message)
                self._write_json(self.messages_file, messages)
                
                logger.info(f"✅ Message created in room {room_id} by {username}")
                return message
            except Exception as e:
                logger.error(f"Error creating message: {e}")
                return None
    
    async def get_room_messages(self, room_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get messages for a room"""
        async with self._messages_lock:
            try:
                messages = self._read_json(self.messages_file)
                room_messages = messages.get(room_id, [])
                
                # Filter out deleted messages
                active_messages = [m for m in room_messages if not m.get("is_deleted", False)]
                
                # Sort by created_at (newest first, then reverse for chronological order)
                active_messages.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                
                # Apply pagination
                paginated = active_messages[offset:offset + limit]
                
                # Return in chronological order (oldest first)
                return list(reversed(paginated))
            except Exception as e:
                logger.error(f"Error getting messages: {e}")
                return []
    
    async def search_messages(self, room_id: str, query: str, limit: int = 50) -> List[Dict]:
        """Search messages in a room"""
        async with self._messages_lock:
            try:
                messages = self._read_json(self.messages_file)
                room_messages = messages.get(room_id, [])
                
                # Filter by query and not deleted
                query_lower = query.lower()
                results = [
                    m for m in room_messages 
                    if not m.get("is_deleted", False) and query_lower in m.get("content", "").lower()
                ]
                
                # Sort by created_at (newest first)
                results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                
                return results[:limit]
            except Exception as e:
                logger.error(f"Error searching messages: {e}")
                return []
    
    # ============================================================================
    # PINNED MESSAGE OPERATIONS
    # ============================================================================
    
    async def pin_message(self, message_id: str, room_id: str, pinned_by: Optional[str] = None) -> Optional[Dict]:
        """Pin a message"""
        async with self._pins_lock:
            try:
                pins = self._read_json(self.pins_file)
                
                # Ensure room exists in pins
                if room_id not in pins:
                    pins[room_id] = []
                
                # Check if already pinned
                for pin in pins[room_id]:
                    if pin.get("message_id") == message_id:
                        logger.warning(f"Message {message_id} already pinned")
                        return pin
                
                pin = {
                    "id": self._generate_id(),
                    "message_id": message_id,
                    "room_id": room_id,
                    "pinned_by": pinned_by,
                    "pinned_at": datetime.utcnow().isoformat()
                }
                
                pins[room_id].append(pin)
                self._write_json(self.pins_file, pins)
                
                logger.info(f"✅ Message {message_id} pinned in room {room_id}")
                return pin
            except Exception as e:
                logger.error(f"Error pinning message: {e}")
                return None
    
    async def unpin_message(self, message_id: str, room_id: str) -> bool:
        """Unpin a message"""
        async with self._pins_lock:
            try:
                pins = self._read_json(self.pins_file)
                
                if room_id not in pins:
                    return False
                
                # Remove the pin
                original_count = len(pins[room_id])
                pins[room_id] = [p for p in pins[room_id] if p.get("message_id") != message_id]
                
                if len(pins[room_id]) < original_count:
                    self._write_json(self.pins_file, pins)
                    logger.info(f"✅ Message {message_id} unpinned from room {room_id}")
                    return True
                
                return False
            except Exception as e:
                logger.error(f"Error unpinning message: {e}")
                return False
    
    async def get_pinned_messages(self, room_id: str) -> List[Dict[str, Any]]:
        """Get pinned messages for a room with full message details"""
        async with self._pins_lock:
            async with self._messages_lock:
                try:
                    pins = self._read_json(self.pins_file)
                    messages = self._read_json(self.messages_file)
                    
                    room_pins = pins.get(room_id, [])
                    room_messages = messages.get(room_id, [])
                    
                    # Create a message lookup dict
                    message_dict = {m["id"]: m for m in room_messages}
                    
                    # Combine pin info with message details
                    result = []
                    for pin in room_pins:
                        message_id = pin.get("message_id")
                        if message_id in message_dict:
                            result.append({
                                "message": message_dict[message_id],
                                "pinned_at": pin.get("pinned_at")
                            })
                    
                    # Sort by pinned_at (newest first)
                    result.sort(key=lambda x: x.get("pinned_at", ""), reverse=True)
                    
                    return result
                except Exception as e:
                    logger.error(f"Error getting pinned messages: {e}")
                    return []
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    async def test_connection(self) -> bool:
        """Test if JSON storage is working"""
        try:
            # Try to read all files
            self._read_json(self.users_file)
            self._read_json(self.rooms_file)
            self._read_json(self.messages_file)
            self._read_json(self.pins_file)
            logger.info("✅ JSON storage connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ JSON storage connection test failed: {e}")
            return False
    
    async def close(self):
        """Close connections (no-op for JSON, but kept for compatibility)"""
        logger.info("JSON Database manager closed (no cleanup needed)")


# Singleton instance
db_manager = JSONDatabaseManager()

# Made with Bob - 100% JSON, Zero Database Dependencies