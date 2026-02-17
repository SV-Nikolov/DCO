"""
Database initialization and session management for DCO.
"""

import os
import shutil
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
            # Default: data/db/dco_data.db in the project directory
            db_path = os.path.join(os.getcwd(), "data", "db", "dco_data.db")
        
        self.db_path = db_path
        self.engine = None
        self.SessionLocal = None
        
    def init_db(self) -> None:
        """Initialize the database and create all tables."""
        # Create the database file directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        # Migrate legacy database if needed
        self._migrate_legacy_db_if_needed()
        
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
        
        # Create sample puzzles if none exist
        self._create_sample_puzzles_if_empty()
        
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

    def _migrate_legacy_db_if_needed(self) -> None:
        """Move legacy root database into data/db if needed."""
        default_path = os.path.join(os.getcwd(), "data", "db", "dco_data.db")
        legacy_path = os.path.join(os.getcwd(), "dco_data.db")

        if self.db_path != default_path:
            return

        if not os.path.exists(legacy_path):
            return

        if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0:
            return

        try:
            shutil.copy2(legacy_path, self.db_path)
            print("Migrated legacy database to data/db/dco_data.db")
        except Exception as exc:
            print(f"Failed to migrate legacy database: {exc}")

    def _create_sample_puzzles_if_empty(self) -> None:
        """Create sample puzzles if the database is empty."""
        session = self.get_session()
        try:
            # Check if there are any puzzles
            from .models import Puzzle, PuzzleTheme
            puzzle_count = session.query(Puzzle).count()
            
            if puzzle_count == 0:
                # Create sample puzzles
                sample_puzzles = [
                    {
                        "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
                        "solution": ["h5f7"],
                        "theme": PuzzleTheme.MATE,
                        "rating": 800,
                    },
                    {
                        "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5",
                        "solution": ["c4f7", "e8f7", "f3g5", "f7e8", "d1h5"],
                        "theme": PuzzleTheme.TACTIC,
                        "rating": 1200,
                    },
                    {
                        "fen": "r1bqkb1r/pppppppp/2n2n2/8/3PP3/2N5/PPP2PPP/R1BQKBNR b KQkq - 1 3",
                        "solution": ["f6e4"],
                        "theme": PuzzleTheme.MATERIAL,
                        "rating": 1000,
                    },
                    {
                        "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4",
                        "solution": ["f3g5", "d7d5", "g5f7"],
                        "theme": PuzzleTheme.TACTIC,
                        "rating": 1400,
                    },
                    {
                        "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2BPP3/5N2/PPP2PPP/RNBQK2R b KQkq - 0 5",
                        "solution": ["c6d4", "f3d4", "c5d4"],
                        "theme": PuzzleTheme.TACTIC,
                        "rating": 1500,
                    },
                    {
                        "fen": "r2qk2r/ppp2ppp/2np1n2/2b1p1B1/2B1P1b1/3P1N2/PPP2PPP/RN1QK2R w KQkq - 0 7",
                        "solution": ["c4f7", "e8f7", "f3e5"],
                        "theme": PuzzleTheme.MATERIAL,
                        "rating": 1600,
                    },
                    {
                        "fen": "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 0 3",
                        "solution": ["d1f3", "d7d6", "c4f7"],
                        "theme": PuzzleTheme.MATE,
                        "rating": 700,
                    },
                    {
                        "fen": "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
                        "solution": ["c6d4"],
                        "theme": PuzzleTheme.TACTIC,
                        "rating": 1300,
                    },
                ]
                
                from .models import PuzzleProgress
                from datetime import datetime
                import chess
                
                for puzzle_data in sample_puzzles:
                    try:
                        board = chess.Board(puzzle_data["fen"])
                        side_to_move = "white" if board.turn else "black"
                        
                        puzzle = Puzzle(
                            fen=puzzle_data["fen"],
                            side_to_move=side_to_move,
                            solution_line=puzzle_data["solution"],
                            theme=puzzle_data["theme"],
                            rating=puzzle_data["rating"],
                            source="sample",
                            created_at=datetime.utcnow(),
                        )
                        session.add(puzzle)
                        session.flush()
                        
                        progress = PuzzleProgress(
                            puzzle_id=puzzle.id,
                            due_date=datetime.utcnow(),
                        )
                        session.add(progress)
                    except Exception:
                        pass
                
                session.commit()
        except Exception:
            pass
        finally:
            session.close()


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
