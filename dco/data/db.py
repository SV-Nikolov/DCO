"""
Database initialization and session management for DCO.
"""

import os
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base


class Database:
    """Manages database connection and sessions."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Default: dco_data.db in the current directory
            db_path = os.path.join(os.getcwd(), "dco_data.db")
        
        self.db_path = db_path
        self.engine = None
        self.SessionLocal = None
        
    def init_db(self) -> None:
        """Initialize the database and create all tables."""
        # Create the database file directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Create engine
        self.engine = create_engine(
            f'sqlite:///{self.db_path}',
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False  # Set to True for SQL debugging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy Session object
        """
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        return self.SessionLocal()
    
    def close(self) -> None:
        """Close the database connection."""
        if self.engine:
            self.engine.dispose()


# Global database instance
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """
    Get the global database instance.
    
    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        _db_instance.init_db()
    return _db_instance


def init_database(db_path: Optional[str] = None) -> Database:
    """
    Initialize the global database instance.
    
    Args:
        db_path: Optional custom path to database file
        
    Returns:
        Database instance
    """
    global _db_instance
    _db_instance = Database(db_path)
    _db_instance.init_db()
    return _db_instance
