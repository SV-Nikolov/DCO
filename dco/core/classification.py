"""
Move classification logic for DCO.
Classifies chess moves as book, best, excellent, good, inaccuracy, mistake, blunder, critical, or brilliant.
"""

from typing import Optional, TYPE_CHECKING
import chess
from enum import Enum

from .engine import EngineEvaluation

if TYPE_CHECKING:
    from .engine import ChessEngine


class MoveClassification(Enum):
    """Classification categories for moves."""
    BOOK = "book"
    BEST = "best"
    EXCELLENT = "excellent"
    GOOD = "good"
    INACCURACY = "inaccuracy"
    MISTAKE = "mistake"
    BLUNDER = "blunder"
    CRITICAL = "critical"
    BRILLIANT = "brilliant"


# Classification thresholds (in centipawns)
EXCELLENT_THRESHOLD = 15
GOOD_THRESHOLD = 50
INACCURACY_THRESHOLD = 100
MISTAKE_THRESHOLD = 200

# Brilliant move thresholds
BRILLIANT_MARGIN = 30  # User eval must be within this of best eval
BRILLIANT_MIN_SACRIFICE = 2  # Minimum material deficit to qualify as sacrifice

# Critical position thresholds  
UNIQUE_GAP = 120  # E1 - E2 gap for uniqueness
BREADTH_GAP = 150  # E1 - median(E2..E5) gap
WORST_GAP = 250  # E1 - E5 gap
DECIDED_SUPPRESS = 600  # Don't mark critical if position already decided

# PV horizon for sacrifice verification (plies to look ahead)
PV_HORIZON = 8


def classify_move(
    move: chess.Move,
    eval_before: EngineEvaluation,
    eval_best: EngineEvaluation,
    eval_user: EngineEvaluation,
    is_book: bool,
    board_before: chess.Board,
    engine: Optional['ChessEngine'] = None
) -> MoveClassification:
    """
    Classify a chess move based on engine evaluation.
    
    Compares the user's move against the best move from the SAME position.
    
    Args:
        move: The move played by user
        eval_before: Engine evaluation of position before any move
        eval_best: Engine evaluation after playing the best move
        eval_user: Engine evaluation after playing the user's move
        is_book: Whether this is a book move
        board_before: Board position before the move
        
    Returns:
        Move classification
    """
    # Book moves
    if is_book:
        return MoveClassification.BOOK
    
    # Check if this is the best move
    is_best_move = eval_before.best_move and move == eval_before.best_move
    
    if is_best_move:
        # Check for critical position flag
        if engine and _is_critical_position(eval_before, board_before, engine):
            return MoveClassification.CRITICAL
        
        # Check for brilliant (strong sacrifice)
        if engine and not is_book:
            if _is_brilliant_move(move, eval_before, eval_best, eval_user, board_before, engine):
                return MoveClassification.BRILLIANT
        
        return MoveClassification.BEST
    
    # Calculate centipawn loss
    cp_loss = _calculate_cp_loss(eval_best, eval_user, board_before.turn)
    
    # Handle mate situations
    mate_classification = _classify_mate_situation(eval_best, eval_user, board_before.turn)
    if mate_classification is not None:
        return mate_classification
    
    # Classify based on centipawn loss
    if cp_loss is None:
        return MoveClassification.GOOD  # Default if we can't calculate
    
    if cp_loss <= EXCELLENT_THRESHOLD:
        # Check for brilliant among excellent moves
        if engine and not is_book:
            if _is_brilliant_move(move, eval_before, eval_best, eval_user, board_before, engine):
                return MoveClassification.BRILLIANT
        return MoveClassification.EXCELLENT
    elif cp_loss <= GOOD_THRESHOLD:
        return MoveClassification.GOOD
    elif cp_loss <= INACCURACY_THRESHOLD:
        return MoveClassification.INACCURACY
    elif cp_loss <= MISTAKE_THRESHOLD:
        return MoveClassification.MISTAKE
    else:
        return MoveClassification.BLUNDER


