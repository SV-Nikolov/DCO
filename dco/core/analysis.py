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
from ..data.models import Game, Analysis, Move, GameAnalytics, GameSource


# Default phase boundaries (ply is 1-based for readability)
OPENING_END_PLY = 12
MIDDLEGAME_END_PLY = 60


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
        player_color = "white" if move_analysis.ply_index % 2 == 0 else "black"
        cpl = _compute_cpl(player_color, move_analysis.eval_best_cp, move_analysis.eval_after_cp)
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
            cpl=cpl,
            player_color=player_color,
            best_uci=move_analysis.best_uci,
            classification=move_analysis.classification.name,
            is_book=move_analysis.is_book,
            is_critical=move_analysis.is_critical,
            is_brilliant=move_analysis.is_brilliant,
            comment=move_analysis.comment
        )
        session.add(move)

    # Replace existing analytics for this game
    session.query(GameAnalytics).filter(GameAnalytics.game_id == game.id).delete()
    analytics_row = _compute_game_analytics(game, analysis_result)
    session.add(analytics_row)
    
    session.commit()
    return analysis


def _compute_cpl(player_color: str, eval_best_cp: Optional[int], eval_after_cp: Optional[int]) -> Optional[int]:
    """Compute CPL from the player's perspective."""
    if eval_best_cp is None or eval_after_cp is None:
        return None

    if player_color == "white":
        diff = eval_best_cp - eval_after_cp
    else:
        diff = eval_after_cp - eval_best_cp

    return max(0, diff)


def _phase_from_ply(ply_index: int) -> str:
    """Return phase name for a 0-based ply index."""
    ply = ply_index + 1
    if ply <= OPENING_END_PLY:
        return "opening"
    if ply <= MIDDLEGAME_END_PLY:
        return "middlegame"
    return "endgame"


def _compute_game_analytics(game: Game, analysis_result: GameAnalysisResult) -> GameAnalytics:
    """Compute per-game analytics for caching."""
    phase_stats = {
        "opening": {"blunders": 0, "mistakes": 0, "inaccuracies": 0, "total_moves": 0, "cpl_sum": 0, "cpl_count": 0},
        "middlegame": {"blunders": 0, "mistakes": 0, "inaccuracies": 0, "total_moves": 0, "cpl_sum": 0, "cpl_count": 0},
        "endgame": {"blunders": 0, "mistakes": 0, "inaccuracies": 0, "total_moves": 0, "cpl_sum": 0, "cpl_count": 0},
    }

    cpl_buckets = {"0_20": 0, "20_50": 0, "50_100": 0, "100_200": 0, "200_plus": 0, "total": 0}

    overall_cpl_sum = 0
    overall_cpl_count = 0

    color_stats = {
        "white": {"cpl_sum": 0, "cpl_count": 0, "blunders": 0, "mistakes": 0, "inaccuracies": 0},
        "black": {"cpl_sum": 0, "cpl_count": 0, "blunders": 0, "mistakes": 0, "inaccuracies": 0},
    }

    critical_faced = 0
    critical_solved = 0
    critical_failed = 0
    critical_cpl_sum = 0
    critical_cpl_count = 0

    for move in analysis_result.moves:
        player_color = "white" if move.ply_index % 2 == 0 else "black"
        phase = _phase_from_ply(move.ply_index)
        classification = move.classification.name.upper()

        cpl = _compute_cpl(player_color, move.eval_best_cp, move.eval_after_cp)

        # Skip book moves for ACPL and CPL distribution
        if not move.is_book and cpl is not None:
            overall_cpl_sum += cpl
            overall_cpl_count += 1

            color_stats[player_color]["cpl_sum"] += cpl
            color_stats[player_color]["cpl_count"] += 1

            phase_stats[phase]["cpl_sum"] += cpl
            phase_stats[phase]["cpl_count"] += 1

            cpl_buckets["total"] += 1
            if cpl <= 20:
                cpl_buckets["0_20"] += 1
            elif cpl <= 50:
                cpl_buckets["20_50"] += 1
            elif cpl <= 100:
                cpl_buckets["50_100"] += 1
            elif cpl <= 200:
                cpl_buckets["100_200"] += 1
            else:
                cpl_buckets["200_plus"] += 1

        # Error counts by phase and color
        phase_stats[phase]["total_moves"] += 1
        if classification == "BLUNDER":
            phase_stats[phase]["blunders"] += 1
            color_stats[player_color]["blunders"] += 1
        elif classification == "MISTAKE":
            phase_stats[phase]["mistakes"] += 1
            color_stats[player_color]["mistakes"] += 1
        elif classification == "INACCURACY":
            phase_stats[phase]["inaccuracies"] += 1
            color_stats[player_color]["inaccuracies"] += 1

        # Critical positions
        if move.is_critical:
            critical_faced += 1
            if cpl is not None:
                critical_cpl_sum += cpl
                critical_cpl_count += 1
                if cpl == 0:
                    critical_solved += 1
                else:
                    critical_failed += 1

    def _avg(sum_val: int, count_val: int) -> Optional[float]:
        return (sum_val / count_val) if count_val else None

    analytics = GameAnalytics(
        game_id=game.id,
        acpl_overall=_avg(overall_cpl_sum, overall_cpl_count),
        acpl_opening=_avg(phase_stats["opening"]["cpl_sum"], phase_stats["opening"]["cpl_count"]),
        acpl_middlegame=_avg(phase_stats["middlegame"]["cpl_sum"], phase_stats["middlegame"]["cpl_count"]),
        acpl_endgame=_avg(phase_stats["endgame"]["cpl_sum"], phase_stats["endgame"]["cpl_count"]),
        phase_error_counts=phase_stats,
        cpl_distribution=cpl_buckets,
        critical_faced=critical_faced,
        critical_solved=critical_solved,
        critical_failed=critical_failed,
        critical_success_rate=_avg(critical_solved, critical_faced),
        acpl_critical=_avg(critical_cpl_sum, critical_cpl_count),
        acpl_white=_avg(color_stats["white"]["cpl_sum"], color_stats["white"]["cpl_count"]),
        acpl_black=_avg(color_stats["black"]["cpl_sum"], color_stats["black"]["cpl_count"]),
        blunders_white=color_stats["white"]["blunders"],
        blunders_black=color_stats["black"]["blunders"],
        mistakes_white=color_stats["white"]["mistakes"],
        mistakes_black=color_stats["black"]["mistakes"],
        inaccuracies_white=color_stats["white"]["inaccuracies"],
        inaccuracies_black=color_stats["black"]["inaccuracies"],
    )

    return analytics
