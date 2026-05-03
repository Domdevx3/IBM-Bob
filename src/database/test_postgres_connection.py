"""
Test PostgreSQL connection and database setup
Run this script to verify your PostgreSQL configuration
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database import db_manager

async def test_connection():
    """Test database connection and basic operations"""
    print("=" * 60)
    print("🔍 PostgreSQL Connection Test")
    print("=" * 60)
    
    # Display configuration
    print("\n📋 Database Configuration:")
    print(f"  Host: {os.getenv('DB_HOST', 'localhost')}")
    print(f"  Port: {os.getenv('DB_PORT', '5432')}")
    print(f"  Database: {os.getenv('DB_NAME', 'chatdb')}")
    print(f"  User: {os.getenv('DB_USER', 'chatuser')}")
    
    # Test connection
    print("\n🔌 Testing connection...")
    try:
        connected = await db_manager.test_connection()
        if connected:
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test basic operations
    print("\n🧪 Testing basic operations...")
    
    try:
        # Test 1: Get all rooms
        print("\n  1️⃣ Testing room retrieval...")
        rooms = await db_manager.get_all_rooms()
        print(f"     ✅ Found {len(rooms)} rooms")
        for room in rooms[:5]:  # Show first 5 rooms
            print(f"        - {room.icon} {room.name}")
        
        # Test 2: Get users count
        print("\n  2️⃣ Testing user retrieval...")
        test_user = await db_manager.get_user_by_username("test_user_12345")
        if test_user:
            print(f"     ✅ Test user found: {test_user.username}")
        else:
            print("     ℹ️  No test user found (this is normal for a fresh database)")
        
        # Test 3: Get messages from a room
        if rooms:
            print(f"\n  3️⃣ Testing message retrieval from '{rooms[0].name}'...")
            messages = await db_manager.get_room_messages(rooms[0].id, limit=5)
            print(f"     ✅ Found {len(messages)} messages")
            for msg in messages[:3]:  # Show first 3 messages
                print(f"        - [{msg.username}]: {msg.content[:50]}...")
        
        # Test 4: Test search functionality
        if rooms:
            print(f"\n  4️⃣ Testing message search...")
            search_results = await db_manager.search_messages(
                rooms[0].id, 
                "test", 
                limit=5
            )
            print(f"     ✅ Search returned {len(search_results)} results")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)
        print("\n💡 Next steps:")
        print("  1. Run 'python migrate_to_postgres.py' to migrate existing data")
        print("  2. Start your application with 'docker-compose up'")
        print("  3. Your chat app will now use PostgreSQL for real-time messages!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await db_manager.close()

async def main():
    """Main test function"""
    try:
        success = await test_connection()
        if not success:
            print("\n⚠️  Please check your PostgreSQL configuration and try again.")
            print("   Make sure PostgreSQL is running and accessible.")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
