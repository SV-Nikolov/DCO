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
from .eco import get_eco_detector
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
    eco_code: Optional[str] = None
    opening_name: Optional[str] = None
    opening_variation: Optional[str] = None
    eco_code: Optional[str] = None
    opening_name: Optional[str] = None
    opening_variation: Optional[str] = None


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
        
        # Detect opening using ECO
        eco_detector = get_eco_detector()
        
        prev_eval: Optional[EngineEvaluation] = None
        
        for ply_index, move in enumerate(chess_game.mainline_moves()):
            # Record position before move
            fen_before = board.fen()
            
            # Evaluate position before move (if not already done)
            if prev_eval is None:
                eval_before = self.engine.evaluate(board, depth, time_per_move)
            else:
                eval_before = prev_eval
            
            # Get evaluation after best move (from same position)
            board_copy = board.copy()
            if eval_before.best_move:
                board_copy.push(eval_before.best_move)
                eval_best = self.engine.evaluate(board_copy, depth, time_per_move)
            else:
                eval_best = eval_before
            
            # Make the user's move
            san = board.san(move)
            board.push(move)
            
            # Record position after move
            fen_after = board.fen()
            
            # Evaluate position after user's move
            eval_user = self.engine.evaluate(board, depth, time_per_move)
            
            # Classify the move
            is_book = ply_index < opening_book_plies
            
            classification = classify_move(
                move=move,
                eval_before=eval_before,
                eval_best=eval_best,
                eval_user=eval_user,
                is_book=is_book,
                board_before=chess.Board(fen_before),
                engine=self.engine
            )
            
            # Create move analysis
            move_analysis = MoveAnalysis(
                ply_index=ply_index,
                san=san,
                uci=move.uci(),
                fen_before=fen_before,
                fen_after=fen_after,
                eval_before_cp=eval_before.score_cp,
                eval_best_cp=eval_best.score_cp,  # Eval after best move
                eval_after_cp=eval_user.score_cp,  # Eval after user move
                best_uci=eval_before.best_move.uci() if eval_before.best_move else None,
                classification=classification,
                is_book=is_book,
                is_critical=classification == MoveClassification.CRITICAL,
                is_brilliant=classification == MoveClassification.BRILLIANT
            )
            
            moves_analysis.append(move_analysis)
            prev_eval = eval_user
        
        # Compute accuracy for each player
        white_moves = [m for m in moves_analysis if m.ply_index % 2 == 0]
        black_moves = [m for m in moves_analysis if m.ply_index % 2 == 1]
        
        accuracy_white = compute_accuracy(white_moves)
        accuracy_black = compute_accuracy(black_moves)
        
        # Estimate performance Elo with opponent Elo for capping
        perf_elo_white = self._estimate_performance_elo(
            accuracy_white, 
            white_moves, 
            opponent_elo=game.black_elo
        )
        perf_elo_black = self._estimate_performance_elo(
            accuracy_black, 
            black_moves, 
            opponent_elo=game.white_elo
        )
        
        # Detect opening
        eco_code, opening_name, opening_variation = eco_detector.detect_opening(board)
        
        return GameAnalysisResult(
            moves=moves_analysis,
            accuracy_white=accuracy_white,
            accuracy_black=accuracy_black,
            perf_elo_white=perf_elo_white,
            perf_elo_black=perf_elo_black,
            engine_version="Stockfish (python-chess)",
            depth=depth or self.engine.config.depth or 20,
            time_per_move=time_per_move or self.engine.config.time_per_move or 0.5,
            eco_code=eco_code,
            opening_name=opening_name,
            opening_variation=opening_variation
        )
    
    def _estimate_performance_elo(
        self, 
        accuracy: float, 
        moves: List['MoveAnalysis'],
        opponent_elo: Optional[int] = None
    ) -> int:
        """
        Estimate performance Elo based on ACPL (Average Centipawn Loss) and error rates.
        
        Uses a stable, ACPL-based formula with normalization and bounds checking.
        
        Args:
            accuracy: Accuracy percentage (0-100) - for legacy compatibility
            moves: List of move analyses
            opponent_elo: Opponent's Elo rating (for capping)
            
        Returns:
            Estimated performance Elo rating (500-3000)
        """
        # A) Minimum game size gate
        MIN_PLIES = 20
        if len(moves) < MIN_PLIES:
            return 1500  # Default uncertain rating
        
        # B) Compute ACPL (Average Centipawn Loss)
        acpl = self._compute_acpl(moves)
        
        if acpl is None:
            return 1500  # Cannot compute without cp loss data
        
        # C) Normalize error rates by 40 moves
        blunders = sum(1 for m in moves if m.classification == MoveClassification.BLUNDER)
        mistakes = sum(1 for m in moves if m.classification == MoveClassification.MISTAKE)
        inaccuracies = sum(1 for m in moves if m.classification == MoveClassification.INACCURACY)
        
        # Normalize to per-40-moves rate
        num_moves = len(moves)
        blunders_per_40 = (blunders / num_moves) * 40 if num_moves > 0 else 0
        mistakes_per_40 = (mistakes / num_moves) * 40 if num_moves > 0 else 0
        
        # D) ACPL-based curve
        # Lower ACPL = higher Elo
        # Mapping based on typical ACPL ranges:
        # ACPL 10 = ~2600, ACPL 20 = ~2300, ACPL 30 = ~2000
        # ACPL 50 = ~1700, ACPL 100 = ~1200, ACPL 200 = ~800
        if acpl <= 10:
            base_elo = 2600 - (acpl * 30)  # Very strong
        elif acpl <= 30:
            base_elo = 2300 - ((acpl - 10) * 15)  # Strong
        elif acpl <= 50:
            base_elo = 2000 - ((acpl - 30) * 15)  # Intermediate
        elif acpl <= 100:
            base_elo = 1700 - ((acpl - 50) * 10)  # Below average
        else:
            base_elo = 1200 - ((acpl - 100) * 4)  # Beginner
        
        # E) Subtract penalties for blunders/mistakes
        penalty = (blunders_per_40 * 150) + (mistakes_per_40 * 50)
        estimated_elo = base_elo - penalty
        
        # F) Apply bounds
        estimated_elo = max(500, min(3000, estimated_elo))
        
        # G) Cap relative to opponent (if provided)
        if opponent_elo is not None:
            MAX_DIFF = 400
            estimated_elo = min(estimated_elo, opponent_elo + MAX_DIFF)
        
        return int(estimated_elo)
    
    def _compute_acpl(self, moves: List['MoveAnalysis']) -> Optional[float]:
        """
        Compute Average Centipawn Loss for a list of moves.
        
        Excludes book moves and forced moves (optional).
        
        Args:
            moves: List of move analyses
            
        Returns:
            Average centipawn loss, or None if cannot compute
        """
        cp_losses = []
        
        for move in moves:
            # Skip book moves
            if move.is_book:
                continue
            
            # Skip if we don't have evaluation data
            if move.eval_best_cp is None or move.eval_after_cp is None:
                continue
            
            # Calculate CPL for this move
            # CPL is already stored as the difference, but let's recalculate for accuracy
            # Since eval_best_cp and eval_after_cp are from different positions,
            # we need to calculate the loss from the player's perspective
            
            # eval_best_cp: evaluation after best move (from White's POV)
            # eval_after_cp: evaluation after user's move (from White's POV)
            # We need to convert to moving player's POV
            
            is_white_move = (move.ply_index % 2 == 0)
            
            if is_white_move:
                # White's move: higher is better
                cp_loss = max(0, move.eval_best_cp - move.eval_after_cp)
            else:
                # Black's move: lower is better
                cp_loss = max(0, move.eval_after_cp - move.eval_best_cp)
            
            cp_losses.append(cp_loss)
        
        if not cp_losses:
            return None
        
        return sum(cp_losses) / len(cp_losses)


