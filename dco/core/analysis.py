"""
Game analysis functionality for DCO.
Analyzes games move-by-move and classifies moves.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
import chess
import chess.pgn
import io

from .engine import ChessEngine, EngineConfig, EngineEvaluation
from .classification import classify_move, MoveClassification
from .accuracy import compute_accuracy
from ..data.models import Game, Analysis, Move, GameSource


@dataclass
class MoveAnalysis:
    """Analysis result for a single move."""
    ply_index: int
    san: str
    uci: str
    fen_before: str
    fen_after: str
    eval_before_cp: Optional[int]
    eval_best_cp: Optional[int]
    eval_after_cp: Optional[int]
    best_uci: Optional[str]
    classification: MoveClassification
    is_book: bool
    is_critical: bool
    is_brilliant: bool
    comment: Optional[str] = None


@dataclass
class GameAnalysisResult:
    """Complete analysis of a game."""
    moves: List[MoveAnalysis]
    accuracy_white: float
    accuracy_black: float
    perf_elo_white: int
    perf_elo_black: int
    engine_version: str
    depth: int
    time_per_move: float


class GameAnalyzer:
    """Analyzes chess games move-by-move."""
    
    def __init__(self, engine: ChessEngine):
        """
        Initialize game analyzer.
        
        Args:
            engine: Chess engine instance
        """
        self.engine = engine
    
    def analyze_game(
        self,
        game: Game,
        depth: Optional[int] = None,
        time_per_move: Optional[float] = None,
        opening_book_plies: int = 12
    ) -> GameAnalysisResult:
        """
        Analyze a complete game.
        
        Args:
            game: Game to analyze
            depth: Analysis depth (None = use engine default)
            time_per_move: Time per move in seconds (None = use engine default)
            opening_book_plies: Number of plies to consider as book moves
            
        Returns:
            GameAnalysisResult with move-by-move analysis
        """
        # Parse PGN
        pgn = io.StringIO(game.pgn_text)
        chess_game = chess.pgn.read_game(pgn)
        
        if not chess_game:
            raise ValueError("Could not parse game PGN")
        
        # Analyze all moves
        moves_analysis = []
        board = chess_game.board()
        
        prev_eval: Optional[EngineEvaluation] = None
        
        for ply_index, move in enumerate(chess_game.mainline_moves()):
            # Record position before move
            fen_before = board.fen()
            
            # Evaluate position before move (if not already done)
            if prev_eval is None:
                eval_before = self.engine.evaluate(board, depth, time_per_move)
            else:
                eval_before = prev_eval
            
            # Make the move
            san = board.san(move)
            board.push(move)
            
            # Record position after move
            fen_after = board.fen()
            
            # Evaluate position after move
            eval_after = self.engine.evaluate(board, depth, time_per_move)
            
            # Classify the move
            is_book = ply_index < opening_book_plies
            
            classification = classify_move(
                move=move,
                eval_before=eval_before,
                eval_after=eval_after,
                is_book=is_book,
                board_before=chess.Board(fen_before)
            )
            
            # Create move analysis
            move_analysis = MoveAnalysis(
                ply_index=ply_index,
                san=san,
                uci=move.uci(),
                fen_before=fen_before,
                fen_after=fen_after,
                eval_before_cp=eval_before.score_cp,
                eval_best_cp=eval_before.score_cp,  # Best eval = current position
                eval_after_cp=eval_after.score_cp,
                best_uci=eval_before.best_move.uci() if eval_before.best_move else None,
                classification=classification,
                is_book=is_book,
                is_critical=classification == MoveClassification.CRITICAL,
                is_brilliant=classification == MoveClassification.BRILLIANT
            )
            
            moves_analysis.append(move_analysis)
            prev_eval = eval_after
        
        # Compute accuracy for each player
        white_moves = [m for m in moves_analysis if m.ply_index % 2 == 0]
        black_moves = [m for m in moves_analysis if m.ply_index % 2 == 1]
        
        accuracy_white = compute_accuracy(white_moves)
        accuracy_black = compute_accuracy(black_moves)
        
        # Estimate performance Elo (simplified)
        perf_elo_white = self._estimate_performance_elo(accuracy_white, white_moves)
        perf_elo_black = self._estimate_performance_elo(accuracy_black, black_moves)
        
        return GameAnalysisResult(
            moves=moves_analysis,
            accuracy_white=accuracy_white,
            accuracy_black=accuracy_black,
            perf_elo_white=perf_elo_white,
            perf_elo_black=perf_elo_black,
            engine_version="Stockfish (python-chess)",
            depth=depth or self.engine.config.depth or 20,
            time_per_move=time_per_move or self.engine.config.time_per_move or 0.5
        )
    
    def _estimate_performance_elo(
        self, 
        accuracy: float, 
        moves: List[MoveAnalysis]
    ) -> int:
        """
        Estimate performance Elo based on accuracy and move quality.
        
        This is a simplified heuristic.
        
        Args:
            accuracy: Accuracy percentage (0-100)
            moves: List of move analyses
            
        Returns:
            Estimated performance Elo rating
        """
        # Count move types
        blunders = sum(1 for m in moves if m.classification == MoveClassification.BLUNDER)
        mistakes = sum(1 for m in moves if m.classification == MoveClassification.MISTAKE)
        inaccuracies = sum(1 for m in moves if m.classification == MoveClassification.INACCURACY)
        
        # Base Elo on accuracy (simplified mapping)
        # 95%+ = 2200+, 90% = 2000, 85% = 1800, 80% = 1600, etc.
        base_elo = 800 + (accuracy / 100) * 1600
        
        # Penalize errors
        num_moves = len(moves)
        if num_moves > 0:
            error_rate = (blunders * 3 + mistakes * 2 + inaccuracies) / num_moves
            penalty = error_rate * 300
            base_elo -= penalty
        
        return max(500, min(3000, int(base_elo)))


def save_analysis_to_db(
    session,
    game: Game,
    analysis_result: GameAnalysisResult
) -> Analysis:
    """
    Save analysis results to database.
    
    Args:
        session: SQLAlchemy session
        game: Game being analyzed
        analysis_result: Analysis results
        
    Returns:
        Saved Analysis object
    """
    # Create Analysis record
    analysis = Analysis(
        game_id=game.id,
        engine_version=analysis_result.engine_version,
        depth=analysis_result.depth,
        time_per_move=analysis_result.time_per_move,
        accuracy_white=analysis_result.accuracy_white,
        accuracy_black=analysis_result.accuracy_black,
        perf_elo_white=analysis_result.perf_elo_white,
        perf_elo_black=analysis_result.perf_elo_black
    )
    
    session.add(analysis)
    
    # Create Move records
    for move_analysis in analysis_result.moves:
        move = Move(
            game_id=game.id,
            ply_index=move_analysis.ply_index,
            san=move_analysis.san,
            uci=move_analysis.uci,
            fen_before=move_analysis.fen_before,
            fen_after=move_analysis.fen_after,
            eval_before_cp=move_analysis.eval_before_cp,
            eval_best_cp=move_analysis.eval_best_cp,
            eval_after_cp=move_analysis.eval_after_cp,
            best_uci=move_analysis.best_uci,
            classification=move_analysis.classification.value,
            is_book=move_analysis.is_book,
            is_critical=move_analysis.is_critical,
            is_brilliant=move_analysis.is_brilliant,
            comment=move_analysis.comment
        )
        session.add(move)
    
    session.commit()
    return analysis