def _calculate_cp_loss(
    eval_best: EngineEvaluation,
    eval_user: EngineEvaluation,
    side_to_move: chess.Color
) -> Optional[int]:
    """
    Calculate centipawn loss from user move compared to best move.
    
    CPL = max(0, eval_best - eval_user) from the perspective of the player who moved.
    
    Args:
        eval_best: Evaluation after best move
        eval_user: Evaluation after user's move
        side_to_move: Color of the side that moved
        
    Returns:
        Centipawn loss (always non-negative), or None if cannot calculate
    """
    if eval_best.score_cp is None or eval_user.score_cp is None:
        return None
    
    # Both evaluations are from White's perspective
    # Convert to moving player's perspective
    if side_to_move == chess.WHITE:
        # White's perspective: positive is good for white
        score_best = eval_best.score_cp
        score_user = eval_user.score_cp
    else:
        # Black's perspective: negate scores (negative is good for black)
        score_best = -eval_best.score_cp
        score_user = -eval_user.score_cp
    
    # CPL = how much worse the user move is compared to best
    loss = score_best - score_user
    
    # Loss should be non-negative
    return max(0, loss)


def _is_critical_position(
    eval_before: EngineEvaluation,
    board: chess.Board,
    engine: 'ChessEngine'
) -> bool:
    """
    Determine if position is critical (only one clearly best move).
    
    A position is critical if ALL are true:
    1. Best move is clearly unique (E1 - E2 >= UNIQUE_GAP)
    2. Breadth collapses (E1 - median(E2..E5) >= BREADTH_GAP)
    3. Worst alternative is much worse (E1 - E5 >= WORST_GAP)
    4. Position not already decided (abs(E1) < DECIDED_SUPPRESS, except mate)
    5. Not a book move (checked by caller)
    
    Uses MultiPV=5 to evaluate top 5 candidate moves.
    
    Args:
        eval_before: Engine evaluation with multiple PVs
        board: Board position
        engine: Chess engine for MultiPV=5 analysis
        
    Returns:
        True if position is critical
    """
    # Need MultiPV=5 analysis
    # Save current multipv setting
    original_multipv = engine.config.multipv
    
    try:
        # Set MultiPV to 5 for critical detection
        engine.config.multipv = 5
        
        # Re-evaluate position with MultiPV=5
        multi_eval = engine.evaluate(board, depth=eval_before.depth)
        
        # Restore original multipv
        engine.config.multipv = original_multipv
        
        # Need at least 2 moves to compare
        if len(multi_eval.pv_lines) < 2:
            return False
        
        # Extract evaluations for each candidate move
        # We need to evaluate each PV line to get its score
        evaluations = []
        
        for i, pv_line in enumerate(multi_eval.pv_lines[:5]):
            if not pv_line:
                continue
            
            # Play the first move of this PV
            test_board = board.copy()
            test_board.push(pv_line[0])
            
            # Get evaluation after this move
            pv_eval = engine.evaluate(test_board, depth=max(15, eval_before.depth - 2))
            
            if pv_eval.score_cp is not None:
                # Convert to side-to-move perspective
                if board.turn == chess.WHITE:
                    score = pv_eval.score_cp
                else:
                    score = -pv_eval.score_cp
                evaluations.append(score)
        
        # Need at least 2 evaluations to compare
        if len(evaluations) < 2:
            return False
        
        E1 = evaluations[0]  # Best move
        E2 = evaluations[1]  # Second best
        
        # Check 4: Suppress if already decided (unless mate-related)
        if abs(E1) >= DECIDED_SUPPRESS:
            # Allow critical only if it's mate-related
            if multi_eval.score_mate is None:
                return False
        
        # Check 1: Uniqueness gap (E1 - E2 >= UNIQUE_GAP)
        if E1 - E2 < UNIQUE_GAP:
            return False
        
        # Check 2: Breadth collapse (need at least 3 moves)
        if len(evaluations) >= 3:
            median_rest = _median(evaluations[1:5])  # E2 through E5
            if E1 - median_rest < BREADTH_GAP:
                return False
        
        # Check 3: Worst collapse (need at least 5 moves)
        if len(evaluations) >= 5:
            E5 = evaluations[4]
            if E1 - E5 < WORST_GAP:
                return False
        
        return True
        
    except:
        # If MultiPV analysis fails, not critical
        engine.config.multipv = original_multipv
        return False


