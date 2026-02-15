"""
Chess engine integration for DCO.
Handles communication with Stockfish using python-chess.
"""

import os
import shutil
import glob
from typing import Optional, List, Tuple
from dataclasses import dataclass
import chess
import chess.engine
from pathlib import Path


@dataclass
class EngineConfig:
    """Configuration for the chess engine."""
    path: Optional[str] = None
    threads: int = 1
    hash_mb: int = 128
    depth: Optional[int] = 20
    time_per_move: Optional[float] = None  # seconds
    multipv: int = 3  # Number of principal variations


@dataclass
class EngineEvaluation:
    """Result of engine evaluation."""
    score_cp: Optional[int]  # Centipawn score (from White's perspective)
    score_mate: Optional[int]  # Mate in N moves (None if not mate)
    best_move: Optional[chess.Move]
    pv_lines: List[List[chess.Move]]  # Principal variations
    depth: int


class ChessEngine:
    """Wrapper for Stockfish chess engine."""
    
    def __init__(self, config: Optional[EngineConfig] = None):
        """
        Initialize chess engine.
        
        Args:
            config: Engine configuration. If None, uses defaults.
        """
        self.config = config or EngineConfig()
        self.engine: Optional[chess.engine.SimpleEngine] = None
        
        # Auto-detect engine path if not provided
        if not self.config.path:
            self.config.path = self._find_stockfish()
    
    def _find_stockfish(self) -> Optional[str]:
        """
        Try to find Stockfish executable on the system.
        
        Returns:
            Path to Stockfish executable, or None if not found
        """
        # Common names for Stockfish executable
        exe_names = ['stockfish', 'stockfish.exe', 'stockfish_x64.exe']
        
        # Check if stockfish is in PATH
        for name in exe_names:
            path = shutil.which(name)
            if path:
                return path
        
        # Check common installation directories (Windows)
        common_paths = [
            r"C:\Program Files\Stockfish\stockfish.exe",
            r"C:\Program Files (x86)\Stockfish\stockfish.exe",
            os.path.expanduser("~\\AppData\\Local\\Stockfish\\stockfish.exe"),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Check current directory and subdirectories for any stockfish executable
        search_patterns = [
            "stockfish*.exe",
            "stockfish",
            "engines/stockfish*.exe",
            "engines/stockfish",
        ]
        
        for pattern in search_patterns:
            matches = glob.glob(pattern)
            if matches:
                # Return the first match
                return os.path.abspath(matches[0])
        
        return None
    
    def start(self) -> bool:
        """
        Start the chess engine.
        
        Returns:
            True if engine started successfully, False otherwise
        """
        if self.engine:
            return True
        
        if not self.config.path:
            raise RuntimeError(
                "Stockfish not found. Please install Stockfish and configure "
                "the path in settings, or place stockfish.exe in the application directory."
            )
        
        if not os.path.exists(self.config.path):
            raise RuntimeError(f"Stockfish not found at: {self.config.path}")
        
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.config.path)
            
            # Configure engine options
            self.engine.configure({
                "Threads": self.config.threads,
                "Hash": self.config.hash_mb,
            })
            
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to start Stockfish: {str(e)}")
    
    def stop(self):
        """Stop the chess engine."""
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
            finally:
                self.engine = None
    
    def evaluate(
        self, 
        board: chess.Board,
        depth: Optional[int] = None,
        time_limit: Optional[float] = None
    ) -> EngineEvaluation:
        """
        Evaluate a position.
        
        Args:
            board: Chess board to evaluate
            depth: Search depth (uses config default if None)
            time_limit: Time limit in seconds (uses config default if None)
            
        Returns:
            EngineEvaluation with score and best moves
        """
        if not self.engine:
            self.start()
        
        # Determine analysis limit
        if time_limit is not None:
            limit = chess.engine.Limit(time=time_limit)
        elif depth is not None:
            limit = chess.engine.Limit(depth=depth)
        elif self.config.time_per_move is not None:
            limit = chess.engine.Limit(time=self.config.time_per_move)
        else:
            limit = chess.engine.Limit(depth=self.config.depth or 20)
        
        # Analyze position
        info = self.engine.analyse(
            board, 
            limit,
            multipv=self.config.multipv
        )
        
        # Extract primary evaluation
        primary_info = info if isinstance(info, dict) else info[0]
        score = primary_info.get("score", chess.engine.Score(None, None))
        
        # Convert score to centipawns (from White's perspective)
        score_cp = None
        score_mate = None
        
        if score.is_mate():
            score_mate = score.white().mate()
        else:
            score_cp = score.white().score()
        
        # Extract best move and PV lines
        best_move = primary_info.get("pv", [None])[0]
        
        pv_lines = []
        if isinstance(info, list):
            for item in info:
                pv = item.get("pv", [])
                if pv:
                    pv_lines.append(pv)
        else:
            pv = primary_info.get("pv", [])
            if pv:
                pv_lines.append(pv)
        
        return EngineEvaluation(
            score_cp=score_cp,
            score_mate=score_mate,
            best_move=best_move,
            pv_lines=pv_lines,
            depth=primary_info.get("depth", 0)
        )
    
    def get_best_move(
        self, 
        board: chess.Board,
        depth: Optional[int] = None,
        time_limit: Optional[float] = None
    ) -> Optional[chess.Move]:
        """
        Get the best move for a position.
        
        Args:
            board: Chess board
            depth: Search depth
            time_limit: Time limit in seconds
            
        Returns:
            Best move, or None if no legal moves
        """
        eval_result = self.evaluate(board, depth, time_limit)
        return eval_result.best_move
    
    def play_move(
        self, 
        board: chess.Board,
        skill_level: Optional[int] = None,
        time_limit: Optional[float] = None
    ) -> Optional[chess.Move]:
        """
        Play a move at a specific skill level (for playing against the engine).
        
        Args:
            board: Chess board
            skill_level: Skill level 0-20 (None = maximum strength)
            time_limit: Time limit in seconds
            
        Returns:
            Move to play
        """
        if not self.engine:
            self.start()
        
        # Configure skill level if specified
        if skill_level is not None:
            self.engine.configure({"Skill Level": skill_level})
        
        # Determine time limit
        limit = chess.engine.Limit(time=time_limit or 1.0)
        
        # Get move
        result = self.engine.play(board, limit)
        
        # Reset skill level if it was set
        if skill_level is not None:
            self.engine.configure({"Skill Level": 20})
        
        return result.move
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def elo_to_skill_level(elo: int) -> int:
    """
    Convert Elo rating to Stockfish skill level (0-20).
    
    Args:
        elo: Elo rating (1000-3200)
        
    Returns:
        Skill level (0-20)
    """
    # Rough mapping: 1000 Elo = skill 0, 3200 Elo = skill 20
    # Linear interpolation
    elo = max(1000, min(3200, elo))
    skill = int((elo - 1000) / (3200 - 1000) * 20)
    return max(0, min(20, skill))


def skill_level_to_elo(skill: int) -> int:
    """
    Convert Stockfish skill level to approximate Elo rating.
    
    Args:
        skill: Skill level (0-20)
        
    Returns:
        Approximate Elo rating
    """
    skill = max(0, min(20, skill))
    elo = 1000 + int(skill / 20 * (3200 - 1000))
    return elo
