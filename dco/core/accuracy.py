"""
Accuracy computation for DCO.
Calculates move accuracy based on centipawn loss.
"""

from typing import List, Optional
import math

from .classification import MoveClassification


def compute_accuracy(moves: List) -> float:
    """
    Compute accuracy percentage for a list of moves.
    
    Uses a logarithmic decay function to map centipawn loss to accuracy.
    
    Args:
        moves: List of MoveAnalysis objects
        
    Returns:
        Accuracy percentage (0-100)
    """
    if not moves:
        return 0.0
    
    # Filter out book moves (they don't count toward accuracy)
    non_book_moves = [m for m in moves if not m.is_book]
    
    if not non_book_moves:
        return 100.0  # All moves were book moves
    
    total_score = 0.0
    
    for move in non_book_moves:
        # Calculate centipawn loss
        cp_loss = _get_cp_loss(move)
        
        # Map to 0-100 score using decay function
        move_score = _cp_loss_to_score(cp_loss)
        total_score += move_score
    
    # Average across all non-book moves
    accuracy = total_score / len(non_book_moves)
    
    return round(accuracy, 2)


def _get_cp_loss(move) -> int:
    """
    Get centipawn loss for a move.
    
    Args:
        move: MoveAnalysis object
        
    Returns:
        Centipawn loss (always non-negative)
    """
    # Handle None values
    if move.eval_before_cp is None or move.eval_after_cp is None:
        return 0
    
    # Determine which player made the move (even ply = White, odd ply = Black)
    is_white = (move.ply_index % 2 == 0)
    
    # Both evals are from White's perspective
    eval_before = move.eval_before_cp
    eval_after = move.eval_after_cp
    
    # Calculate loss from moving player's perspective
    if is_white:
        loss = eval_before - eval_after
    else:
        loss = eval_after - eval_before
    
    return max(0, loss)


def _cp_loss_to_score(cp_loss: int) -> float:
    """
    Map centipawn loss to a score from 0-100.
    
    Uses a logarithmic decay function:
    - 0 cp loss = 100 score
    - 50 cp loss = ~90 score
    - 100 cp loss = ~80 score
    - 200 cp loss = ~65 score
    - 500 cp loss = ~40 score
    - 1000+ cp loss = ~20 score
    
    Args:
        cp_loss: Centipawn loss (non-negative)
        
    Returns:
        Score from 0-100
    """
    if cp_loss <= 0:
        return 100.0
    
    # Use logarithmic decay: score = 100 - k * log(1 + cp_loss)
    # Tuned so that 100 cp loss ≈ 80 score
    k = 28.85  # Tuning constant
    
    score = 100.0 - k * math.log10(1 + cp_loss)
    
    # Clamp to [0, 100]
    return max(0.0, min(100.0, score))


def compute_average_cp_loss(moves: List) -> float:
    """
    Compute average centipawn loss across moves.
    
    Args:
        moves: List of MoveAnalysis objects
        
    Returns:
        Average centipawn loss
    """
    if not moves:
        return 0.0
    
    non_book_moves = [m for m in moves if not m.is_book]
    
    if not non_book_moves:
        return 0.0
    
    total_loss = sum(_get_cp_loss(m) for m in non_book_moves)
    return total_loss / len(non_book_moves)


def count_move_types(moves: List) -> dict:
    """
    Count moves by classification type.
    
    Args:
        moves: List of MoveAnalysis objects
        
    Returns:
        Dictionary mapping classification to count
    """
    counts = {
        MoveClassification.BOOK: 0,
        MoveClassification.BEST: 0,
        MoveClassification.EXCELLENT: 0,
        MoveClassification.GOOD: 0,
        MoveClassification.INACCURACY: 0,
        MoveClassification.MISTAKE: 0,
        MoveClassification.BLUNDER: 0,
        MoveClassification.CRITICAL: 0,
        MoveClassification.BRILLIANT: 0,
    }
    
    for move in moves:
        classification = move.classification
        if classification in counts:
            counts[classification] += 1
    
    return counts
