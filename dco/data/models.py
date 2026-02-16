"""
Database models for DCO.
Defines the schema for games, analyses, practice items, and more.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, Column, Integer, String, Float, DateTime, 
    Text, JSON, Enum, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class GameSource(enum.Enum):
    """Source of the game."""
    ENGINE_PLAY = "engine_play"
    PGN_IMPORT = "pgn_import"


class MoveClassification(enum.Enum):
    """Classification of a move."""
    BOOK = "book"
    BEST = "best"
    EXCELLENT = "excellent"
    GOOD = "good"
    INACCURACY = "inaccuracy"
    MISTAKE = "mistake"
    BLUNDER = "blunder"
    CRITICAL = "critical"
    BRILLIANT = "brilliant"


class PracticeCategory(enum.Enum):
    """Category of practice item."""
    BLUNDER = "blunder"
    MISTAKE = "mistake"
    INACCURACY = "inaccuracy"
    CRITICAL = "critical"


class PracticeResult(enum.Enum):
    """Result of a practice attempt."""
    PASS_FIRST_TRY = "pass_first_try"
    PASS = "pass"
    FAIL = "fail"


class SessionType(enum.Enum):
    """Type of training session."""
    PRACTICE = "practice"
    PUZZLE = "puzzle"
    PLAY = "play"


class Game(Base):
    """Represents a chess game."""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(Enum(GameSource, native_enum=False, length=20), nullable=False)
    
    # PGN headers
    event = Column(String(200))
    site = Column(String(200))
    date = Column(String(50))
    round = Column(String(20))
    white = Column(String(100))
    black = Column(String(100))
    result = Column(String(10))  # 1-0, 0-1, 1/2-1/2, *
    
    # Additional metadata
    white_elo = Column(Integer)
    black_elo = Column(Integer)
    time_control = Column(String(50))
    termination = Column(String(100))
    
    # Opening information (ECO)
    eco_code = Column(String(10))  # e.g., "C50"
    opening_name = Column(String(200))  # e.g., "Italian Game"
    opening_variation = Column(String(200))  # e.g., "Giuoco Piano"
    
    # Game content
    pgn_text = Column(Text, nullable=False)
    moves_san = Column(Text)  # Space-separated SAN moves for quick search
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="game", uselist=False)
    moves = relationship("Move", back_populates="game", cascade="all, delete-orphan")
    practice_items = relationship("PracticeItem", back_populates="game")
    
    # Indexes for searching
    __table_args__ = (
        Index('idx_game_white', 'white'),
        Index('idx_game_black', 'black'),
        Index('idx_game_date', 'date'),
        Index('idx_game_source', 'source'),
    )


class Analysis(Base):
    """Represents an analysis of a game."""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, unique=True)
    
    # Engine configuration
    engine_version = Column(String(100))
    depth = Column(Integer)
    time_per_move = Column(Float)  # seconds
    
    # Results
    accuracy_white = Column(Float)
    accuracy_black = Column(Float)
    perf_elo_white = Column(Integer)
    perf_elo_black = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    game = relationship("Game", back_populates="analysis")
    
    __table_args__ = (
        Index('idx_analysis_game', 'game_id'),
    )


class Move(Base):
    """Represents a single move in a game."""
    __tablename__ = "moves"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    ply_index = Column(Integer, nullable=False)  # 0-based ply number
    
    # Move notation
    san = Column(String(20), nullable=False)
    uci = Column(String(10), nullable=False)
    
    # Position data
    fen_before = Column(String(100), nullable=False)
    fen_after = Column(String(100), nullable=False)
    
    # Evaluation data (in centipawns from White's perspective)
    eval_before_cp = Column(Integer)
    eval_best_cp = Column(Integer)  # If best move was played
    eval_after_cp = Column(Integer)
    
    # Best move info
    best_uci = Column(String(10))
    
    # Classification
    classification = Column(Enum(MoveClassification, native_enum=False, length=20))
    is_book = Column(Boolean, default=False)
    is_critical = Column(Boolean, default=False)
    is_brilliant = Column(Boolean, default=False)
    
    # Optional comment or explanation
    comment = Column(Text)
    
    # Relationships
    game = relationship("Game", back_populates="moves")
    
    __table_args__ = (
        Index('idx_move_game_ply', 'game_id', 'ply_index'),
        Index('idx_move_classification', 'classification'),
    )


class PracticeItem(Base):
    """Represents a training position extracted from a game."""
    __tablename__ = "practice_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    source_ply_index = Column(Integer, nullable=False)
    
    # Position data
    fen_start = Column(String(100), nullable=False)
    side_to_move = Column(String(5), nullable=False)  # 'white' or 'black'
    
    # Target solution
    target_line_uci = Column(JSON, nullable=False)  # Array of UCI moves
    target_line_san = Column(JSON, nullable=False)  # Array of SAN moves
    
    # Categorization
    category = Column(Enum(PracticeCategory, native_enum=False, length=20), nullable=False)
    motif_tags = Column(JSON)  # Array of strings: ["fork", "pin", etc.]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    game = relationship("Game", back_populates="practice_items")
    progress = relationship("PracticeProgress", back_populates="item", uselist=False)
    
    __table_args__ = (
        Index('idx_practice_category', 'category'),
        Index('idx_practice_game', 'source_game_id'),
    )


class PracticeProgress(Base):
    """Tracks spaced repetition progress for a practice item."""
    __tablename__ = "practice_progress"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    practice_item_id = Column(Integer, ForeignKey("practice_items.id"), nullable=False, unique=True)
    
    # Spaced repetition data
    due_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    interval_days = Column(Float, default=1.0)
    ease_factor = Column(Float, default=2.5)
    repetitions = Column(Integer, default=0)
    lapses = Column(Integer, default=0)
    
    # Last attempt
    last_result = Column(Enum(PracticeResult, native_enum=False, length=20))
    
    # Statistics
    attempts_total = Column(Integer, default=0)
    attempts_first_try_correct = Column(Integer, default=0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    item = relationship("PracticeItem", back_populates="progress")
    
    __table_args__ = (
        Index('idx_progress_due', 'due_date'),
    )


class Session(Base):
    """Represents a training session."""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum(SessionType, native_enum=False, length=20), nullable=False)
    
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime)
    
    accuracy = Column(Float)  # 0-100
    notes = Column(Text)
    
    __table_args__ = (
        Index('idx_session_started', 'started_at'),
        Index('idx_session_type', 'type'),
    )


class Puzzle(Base):
    """Represents a chess puzzle."""
    __tablename__ = "puzzles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Position data
    fen = Column(String(100), nullable=False)
    side_to_move = Column(String(5), nullable=False)
    
    # Solution
    solution_line = Column(JSON, nullable=False)  # Array of UCI moves
    
    # Metadata
    theme_tags = Column(JSON)  # Array of strings
    rating = Column(Integer)
    source = Column(String(100))  # 'lichess', 'own_game', 'offline_pack', etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    attempts = relationship("PuzzleAttempt", back_populates="puzzle")
    
    __table_args__ = (
        Index('idx_puzzle_rating', 'rating'),
        Index('idx_puzzle_source', 'source'),
    )


class PuzzleAttempt(Base):
    """Tracks attempts at solving puzzles."""
    __tablename__ = "puzzle_attempts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    puzzle_id = Column(Integer, ForeignKey("puzzles.id"), nullable=False)
    
    attempt_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    success = Column(Boolean, nullable=False)
    hints_used = Column(Integer, default=0)
    
    # Relationships
    puzzle = relationship("Puzzle", back_populates="attempts")
    
    __table_args__ = (
        Index('idx_puzzle_attempt_puzzle', 'puzzle_id'),
    )
