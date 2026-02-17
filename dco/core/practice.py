"""
Practice mode helpers for DCO.
Generates practice items and updates spaced repetition progress.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import random

import chess

from .engine import ChessEngine
from .analysis import GameAnalysisResult
from ..data.models import (
    Game,
    PracticeItem,
    PracticeProgress,
    PracticeCategory,
    PracticeResult,
)


DEFAULT_OFFSET_PLIES = 2
DEFAULT_TARGET_LINE_PLIES = 1

logger = logging.getLogger(__name__)


def generate_practice_items(
    session,
    game: Game,
    analysis_result: GameAnalysisResult,
    engine: ChessEngine,
    categories: Optional[List[PracticeCategory]] = None,
    offset_plies: int = DEFAULT_OFFSET_PLIES,
    target_line_plies: int = DEFAULT_TARGET_LINE_PLIES
) -> int:
    """
    Generate practice items from analysis results. Deletes old practice items for this game first.

    Args:
        session: SQLAlchemy session
        game: Game being analyzed
        analysis_result: Analysis results with per-move data
        engine: Chess engine for PV line generation
        categories: Optional list of PracticeCategory to include
        offset_plies: Number of plies before mistake to start practice
        target_line_plies: Number of plies in target solution line

    Returns:
        Number of practice items created
    """
    if categories is None:
        categories = [
            PracticeCategory.BLUNDER,
            PracticeCategory.MISTAKE,
            PracticeCategory.CRITICAL,
        ]

    # Delete old practice items and their progress records for this game (for reanalysis)
    # Delete progress records first, then items
    session.query(PracticeProgress).filter(
        PracticeProgress.practice_item_id.in_(
            session.query(PracticeItem.id).filter(
                PracticeItem.source_game_id == game.id
            )
        )
    ).delete(synchronize_session='fetch')
    
    session.query(PracticeItem).filter(
        PracticeItem.source_game_id == game.id
    ).delete(synchronize_session='fetch')
    
    # Flush to ensure deletion happens immediately
    session.flush()

    created = 0

    for move in analysis_result.moves:
        category = _map_move_to_category(move.classification.name)
        if category is None or category not in categories:
            continue

        # Skip book moves and brilliant moves (not for practice)
        if move.is_book or move.is_brilliant:
            continue

        # Compute starting ply
        start_ply = max(0, move.ply_index - offset_plies)
        start_move = analysis_result.moves[start_ply]

        fen_start = start_move.fen_before
        board = chess.Board(fen_start)
        side_to_move = "white" if board.turn == chess.WHITE else "black"

        # Build target line from engine PV
        target_uci, target_san = _build_target_line(
            board,
            engine,
            target_line_plies
        )
        if not target_uci:
            continue

        practice_item = PracticeItem(
            source_game_id=game.id,
            source_ply_index=move.ply_index,
            fen_start=fen_start,
            side_to_move=side_to_move,
            target_line_uci=target_uci,
            target_line_san=target_san,
            category=category,
            motif_tags=None
        )
        session.add(practice_item)
        session.flush()

        # Create progress record
        progress = PracticeProgress(
            practice_item_id=practice_item.id,
            due_date=datetime.utcnow(),
            interval_days=1.0,
            ease_factor=2.5,
            repetitions=0,
            lapses=0,
            last_result=None,
            attempts_total=0,
            attempts_first_try_correct=0
        )
        session.add(progress)

        created += 1

    return created


def select_practice_items(
    session,
    categories: List[PracticeCategory],
    limit: int,
    due_only: bool = True
) -> List[PracticeItem]:
    """
    Select practice items for a session.

    Args:
        session: SQLAlchemy session
        categories: Categories to include
        limit: Maximum number of items
        due_only: If True, prefer due items first

    Returns:
        List of PracticeItem objects
    """
    query = session.query(PracticeItem).filter(
        PracticeItem.category.in_(categories)
    ).join(PracticeProgress)

    # Exclude mastered items (3 consecutive first-try passes)
    query = query.filter(PracticeProgress.consecutive_first_try < 3)

    if due_only:
        now = datetime.utcnow()
        query = query.filter(PracticeProgress.due_date <= now)

    items = query.all()
    if not items:
        # Fallback: any items if no due items
        items = session.query(PracticeItem).join(PracticeProgress).filter(
            PracticeItem.category.in_(categories),
            PracticeProgress.consecutive_first_try < 3
        ).all()

    # Ensure attributes are loaded before detaching
    for item in items:
        _ = item.fen_start
        _ = item.target_line_uci
        _ = item.target_line_san
        _ = item.category
        session.expunge(item)

    random.shuffle(items)
    return items[:limit]


def update_practice_progress(
    progress: PracticeProgress,
    result: PracticeResult,
    first_try: bool
) -> None:
    """
    Update spaced repetition progress using a simple SM-2 style algorithm.

    Args:
        progress: PracticeProgress record
        result: PracticeResult for the attempt
        first_try: Whether correct on the first try
    """
    progress.attempts_total += 1
    if first_try and result != PracticeResult.FAIL:
        progress.attempts_first_try_correct += 1

    # Assign a quality score
    if result == PracticeResult.PASS_FIRST_TRY:
        quality = 5
    elif result == PracticeResult.PASS:
        quality = 3
    else:
        quality = 1

    if quality < 3:
        progress.repetitions = 0
        progress.interval_days = 1.0
        progress.ease_factor = max(1.3, progress.ease_factor - 0.2)
        progress.lapses += 1
        progress.consecutive_first_try = 0
    else:
        progress.repetitions += 1
        if progress.repetitions == 1:
            progress.interval_days = 1.0
        elif progress.repetitions == 2:
            progress.interval_days = 6.0
        else:
            progress.interval_days *= progress.ease_factor
        progress.ease_factor = max(1.3, progress.ease_factor + 0.1)

        if result == PracticeResult.PASS_FIRST_TRY:
            progress.consecutive_first_try += 1
        else:
            progress.consecutive_first_try = 0

    progress.last_result = result
    progress.due_date = datetime.utcnow() + timedelta(days=progress.interval_days)


def _map_move_to_category(classification: str) -> Optional[PracticeCategory]:
    """Map move classification string to PracticeCategory."""
    mapping = {
        "BLUNDER": PracticeCategory.BLUNDER,
        "MISTAKE": PracticeCategory.MISTAKE,
        "INACCURACY": PracticeCategory.INACCURACY,
        "CRITICAL": PracticeCategory.CRITICAL
    }
    return mapping.get(classification)


def _build_target_line(
    board: chess.Board,
    engine: ChessEngine,
    max_plies: int
) -> Tuple[List[str], List[str]]:
    """
    Build a target line from the engine PV.

    Args:
        board: Starting board position
        engine: Chess engine
        max_plies: Max number of plies to include

    Returns:
        Tuple of (uci_moves, san_moves)
    """
    eval_info = engine.evaluate(board)
    if not eval_info.pv_lines:
        return [], []

    pv = eval_info.pv_lines[0]
    if not pv:
        return [], []

    uci_moves = []
    san_moves = []
    temp_board = board.copy()

    for move in pv[:max_plies]:
        try:
            san_moves.append(temp_board.san(move))
            uci_moves.append(move.uci())
            temp_board.push(move)
        except (chess.IllegalMoveError, ValueError) as e:
            logger.debug(f"Stopping PV parsing due to illegal move: {e}")
            break

    return uci_moves, san_moves