def _median(values: list) -> float:
    """Calculate median of a list of numbers."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n % 2 == 0:
        return (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
    else:
        return sorted_vals[n//2]


def _is_brilliant_move(
    move: chess.Move,
    eval_before: EngineEvaluation,
    eval_best: EngineEvaluation,
    eval_user: EngineEvaluation,
    board: chess.Board,
    engine: 'ChessEngine'
) -> bool:
    """
    Detect brilliant moves (strong, non-obvious sacrifices with lasting compensation).
    
    A move is brilliant if ALL conditions are met:
    1. Move is BEST or EXCELLENT (CPL <= 15)
    2. Not a book move (checked by caller)
    3. Not a recapture and not the only legal move
    4. Sacrifices material that persists after engine PV horizon (trade-proof)
    5. Evaluation remains strong after deeper verification (within BRILLIANT_MARGIN)
    6. Non-obvious (not a checking move)
    
    Args:
        move: The move played
        eval_before: Evaluation before any move
        eval_best: Evaluation after best move
        eval_user: Evaluation after user's move
        board: Board before move
        engine: Chess engine for deeper verification
        
    Returns:
        True if move is brilliant
    """
    # A) Candidate check: Must be Best or Excellent
    is_best = eval_before.best_move and move == eval_before.best_move
    if not is_best:
        cp_loss = _calculate_cp_loss(eval_best, eval_user, board.turn)
        if cp_loss is None or cp_loss > EXCELLENT_THRESHOLD:
            return False
    
    # A) Not a recapture
    if _is_recapture(move, board):
        return False
    
    # A) Not the only legal move
    if board.legal_moves.count() <= 1:
        return False
    
    # A) Not a checking move (obvious)
    board_copy = board.copy()
    board_copy.push(move)
    if board_copy.is_check():
        return False
    
    # B) Trade-proof sacrifice detection
    material_before = _calculate_material(board, board.turn)
    
    # Apply user move
    board_after = board.copy()
    board_after.push(move)
    material_immediate = _calculate_material(board_after, board.turn)
    
    # If no material lost immediately, not a sacrifice
    if material_immediate >= material_before:
        return False
    
    # Check if material deficit persists after PV horizon
    # Play out engine's PV continuation for PV_HORIZON plies
    pv_board = board_after.copy()
    pv_moves_played = 0
    
    if eval_user.pv_lines and len(eval_user.pv_lines) > 0:
        pv = eval_user.pv_lines[0]
        for pv_move in pv[:PV_HORIZON]:
            if pv_board.is_game_over():
                break
            try:
                pv_board.push(pv_move)
                pv_moves_played += 1
            except:
                break
    
    # Calculate material after horizon (only if we got some moves)
    if pv_moves_played >= 4:  # Need at least 4 plies (2 full moves) of continuation
        material_horizon = _calculate_material(pv_board, board.turn)
        
        # If material returns to within 1 point, it's a trade, not sacrifice
        if material_horizon >= material_before - 1:
            return False
        
        # Must remain down at least BRILLIANT_MIN_SACRIFICE
        if material_before - material_horizon < BRILLIANT_MIN_SACRIFICE:
            return False
    else:
        # If we can't verify with PV, require immediate material loss to be significant
        if material_before - material_immediate < BRILLIANT_MIN_SACRIFICE:
            return False
    
    # C) Deeper confirmation: re-evaluate with higher depth
    try:
        deeper_eval = engine.evaluate(board_after, depth=(eval_user.depth + 5))
        
        if deeper_eval.score_cp is not None and eval_best.score_cp is not None:
            # Convert to moving player's perspective
            if board.turn == chess.WHITE:
                score_best = eval_best.score_cp
                score_deeper = deeper_eval.score_cp
            else:
                score_best = -eval_best.score_cp
                score_deeper = -deeper_eval.score_cp
            
            # Deeper eval must remain within BRILLIANT_MARGIN of best
            if score_deeper < score_best - BRILLIANT_MARGIN:
                return False
    except:
        # If deeper eval fails, reject brilliant
        return False
    
    return True


def _is_recapture(move: chess.Move, board: chess.Board) -> bool:
    """
    Check if move is a recapture.
    
    Args:
        move: Move to check
        board: Board before move
        
    Returns:
        True if move recaptures on the square of the last capture
    """
    # Check if there was a previous move
    if len(board.move_stack) == 0:
        return False
    
    # Get last move
    last_move = board.peek()
    
    # Check if last move was a capture
    board_before_last = board.copy()
    board_before_last.pop()
    was_capture = board_before_last.piece_at(last_move.to_square) is not None
    
    if not was_capture:
        return False
    
    # Check if current move recaptures on same square
    return move.to_square == last_move.to_square and board.piece_at(move.to_square) is not None


def _calculate_material(board: chess.Board, side: chess.Color) -> int:
    """
    Calculate total material for a side.
    
    Args:
        board: Chess board
        side: Color to calculate material for
        
    Returns:
        Total material value
    """
    material = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == side:
            material += _get_piece_value(piece.piece_type)
    return material


def _get_piece_value(piece_type: chess.PieceType) -> int:
    """Get approximate piece value."""
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    return values.get(piece_type, 0)


def _classify_mate_situation(
    eval_best: EngineEvaluation,
    eval_user: EngineEvaluation,
    side_to_move: chess.Color
) -> Optional[MoveClassification]:
    """
    Classify moves in mate situations.
    
    Mate handling:
    - Missing mate-in-X: CRITICAL (could have forced mate, didn't)
    - Allowing mate-in-X: BLUNDER (opponent now has forced mate)
    - Finding mate: BEST (executed forced mate)
    
    Args:
        eval_best: Evaluation after best move
        eval_user: Evaluation after user's move
        side_to_move: Color that made the move
        
    Returns:
        Classification if in mate situation, None otherwise
    """
    # Best move leads to mate (we had forced mate available)
    if eval_best.score_mate is not None and eval_best.score_mate > 0:
        # From moving player's perspective
        if side_to_move == chess.WHITE:
            mate_for_us = eval_best.score_mate > 0
        else:
            mate_for_us = eval_best.score_mate < 0
        
        if mate_for_us:
            # We could have forced mate
            # Check if user move also leads to mate
            if eval_user.score_mate is not None:
                if side_to_move == chess.WHITE:
                    user_mate = eval_user.score_mate > 0
                else:
                    user_mate = eval_user.score_mate < 0
                
                if user_mate:
                    # User found mate too (may be different line)
                    return MoveClassification.BEST
                else:
                    # User move allowed opponent mate
                    return MoveClassification.CRITICAL
            else:
                # User move doesn't lead to mate, missed the forced mate
                return MoveClassification.CRITICAL
    
    # User move allows mate for opponent
    if eval_user.score_mate is not None:
        if side_to_move == chess.WHITE:
            opponent_has_mate = eval_user.score_mate < 0
        else:
            opponent_has_mate = eval_user.score_mate > 0
        
        if opponent_has_mate:
            # We gave opponent forced mate
            return MoveClassification.BLUNDER
    
    return None
