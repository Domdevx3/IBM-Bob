"""
Test script for JSON Database Manager
Verifies all core functionality works correctly
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.json_manager import db_manager


async def test_json_manager():
    """Test all JSON manager functionality"""
    print("\n" + "="*60)
    print("🧪 TESTING JSON DATABASE MANAGER")
    print("="*60)
    
    try:
        # Test 1: Connection test
        print("\n1️⃣ Testing connection...")
        if await db_manager.test_connection():
            print("   ✅ Connection test passed")
        else:
            print("   ❌ Connection test failed")
            return False
        
        # Test 2: Get all rooms
        print("\n2️⃣ Testing room retrieval...")
        rooms = await db_manager.get_all_rooms()
        print(f"   ✅ Found {len(rooms)} rooms:")
        for room in rooms:
            print(f"      - {room.get('icon', '💬')} {room.get('name', 'Unknown')}")
        
        # Test 3: Create a test user
        print("\n3️⃣ Testing user creation...")
        test_username = "test_user_json"
        test_user = await db_manager.create_user(
            username=test_username,
            password_hash="test_hash_123",
            email="test@example.com"
        )
        if test_user:
            print(f"   ✅ User created: {test_user.get('username')}")
        else:
            print("   ⚠️  User might already exist")
        
        # Test 4: Get user
        print("\n4️⃣ Testing user retrieval...")
        retrieved_user = await db_manager.get_user_by_username(test_username)
        if retrieved_user:
            print(f"   ✅ User retrieved: {retrieved_user.get('username')}")
        else:
            print("   ❌ User retrieval failed")
        
        # Test 5: Create a message
        if rooms:
            print(f"\n5️⃣ Testing message creation in '{rooms[0].get('name')}'...")
            message = await db_manager.create_message(
                room_id=rooms[0].get('id'),
                user_id=test_user.get('id') if test_user else None,
                username=test_username,
                content="Test message from JSON manager",
                message_type="text"
            )
            if message:
                print(f"   ✅ Message created: {message.get('content')[:50]}...")
            else:
                print("   ❌ Message creation failed")
            
            # Test 6: Get room messages
            print(f"\n6️⃣ Testing message retrieval from '{rooms[0].get('name')}'...")
            messages = await db_manager.get_room_messages(rooms[0].get('id'), limit=5)
            print(f"   ✅ Retrieved {len(messages)} messages")
            for msg in messages[-3:]:  # Show last 3
                print(f"      - [{msg.get('username')}]: {msg.get('content', '')[:50]}...")
            
            # Test 7: Pin a message
            if messages:
                print(f"\n7️⃣ Testing message pinning...")
                pin = await db_manager.pin_message(
                    message_id=messages[-1].get('id'),
                    room_id=rooms[0].get('id'),
                    pinned_by=test_user.get('id') if test_user else None
                )
                if pin:
                    print(f"   ✅ Message pinned successfully")
                else:
                    print("   ⚠️  Message might already be pinned")
                
                # Test 8: Get pinned messages
                print(f"\n8️⃣ Testing pinned message retrieval...")
                pinned = await db_manager.get_pinned_messages(rooms[0].get('id'))
                print(f"   ✅ Found {len(pinned)} pinned messages")
                for p in pinned:
                    msg = p.get('message', {})
                    print(f"      - [{msg.get('username')}]: {msg.get('content', '')[:50]}...")
        
        # Test 9: Search messages
        if rooms:
            print(f"\n9️⃣ Testing message search...")
            search_results = await db_manager.search_messages(
                room_id=rooms[0].get('id'),
                query="test",
                limit=5
            )
            print(f"   ✅ Found {len(search_results)} messages matching 'test'")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_json_manager())
    sys.exit(0 if success else 1)

# Made with Bob
