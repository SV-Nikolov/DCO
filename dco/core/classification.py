"""
Move classification logic for DCO.
Classifies chess moves as book, best, excellent, good, inaccuracy, mistake, blunder, critical, or brilliant.
"""

from typing import Optional
import chess
from enum import Enum

from .engine import EngineEvaluation


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
CRITICAL_THRESHOLD = 120
CRITICAL_OTHER_MOVES_THRESHOLD = 150


def classify_move(
    move: chess.Move,
    eval_before: EngineEvaluation,
    eval_after: EngineEvaluation,
    is_book: bool,
    board_before: chess.Board
) -> MoveClassification:
    """
    Classify a chess move based on engine evaluation.
    
    Args:
        move: The move played
        eval_before: Engine evaluation before the move
        eval_after: Engine evaluation after the move
        is_book: Whether this is a book move
        board_before: Board position before the move
        
    Returns:
        Move classification
    """
    # Book moves
    if is_book:
        return MoveClassification.BOOK
    
    # Check if this is the best move
    if eval_before.best_move and move == eval_before.best_move:
        # Check for brilliant (strong sacrifice)
        if _is_brilliant_move(move, eval_before, eval_after, board_before):
            return MoveClassification.BRILLIANT
        return MoveClassification.BEST
    
    # Check for critical position (only one good move)
    if _is_critical_position(eval_before, board_before):
        return MoveClassification.CRITICAL
    
    # Calculate centipawn loss
    cp_loss = _calculate_cp_loss(eval_before, eval_after, board_before.turn)
    
    # Handle mate situations
    if eval_before.score_mate is not None or eval_after.score_mate is not None:
        return _classify_mate_situation(eval_before, eval_after, board_before.turn)
    
    # Classify based on centipawn loss
    if cp_loss is None:
        return MoveClassification.GOOD  # Default if we can't calculate
    
    if cp_loss <= EXCELLENT_THRESHOLD:
        # Check for brilliant among excellent moves
        if _is_brilliant_move(move, eval_before, eval_after, board_before):
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
    eval_before: EngineEvaluation,
    eval_after: EngineEvaluation,
    side_to_move: chess.Color
) -> Optional[int]:
    """
    Calculate centipawn loss from a move.
    
    Args:
        eval_before: Evaluation before the move
        eval_after: Evaluation after the move (from opponent's perspective)
        side_to_move: Color of the side that moved
        
    Returns:
        Centipawn loss (always positive), or None if cannot calculate
    """
    if eval_before.score_cp is None or eval_after.score_cp is None:
        return None
    
    # Both scores are from White's perspective
    # After the move, the position is from opponent's perspective but eval is still from White's
    score_before = eval_before.score_cp
    score_after = eval_after.score_cp
    
    # Calculate loss from moving player's perspective
    if side_to_move == chess.WHITE:
        # White's move: loss = before - after
        loss = score_before - score_after
    else:
        # Black's move: loss = after - before (since scores are from White's perspective)
        loss = score_after - score_before
    
    # Loss should be non-negative (we lost or stayed same)
    return max(0, loss)


def _is_critical_position(
    eval_before: EngineEvaluation,
    board: chess.Board
) -> bool:
    """
    Determine if position is critical (only one good move).
    
    A position is critical if:
    - The best move keeps evaluation acceptable
    - All other legal moves lose significantly more
    
    Args:
        eval_before: Engine evaluation with multiple PVs
        board: Board position
        
    Returns:
        True if position is critical
    """
    # Need at least 2 PV lines to compare
    if len(eval_before.pv_lines) < 2:
        return False
    
    # Get best move evaluation (already in eval_before.score_cp)
    best_score = eval_before.score_cp
    
    if best_score is None:
        return False
    
    # In a critical position, the best move should be acceptable
    # and other moves should be significantly worse
    # This is a simplified heuristic - ideally we'd re-evaluate each move
    
    # For now, we'll use a simple heuristic:
    # If position is sharp (eval magnitude > 200) and we have limited good moves
    # This is a placeholder for more sophisticated detection
    
    if abs(best_score) > 200:  # Sharp position
        return True
    
    return False


def _is_brilliant_move(
    move: chess.Move,
    eval_before: EngineEvaluation,
    eval_after: EngineEvaluation,
    board: chess.Board
) -> bool:
    """
    Detect brilliant moves (strong, non-obvious sacrifices).
    
    A move is brilliant if:
    - It's in top engine choices (best or excellent)
    - It sacrifices material without immediate equal recapture
    - The compensation is strong (evaluation remains good)
    - It's non-obvious (not a check, not forced)
    
    Args:
        move: The move played
        eval_before: Evaluation before move
        eval_after: Evaluation after move
        board: Board before move
        
    Returns:
        True if move is brilliant
    """
    # Check if move is in top choices
    if not eval_before.best_move or move != eval_before.best_move:
        # If not best move, check if excellent
        cp_loss = _calculate_cp_loss(eval_before, eval_after, board.turn)
        if cp_loss is None or cp_loss > EXCELLENT_THRESHOLD:
            return False
    
    # Check if it's a sacrifice
    board_copy = board.copy()
    board_copy.push(move)
    
    # Simple sacrifice detection: piece was moved to attacked square
    # and wasn't recaptured (or recapture is not equal)
    to_square = move.to_square
    moving_piece = board.piece_at(move.from_square)
    
    if not moving_piece:
        return False
    
    # Check if target square is attacked by opponent
    is_attacked = board_copy.is_attacked_by(not board.turn, to_square)
    
    if not is_attacked:
        return False
    
    # Check if it's a check (brilliant should be non-obvious)
    if board_copy.is_check():
        return False
    
    # Check if material was sacrificed (piece value >= pawn)
    piece_value = _get_piece_value(moving_piece.piece_type)
    if piece_value < 1:  # Less than a pawn
        return False
    
    # Check if evaluation remains strong (good compensation)
    if eval_after.score_cp is None:
        return False
    
    # From moving player's perspective, eval should still be decent
    score = eval_after.score_cp
    if board.turn == chess.BLACK:
        score = -score
    
    # Should maintain at least -50 cp (slight disadvantage OK for brilliant)
    if score < -50:
        return False
    
    return True


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
    eval_before: EngineEvaluation,
    eval_after: EngineEvaluation,
    side_to_move: chess.Color
) -> MoveClassification:
    """
    Classify moves in mate situations.
    
    Args:
        eval_before: Evaluation before move
        eval_after: Evaluation after move
        side_to_move: Color of side that moved
        
    Returns:
        Move classification
    """
    mate_before = eval_before.score_mate
    mate_after = eval_after.score_mate
    
    # If we had mate and lost it, that's a blunder
    if mate_before is not None:
        if side_to_move == chess.WHITE:
            # White had mate
            if mate_before > 0:
                # White could mate
                if mate_after is None or mate_after <= 0:
                    # Lost the mate
                    return MoveClassification.BLUNDER
        else:
            # Black had defense against mate
            if mate_before < 0:
                # Black could mate
                if mate_after is None or mate_after >= 0:
                    # Lost the mate
                    return MoveClassification.BLUNDER
    
    # If we allowed mate, that's a blunder
    if mate_after is not None:
        if side_to_move == chess.WHITE and mate_after < 0:
            # White allowed Black to mate
            return MoveClassification.BLUNDER
        elif side_to_move == chess.BLACK and mate_after > 0:
            # Black allowed White to mate
            return MoveClassification.BLUNDER
    
    # Otherwise, use centipawn-based classification
    return MoveClassification.GOOD
