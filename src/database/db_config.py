"""
Database configuration - 100% JSON-based storage
No external database required - optimized for hackathon deployment
"""

import os
from dotenv import load_dotenv

load_dotenv()

# JSON storage directory
DATA_DIR = os.getenv('DATA_DIR', 'data/json')

def get_db_manager():
    """
    Get JSON database manager.
    Always returns the JSON-based manager for fast deployment.
    """
    from src.database.json_manager import db_manager
    return db_manager

# Made with Bob - 100% JSON, Zero Database Dependencies
