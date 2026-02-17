"""
Puzzle manager for DCO.
Handles puzzle operations, rating calculations, and progress tracking.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
import chess

from ..data.models import Puzzle, PuzzleProgress, PuzzleAttempt, PuzzleTheme, PracticeResult
from ..data.db import Database


class PuzzleManager:
    """Manages puzzle operations and progress tracking."""

    def __init__(self, db: Database):
        self.db = db

    def create_puzzle(
        self,
        fen: str,
        solution_moves: List[str],
        theme: PuzzleTheme,
        rating: int,
        source: str = "manual",
        theme_tags: Optional[List[str]] = None,
        source_game_id: Optional[int] = None,
    ) -> Puzzle:
        """Create a new puzzle."""
        session = self.db.get_session()
        try:
            board = chess.Board(fen)
            side_to_move = "white" if board.turn else "black"

            puzzle = Puzzle(
                fen=fen,
                side_to_move=side_to_move,
                solution_line=solution_moves,
                theme=theme,
                theme_tags=theme_tags or [],
                rating=rating,
                source=source,
                source_game_id=source_game_id,
                created_at=datetime.utcnow(),
            )

            session.add(puzzle)
            session.commit()
            puzzle_id = puzzle.id

            # Create progress tracking record
            progress = PuzzleProgress(
                puzzle_id=puzzle_id,
                due_date=datetime.utcnow(),
            )
            session.add(progress)
            session.commit()

            # Return puzzle data before closing session
            return puzzle
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_puzzle(self, puzzle_id: int) -> Optional[Puzzle]:
        """Get a puzzle by ID."""
        session = self.db.get_session()
        try:
            return session.query(Puzzle).filter(Puzzle.id == puzzle_id).first()
        finally:
            session.close()

    def get_puzzles_by_theme(self, theme: PuzzleTheme, limit: int = 50) -> List[Puzzle]:
        """Get puzzles filtered by theme."""
        session = self.db.get_session()
        try:
            return session.query(Puzzle).filter(Puzzle.theme == theme).limit(limit).all()
        finally:
            session.close()

    def get_puzzles_by_rating_range(self, min_rating: int, max_rating: int, limit: int = 50) -> List[Puzzle]:
        """Get puzzles within a rating range."""
        session = self.db.get_session()
        try:
            return (
                session.query(Puzzle)
                .filter(Puzzle.rating >= min_rating, Puzzle.rating <= max_rating)
                .limit(limit)
                .all()
            )
        finally:
            session.close()

    def get_due_puzzles(self, limit: int = 10) -> List[Tuple[Puzzle, PuzzleProgress]]:
        """Get puzzles that are due for review (spaced repetition)."""
        session = self.db.get_session()
        try:
            now = datetime.utcnow()
            rows = (
                session.query(Puzzle, PuzzleProgress)
                .join(PuzzleProgress, Puzzle.id == PuzzleProgress.puzzle_id)
                .filter(PuzzleProgress.due_date <= now)
                .limit(limit)
                .all()
            )
            return rows
        finally:
            session.close()

    def record_puzzle_attempt(
        self,
        puzzle_id: int,
        success: bool,
        hints_used: int = 0,
    ) -> PuzzleProgress:
        """Record a puzzle attempt and update spaced repetition."""
        session = self.db.get_session()
        try:
            # Record attempt
            attempt = PuzzleAttempt(
                puzzle_id=puzzle_id,
                attempt_time=datetime.utcnow(),
                success=success,
                hints_used=hints_used,
            )
            session.add(attempt)

            # Update progress using SM-2 algorithm
            progress = session.query(PuzzleProgress).filter(PuzzleProgress.puzzle_id == puzzle_id).first()
            if not progress:
                progress = PuzzleProgress(puzzle_id=puzzle_id)
                session.add(progress)

            progress.attempts_total += 1
            if success:
                progress.attempts_correct += 1
                progress.consecutive_first_try += 1 if progress.attempts_total == 1 else 0

                # SM-2 algorithm for successful attempt
                progress.repetitions += 1
                q = 5 if progress.consecutive_first_try == 1 else 4  # Quality of recall

                if progress.repetitions == 1:
                    progress.interval_days = 1
                elif progress.repetitions == 2:
                    progress.interval_days = 3
                else:
                    progress.interval_days = progress.interval_days * progress.ease_factor

                progress.ease_factor = max(1.3, progress.ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
            else:
                # Failed attempt
                progress.lapses += 1
                progress.consecutive_first_try = 0
                progress.repetitions = 0
                progress.interval_days = 1
                progress.ease_factor = max(1.3, progress.ease_factor - 0.2)

            progress.last_result = PracticeResult.PASS if success else PracticeResult.FAIL
            progress.updated_at = datetime.utcnow()
            progress.due_date = datetime.utcnow() + timedelta(days=progress.interval_days)

            session.commit()
            return progress
        finally:
            session.close()

    def get_puzzle_statistics(self) -> dict:
        """Get overall puzzle statistics."""
        session = self.db.get_session()
        try:
            total_puzzles = session.query(Puzzle).count()
            total_attempts = session.query(PuzzleAttempt).count()
            successful_attempts = session.query(PuzzleAttempt).filter(PuzzleAttempt.success == True).count()
            success_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0

            return {
                "total_puzzles": total_puzzles,
                "total_attempts": total_attempts,
                "successful_attempts": successful_attempts,
                "success_rate": success_rate,
            }
        finally:
            session.close()
