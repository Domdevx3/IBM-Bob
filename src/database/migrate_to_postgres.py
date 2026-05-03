"""
Migration script to move data from JSON files to PostgreSQL
Run this script after setting up the PostgreSQL database
"""

import json
import asyncio
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import hashlib

# Load environment variables
load_dotenv()

from database import db_manager, User, Room, Message

async def load_json_file(filepath: str):
    """Load data from JSON file"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}

async def migrate_users():
    """Migrate users from usuarios.json to PostgreSQL"""
    print("\n📤 Migrating users...")
    users_data = await load_json_file('data/usuarios.json')
    
    migrated = 0
    for username, user_info in users_data.items():
        try:
            # Check if user already exists
            existing_user = await db_manager.get_user_by_username(username)
            if existing_user:
                print(f"  ⏭️  User '{username}' already exists, skipping...")
                continue
            
            # Create user
            user = await db_manager.create_user(
                username=username,
                password_hash=user_info.get('password', ''),
                email=user_info.get('email')
            )
            
            if user:
                migrated += 1
                print(f"  ✅ Migrated user: {username}")
            else:
                print(f"  ❌ Failed to migrate user: {username}")
                
        except Exception as e:
            print(f"  ❌ Error migrating user {username}: {e}")
    
    print(f"✅ Users migration complete: {migrated} users migrated")
    return migrated

async def migrate_rooms():
    """Migrate rooms from salas.json to PostgreSQL"""
    print("\n📤 Migrating rooms...")
    rooms_data = await load_json_file('data/salas.json')
    
    migrated = 0
    room_mapping = {}  # Map old room names to new UUIDs
    
    for room_name, room_info in rooms_data.items():
        try:
            # Check if room already exists
            existing_room = await db_manager.get_room_by_name(room_name)
            if existing_room:
                print(f"  ⏭️  Room '{room_name}' already exists, skipping...")
                room_mapping[room_name] = existing_room.id
                continue
            
            # Create room
            room = await db_manager.create_room(
                name=room_name,
                description=room_info.get('description', ''),
                icon=room_info.get('icon', '💬')
            )
            
            if room:
                room_mapping[room_name] = room.id
                migrated += 1
                print(f"  ✅ Migrated room: {room_name}")
            else:
                print(f"  ❌ Failed to migrate room: {room_name}")
                
        except Exception as e:
            print(f"  ❌ Error migrating room {room_name}: {e}")
    
    print(f"✅ Rooms migration complete: {migrated} rooms migrated")
    return room_mapping

async def migrate_messages(room_mapping):
    """Migrate messages from historial.json to PostgreSQL"""
    print("\n📤 Migrating messages...")
    history_data = await load_json_file('data/historial.json')
    
    migrated = 0
    total_messages = sum(len(messages) for messages in history_data.values())
    
    for room_name, messages in history_data.items():
        if room_name not in room_mapping:
            print(f"  ⚠️  Room '{room_name}' not found in mapping, skipping messages...")
            continue
        
        room_id = room_mapping[room_name]
        print(f"  📝 Migrating {len(messages)} messages for room '{room_name}'...")
        
        for msg in messages:
            try:
                # Determine message type
                message_type = 'text'
                media_url = None
                content = msg.get('mensaje', '')
                
                if msg.get('tipo') == 'gif':
                    message_type = 'gif'
                    media_url = msg.get('url')
                elif msg.get('tipo') == 'sticker':
                    message_type = 'sticker'
                    media_url = msg.get('url')
                elif msg.get('tipo') == 'imagen':
                    message_type = 'image'
                    media_url = msg.get('url')
                
                # Create message
                message = await db_manager.create_message(
                    room_id=room_id,
                    user_id=None,  # We don't have user IDs in the old format
                    username=msg.get('usuario', 'Unknown'),
                    content=content,
                    message_type=message_type,
                    media_url=media_url
                )
                
                if message:
                    migrated += 1
                    if migrated % 50 == 0:
                        print(f"    Progress: {migrated}/{total_messages} messages migrated...")
                        
            except Exception as e:
                print(f"  ❌ Error migrating message: {e}")
    
    print(f"✅ Messages migration complete: {migrated}/{total_messages} messages migrated")
    return migrated

async def migrate_pinned_messages(room_mapping):
    """Migrate pinned messages from pines.json to PostgreSQL"""
    print("\n📤 Migrating pinned messages...")
    pins_data = await load_json_file('data/pines.json')
    
    migrated = 0
    
    for room_name, pinned_messages in pins_data.items():
        if room_name not in room_mapping:
            print(f"  ⚠️  Room '{room_name}' not found in mapping, skipping pins...")
            continue
        
        room_id = room_mapping[room_name]
        
        for pin_msg in pinned_messages:
            try:
                # First, we need to find the message in the database
                # Since we don't have message IDs from the old system,
                # we'll search by content and username
                messages = await db_manager.search_messages(
                    room_id=room_id,
                    query=pin_msg.get('mensaje', '')[:50],  # Search first 50 chars
                    limit=5
                )
                
                # Find exact match
                for msg in messages:
                    if (msg.content == pin_msg.get('mensaje', '') and 
                        msg.username == pin_msg.get('usuario', '')):
                        
                        # Pin the message
                        pinned = await db_manager.pin_message(
                            message_id=msg.id,
                            room_id=room_id
                        )
                        
                        if pinned:
                            migrated += 1
                            print(f"  ✅ Pinned message in room '{room_name}'")
                        break
                        
            except Exception as e:
                print(f"  ❌ Error migrating pinned message: {e}")
    
    print(f"✅ Pinned messages migration complete: {migrated} pins migrated")
    return migrated

async def main():
    """Main migration function"""
    print("=" * 60)
    print("🚀 Starting PostgreSQL Migration")
    print("=" * 60)
    
    # Test database connection
    print("\n🔌 Testing database connection...")
    if not await db_manager.test_connection():
        print("❌ Database connection failed. Please check your configuration.")
        return
    
    print("✅ Database connection successful!")
    
    # Run migrations
    try:
        # 1. Migrate users
        users_count = await migrate_users()
        
        # 2. Migrate rooms
        room_mapping = await migrate_rooms()
        
        # 3. Migrate messages
        messages_count = await migrate_messages(room_mapping)
        
        # 4. Migrate pinned messages
        pins_count = await migrate_pinned_messages(room_mapping)
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ Migration Complete!")
        print("=" * 60)
        print(f"📊 Summary:")
        print(f"  - Users migrated: {users_count}")
        print(f"  - Rooms migrated: {len(room_mapping)}")
        print(f"  - Messages migrated: {messages_count}")
        print(f"  - Pinned messages migrated: {pins_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close database connections
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
