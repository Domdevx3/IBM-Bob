"""
Database module - JSON-based storage
Exports the JSON database manager for use throughout the application
"""

from src.database.json_manager import db_manager, JSONDatabaseManager

__all__ = ['db_manager', 'JSONDatabaseManager']

# Made with Bob - 100% JSON Storage