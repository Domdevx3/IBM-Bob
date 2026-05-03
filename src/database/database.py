"""
PostgreSQL Database Connection and ORM Module
Handles real-time message storage and retrieval
Optimized for fast startup with lazy initialization
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from contextlib import asynccontextmanager
import logging

# Configure logging - reduced for faster startup
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Type checking imports - no runtime cost
if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
    from sqlalchemy.orm import DeclarativeMeta

# Global state for lazy initialization
_db_initialized = False
_db_manager_instance = None


class LazyDatabaseManager:
    """
    Lazy-loading database manager that only initializes when first used.
    This significantly improves app startup time.
    """
    
    def __init__(self):
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5433')
        self.db_name = os.getenv('DB_NAME', 'chatdb')
        self.db_user = os.getenv('DB_USER', 'chatuser')
        self.db_password = os.getenv('DB_PASSWORD', 'chatpass123')
        
        # Lazy-loaded attributes
        self._async_engine = None
        self._async_session_maker = None
        self._models_loaded = False
        self._Base = None
        self._User = None
        self._Room = None
        self._Message = None
        self._PinnedMessage = None
        
    def _load_sqlalchemy(self):
        """Load SQLAlchemy only when needed"""
        if self._models_loaded:
            return
            
        try:
            from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, ForeignKey, Index
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
            from sqlalchemy.orm import declarative_base, relationship
            from sqlalchemy.dialects.postgresql import UUID
            from sqlalchemy import select, and_, desc, func
            import uuid
            
            # Store in instance
            self._sqlalchemy = {
                'create_engine': create_engine,
                'Column': Column,
                'String': String,
                'Boolean': Boolean,
                'DateTime': DateTime,
                'Text': Text,
                'ForeignKey': ForeignKey,
                'Index': Index,
                'create_async_engine': create_async_engine,
                'AsyncSession': AsyncSession,
                'async_sessionmaker': async_sessionmaker,
                'declarative_base': declarative_base,
                'relationship': relationship,
                'UUID': UUID,
                'select': select,
                'and_': and_,
                'desc': desc,
                'func': func,
                'uuid': uuid
            }
            
            # Create Base
            self._Base = declarative_base()
            self._define_models()
            self._models_loaded = True
            
        except ImportError as e:
            logger.error(f"Failed to import SQLAlchemy: {e}")
            raise
    
    def _define_models(self):
        """Define ORM models"""
        sa = self._sqlalchemy
        Base = self._Base
        
        # User Model
        class User(Base):
            __tablename__ = 'users'
            id = sa['Column'](sa['UUID'](as_uuid=True), primary_key=True, default=sa['uuid'].uuid4)
            username = sa['Column'](sa['String'](50), unique=True, nullable=False, index=True)
            password_hash = sa['Column'](sa['String'](255), nullable=False)
            email = sa['Column'](sa['String'](100))
            created_at = sa['Column'](sa['DateTime'](timezone=True), default=datetime.utcnow)
            last_login = sa['Column'](sa['DateTime'](timezone=True))
            is_active = sa['Column'](sa['Boolean'], default=True)
            profile_picture = sa['Column'](sa['Text'])
            status = sa['Column'](sa['String'](50), default='offline')
        
        # Room Model
        class Room(Base):
            __tablename__ = 'rooms'
            id = sa['Column'](sa['UUID'](as_uuid=True), primary_key=True, default=sa['uuid'].uuid4)
            name = sa['Column'](sa['String'](100), unique=True, nullable=False, index=True)
            description = sa['Column'](sa['Text'])
            created_by = sa['Column'](sa['UUID'](as_uuid=True), sa['ForeignKey']('users.id', ondelete='SET NULL'))
            created_at = sa['Column'](sa['DateTime'](timezone=True), default=datetime.utcnow)
            is_private = sa['Column'](sa['Boolean'], default=False)
            icon = sa['Column'](sa['String'](50), default='💬')
        
        # Message Model
        class Message(Base):
            __tablename__ = 'messages'
            id = sa['Column'](sa['UUID'](as_uuid=True), primary_key=True, default=sa['uuid'].uuid4)
            room_id = sa['Column'](sa['UUID'](as_uuid=True), sa['ForeignKey']('rooms.id', ondelete='CASCADE'), nullable=False)
            user_id = sa['Column'](sa['UUID'](as_uuid=True), sa['ForeignKey']('users.id', ondelete='SET NULL'))
            username = sa['Column'](sa['String'](50), nullable=False)
            content = sa['Column'](sa['Text'], nullable=False)
            message_type = sa['Column'](sa['String'](20), default='text')
            media_url = sa['Column'](sa['Text'])
            created_at = sa['Column'](sa['DateTime'](timezone=True), default=datetime.utcnow, index=True)
            edited_at = sa['Column'](sa['DateTime'](timezone=True))
            is_deleted = sa['Column'](sa['Boolean'], default=False)
            reply_to = sa['Column'](sa['UUID'](as_uuid=True), sa['ForeignKey']('messages.id', ondelete='SET NULL'))
        
        # PinnedMessage Model
        class PinnedMessage(Base):
            __tablename__ = 'pinned_messages'
            id = sa['Column'](sa['UUID'](as_uuid=True), primary_key=True, default=sa['uuid'].uuid4)
            message_id = sa['Column'](sa['UUID'](as_uuid=True), sa['ForeignKey']('messages.id', ondelete='CASCADE'), nullable=False)
            room_id = sa['Column'](sa['UUID'](as_uuid=True), sa['ForeignKey']('rooms.id', ondelete='CASCADE'), nullable=False)
            pinned_by = sa['Column'](sa['UUID'](as_uuid=True), sa['ForeignKey']('users.id', ondelete='SET NULL'))
            pinned_at = sa['Column'](sa['DateTime'](timezone=True), default=datetime.utcnow)
        
        self._User = User
        self._Room = Room
        self._Message = Message
        self._PinnedMessage = PinnedMessage
    
    def _initialize_engine(self):
        """Initialize async engine only when needed"""
        if self._async_engine is not None:
            return
        
        self._load_sqlalchemy()
        
        async_url = f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        self._async_engine = self._sqlalchemy['create_async_engine'](
            async_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,  # Reduced pool size for faster startup
            max_overflow=10
        )
        
        self._async_session_maker = self._sqlalchemy['async_sessionmaker'](
            self._async_engine,
            class_=self._sqlalchemy['AsyncSession'],
            expire_on_commit=False
        )
        
        logger.info(f"Database engine initialized: {self.db_host}:{self.db_port}/{self.db_name}")
    
    @asynccontextmanager
    async def get_session(self):
        """Get an async database session - initializes on first use"""
        if self._async_session_maker is None:
            self._initialize_engine()
        
        async with self._async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Session error: {e}")
                raise
            finally:
                await session.close()
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            self._initialize_engine()
            async with self.get_session() as session:
                result = await session.execute(
                    self._sqlalchemy['select'](self._sqlalchemy['func'].count()).select_from(self._User)
                )
                count = result.scalar()
                logger.info(f"Database connection successful. Users count: {count}")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    # User Operations
    async def create_user(self, username: str, password_hash: str, email: Optional[str] = None):
        """Create a new user"""
        self._initialize_engine()
        try:
            async with self.get_session() as session:
                user = self._User(
                    username=username,
                    password_hash=password_hash,
                    email=email
                )
                session.add(user)
                await session.flush()
                await session.refresh(user)
                return user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def get_user_by_username(self, username: str):
        """Get user by username"""
        self._initialize_engine()
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    self._sqlalchemy['select'](self._User).where(self._User.username == username)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    # Room Operations
    async def get_all_rooms(self) -> List:
        """Get all rooms"""
        self._initialize_engine()
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    self._sqlalchemy['select'](self._Room).order_by(self._Room.created_at)
                )
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting rooms: {e}")
            return []
    
    async def get_room_by_name(self, name: str):
        """Get room by name"""
        self._initialize_engine()
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    self._sqlalchemy['select'](self._Room).where(self._Room.name == name)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting room: {e}")
            return None
    
    async def create_room(self, name: str, description: str = "", icon: str = "💬", created_by=None):
        """Create a new room"""
        self._initialize_engine()
        try:
            async with self.get_session() as session:
                room = self._Room(
                    name=name,
                    description=description,
                    icon=icon,
                    created_by=created_by
                )
                session.add(room)
                await session.flush()
                await session.refresh(room)
                return room
        except Exception as e:
            logger.error(f"Error creating room: {e}")
            return None
    
    # Message Operations
    async def create_message(self, room_id, user_id, username: str, content: str, 
                            message_type: str = 'text', media_url: Optional[str] = None):
        """Create a new message"""
        self._initialize_engine()
        try:
            async with self.get_session() as session:
                message = self._Message(
                    room_id=room_id,
                    user_id=user_id,
                    username=username,
                    content=content,
                    message_type=message_type,
                    media_url=media_url
                )
                session.add(message)
                await session.flush()
                await session.refresh(message)
                return message
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None
    
    async def get_room_messages(self, room_id, limit: int = 100, offset: int = 0) -> List:
        """Get messages for a room"""
        self._initialize_engine()
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    self._sqlalchemy['select'](self._Message)
                    .where(self._sqlalchemy['and_'](
                        self._Message.room_id == room_id,
                        self._Message.is_deleted == False
                    ))
                    .order_by(self._sqlalchemy['desc'](self._Message.created_at))
                    .limit(limit)
                    .offset(offset)
                )
                messages = list(result.scalars().all())
                return list(reversed(messages))
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    async def search_messages(self, room_id, query: str, limit: int = 50) -> List:
        """Search messages in a room"""
        self._initialize_engine()
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    self._sqlalchemy['select'](self._Message)
                    .where(self._sqlalchemy['and_'](
                        self._Message.room_id == room_id,
                        self._Message.is_deleted == False,
                        self._Message.content.ilike(f'%{query}%')
                    ))
                    .order_by(self._sqlalchemy['desc'](self._Message.created_at))
                    .limit(limit)
                )
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []
    
    async def pin_message(self, message_id, room_id, pinned_by=None):
        """Pin a message"""
        self._initialize_engine()
        try:
            async with self.get_session() as session:
                pinned = self._PinnedMessage(
                    message_id=message_id,
                    room_id=room_id,
                    pinned_by=pinned_by
                )
                session.add(pinned)
                await session.flush()
                await session.refresh(pinned)
                return pinned
        except Exception as e:
            logger.error(f"Error pinning message: {e}")
            return None
    
    async def get_pinned_messages(self, room_id) -> List[Dict[str, Any]]:
        """Get pinned messages for a room"""
        self._initialize_engine()
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    self._sqlalchemy['select'](self._Message, self._PinnedMessage)
                    .join(self._PinnedMessage, self._Message.id == self._PinnedMessage.message_id)
                    .where(self._PinnedMessage.room_id == room_id)
                    .order_by(self._sqlalchemy['desc'](self._PinnedMessage.pinned_at))
                )
                return [
                    {'message': msg, 'pinned_at': pinned.pinned_at}
                    for msg, pinned in result.all()
                ]
        except Exception as e:
            logger.error(f"Error getting pinned messages: {e}")
            return []
    
    async def close(self):
        """Close database connections"""
        if self._async_engine:
            await self._async_engine.dispose()
            logger.info("Database connections closed")


# Singleton instance - created but not initialized until first use
db_manager = LazyDatabaseManager()

# Made with Bob
