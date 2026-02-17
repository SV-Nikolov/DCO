"""
Engine controller for playing against Stockfish.
Manages engine lifecycle, strength configuration, and move calculations.
"""

from __future__ import annotations

import chess
import chess.engine
from typing import Optional, List, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EngineController:
    """Controller for Stockfish chess engine."""
    
    # Elo to Stockfish skill level mapping
    ELO_TO_SKILL = {
        1000: (0, 1, 0.01),    # (skill, depth, time_seconds)
        1200: (2, 2, 0.02),
        1400: (4, 3, 0.05),
        1600: (6, 5, 0.1),
        1800: (8, 8, 0.2),
        2000: (10, 10, 0.5),
        2200: (13, 12, 1.0),
        2400: (16, 15, 2.0),
        2600: (18, 18, 5.0),
        2800: (20, 20, 10.0),
    }
    
    def __init__(self, stockfish_path: Optional[str] = None):
        """
        Initialize engine controller.
        
        Args:
            stockfish_path: Path to Stockfish executable. If None, searches standard locations.
        """
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.stockfish_path = stockfish_path or self._find_stockfish()
        self.current_elo = 2000
        self.current_skill = 10
        self.current_depth = 10
        self.current_time = 0.5
        
    def _find_stockfish(self) -> str:
        """Find Stockfish executable in standard locations."""
        possible_paths = [
            Path(__file__).parent.parent / "stockfish" / "stockfish-windows-x86-64-avx2.exe",
            Path("dco/stockfish/stockfish-windows-x86-64-avx2.exe"),
            Path("stockfish/stockfish.exe"),
            Path("stockfish/stockfish"),
            Path("stockfish"),
            Path("/usr/bin/stockfish"),
            Path("/usr/local/bin/stockfish"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path.absolute())
        
        # Default to "stockfish" and hope it's in PATH
        return "stockfish"
    
    def start(self) -> bool:
        """
        Start the chess engine.
        
        Returns:
            True if engine started successfully, False otherwise.
        """
        if self.engine is not None:
            logger.warning("Engine already started")
            return True
            
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            self._configure_engine()
            logger.info(f"Engine started: {self.stockfish_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to start engine: {e}")
            self.engine = None
            return False
    
    def quit(self):
        """Stop the chess engine."""
        if self.engine is not None:
            try:
                # Force terminate the engine process
                if hasattr(self.engine, 'process') and self.engine.process:
                    self.engine.process.terminate()
                    try:
                        self.engine.process.wait(timeout=1.0)
                    except:
                        self.engine.process.kill()  # Force kill if terminate doesn't work
                self.engine.quit()
                logger.info("Engine stopped")
            except Exception as e:
                logger.error(f"Error stopping engine: {e}")
            finally:
                self.engine = None
    
    def _configure_engine(self):
        """Configure engine UCI options."""
        if self.engine is None:
            return
            
        try:
            # Set skill level
            self.engine.configure({"Skill Level": self.current_skill})
            
            # Optional: Set threads and hash (can adjust based on system)
            self.engine.configure({"Threads": 1})
            self.engine.configure({"Hash": 64})  # MB
            
        except Exception as e:
            logger.warning(f"Could not configure engine options: {e}")
    
    def set_elo_strength(self, elo: int):
        """
        Set engine strength based on target Elo rating.
        
        Args:
            elo: Target Elo rating (1000-3200)
        """
        # Clamp Elo to valid range
        elo = max(1000, min(3200, elo))
        
        # Find closest mapping
        skill, depth, time_limit = self._map_elo_to_params(elo)
        
        self.current_elo = elo
        self.current_skill = skill
        self.current_depth = depth
        self.current_time = time_limit
        
        # Reconfigure engine if running
        if self.engine is not None:
            try:
                self.engine.configure({"Skill Level": skill})
                logger.info(f"Engine strength set to {elo} Elo (skill={skill}, depth={depth}, time={time_limit})")
            except Exception as e:
                logger.warning(f"Could not set skill level: {e}")
    
    def _map_elo_to_params(self, elo: int) -> Tuple[int, int, float]:
        """
        Map Elo rating to Stockfish parameters.
        
        Returns:
            Tuple of (skill_level, depth, time_limit_seconds)
        """
        # Find the two closest Elo ratings in our mapping
        elo_ratings = sorted(self.ELO_TO_SKILL.keys())
        
        if elo <= elo_ratings[0]:
            return self.ELO_TO_SKILL[elo_ratings[0]]
        if elo >= elo_ratings[-1]:
            return self.ELO_TO_SKILL[elo_ratings[-1]]
        
        # Interpolate between two closest ratings
        for i in range(len(elo_ratings) - 1):
            if elo_ratings[i] <= elo <= elo_ratings[i + 1]:
                lower_elo = elo_ratings[i]
                upper_elo = elo_ratings[i + 1]
                
                lower_params = self.ELO_TO_SKILL[lower_elo]
                upper_params = self.ELO_TO_SKILL[upper_elo]
                
                # Linear interpolation
                t = (elo - lower_elo) / (upper_elo - lower_elo)
                
                skill = int(lower_params[0] + t * (upper_params[0] - lower_params[0]))
                depth = int(lower_params[1] + t * (upper_params[1] - lower_params[1]))
                time_limit = lower_params[2] + t * (upper_params[2] - lower_params[2])
                
                return (skill, depth, time_limit)
        
        # Fallback
        return (10, 10, 0.5)
    
    def get_best_move(
        self,
        board: chess.Board,
        time_limit: Optional[float] = None
    ) -> Optional[chess.Move]:
        """
        Get the best move for the current position.
        
        Args:
            board: Current board position
            time_limit: Time limit in seconds (uses default if None)
            
        Returns:
            Best move or None if engine not available
        """
        if self.engine is None:
            logger.error("Engine not started")
            return None
        
        try:
            limit = chess.engine.Limit(
                time=time_limit or self.current_time,
                depth=self.current_depth
            )
            
            result = self.engine.play(board, limit)
            return result.move
            
        except Exception as e:
            logger.error(f"Error getting engine move: {e}")
            return None
    
    def get_top_moves(
        self,
        board: chess.Board,
        n: int = 3,
        time_limit: float = 1.0
    ) -> List[Tuple[chess.Move, int]]:
        """
        Get top N engine moves with evaluations.
        
        Args:
            board: Current board position
            n: Number of top moves to return
            time_limit: Analysis time limit in seconds
            
        Returns:
            List of (move, centipawn_score) tuples
        """
        if self.engine is None:
            logger.error("Engine not started")
            return []
        
        try:
            limit = chess.engine.Limit(time=time_limit)
            info = self.engine.analyse(board, limit, multipv=n)
            
            # Handle both single and multiple results
            if not isinstance(info, list):
                info = [info]
            
            top_moves = []
            for analysis in info:
                if "pv" in analysis and analysis["pv"]:
                    move = analysis["pv"][0]
                    score = analysis.get("score", chess.engine.PovScore(chess.engine.Cp(0), board.turn))
                    
                    # Convert score to centipawns from current player's perspective
                    cp_score = score.relative.score(mate_score=10000)
                    if cp_score is not None:
                        top_moves.append((move, cp_score))
            
            return top_moves
            
        except Exception as e:
            logger.error(f"Error analyzing position: {e}")
            return []
    
    def analyze_threats(
        self,
        board: chess.Board,
        time_limit: float = 0.5
    ) -> List[str]:
        """
        Analyze tactical threats in the position (for coach mode).
        
        Args:
            board: Current board position
            time_limit: Analysis time limit
            
        Returns:
            List of threat descriptions
        """
        if self.engine is None:
            return []
        
        threats = []
        
        try:
            # Get engine evaluation
            limit = chess.engine.Limit(time=time_limit)
            info = self.engine.analyse(board, limit)
            
            if "pv" in info and len(info["pv"]) > 0:
                best_move = info["pv"][0]
                score = info.get("score", chess.engine.PovScore(chess.engine.Cp(0), board.turn))
                
                # Check if move is a capture
                if board.is_capture(best_move):
                    threats.append(f"Threat: Capture on {chess.square_name(best_move.to_square)}")
                
                # Check if move gives check
                board_copy = board.copy()
                board_copy.push(best_move)
                if board_copy.is_check():
                    threats.append("Threat: Check")
                
                # Check if it's a strong tactical move (large eval swing)
                cp_score = score.relative.score(mate_score=10000)
                if cp_score and abs(cp_score) > 200:
                    threats.append(f"Strong tactical opportunity (eval: {cp_score/100:.1f})")
            
        except Exception as e:
            logger.error(f"Error analyzing threats: {e}")
        
        return threats
    
    def is_running(self) -> bool:
        """Check if engine is currently running."""
        return self.engine is not None
    
    def __del__(self):
        """Cleanup engine on deletion."""
        self.quit()
