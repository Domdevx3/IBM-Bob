"""
Database configuration - controls whether PostgreSQL is used
Set USE_POSTGRES=False to use JSON files (faster startup)
Set USE_POSTGRES=True to use PostgreSQL (production ready)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Toggle PostgreSQL usage - set to False for faster startup during development
USE_POSTGRES = os.getenv('USE_POSTGRES', 'false').lower() == 'true'

# Database connection settings
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5433'),
    'database': os.getenv('DB_NAME', 'chatdb'),
    'user': os.getenv('DB_USER', 'chatuser'),
    'password': os.getenv('DB_PASSWORD', 'chatpass123'),
}

def get_db_manager():
    """
    Get database manager only if PostgreSQL is enabled.
    Returns None if using JSON files.
    """
    if not USE_POSTGRES:
        return None
    
    # Lazy import - only load when PostgreSQL is actually used
    from src.database.database import db_manager
    return db_manager

# Made with Bob
