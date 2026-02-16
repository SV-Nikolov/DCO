"""
Database initialization and session management for DCO.
"""

import os
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, text
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

        # Lightweight auto-migrations for schema and enum value fixes
        self._auto_migrate()
        
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

    def _auto_migrate(self) -> None:
        """Apply lightweight schema/data migrations for SQLite."""
        if not self.engine:
            return

        with self.engine.begin() as conn:
            # Add missing ECO columns to games
            games_cols = _get_table_columns(conn, "games")
            if "eco_code" not in games_cols:
                conn.execute(text("ALTER TABLE games ADD COLUMN eco_code VARCHAR(10)"))
            if "opening_name" not in games_cols:
                conn.execute(text("ALTER TABLE games ADD COLUMN opening_name VARCHAR(200)"))
            if "opening_variation" not in games_cols:
                conn.execute(text("ALTER TABLE games ADD COLUMN opening_variation VARCHAR(200)"))

            # Normalize move classification values to enum names (uppercase)
            moves_cols = _get_table_columns(conn, "moves")
            if "classification" in moves_cols:
                conn.execute(text("UPDATE moves SET classification = UPPER(classification)"))

            # Add missing practice progress columns
            progress_cols = _get_table_columns(conn, "practice_progress")
            if "consecutive_first_try" not in progress_cols:
                conn.execute(text("ALTER TABLE practice_progress ADD COLUMN consecutive_first_try INTEGER DEFAULT 0"))


def _get_table_columns(conn, table_name: str) -> set:
    """Return a set of column names for a table."""
    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
    return {row[1] for row in result}


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