def save_analysis_to_db(
    session,
    game: Game,
    analysis_result: GameAnalysisResult
) -> Analysis:
    """
    Save analysis results to database. Deletes any existing analysis for this game first.
    
    Args:
        session: SQLAlchemy session
        game: Game being analyzed
        analysis_result: Analysis results
        
    Returns:
        Saved Analysis object
    """
    # Delete old analysis if it exists (for reanalysis)
    old_analysis = session.query(Analysis).filter(Analysis.game_id == game.id).first()
    if old_analysis:
        # Delete associated moves first
        session.query(Move).filter(Move.game_id == game.id).delete(synchronize_session='fetch')
        # Delete the analysis record
        session.query(Analysis).filter(Analysis.game_id == game.id).delete(synchronize_session='fetch')
        # Flush to ensure deletion happens immediately
        session.flush()
    
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
    
    # Update game with ECO information
    if analysis_result.eco_code:
        game.eco_code = analysis_result.eco_code
        game.opening_name = analysis_result.opening_name
        game.opening_variation = analysis_result.opening_variation
    
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
            classification=move_analysis.classification.name,
            is_book=move_analysis.is_book,
            is_critical=move_analysis.is_critical,
            is_brilliant=move_analysis.is_brilliant,
            comment=move_analysis.comment
        )
        session.add(move)
    
    session.commit()
    return analysis
