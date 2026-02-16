"""
Puzzle generator for DCO.
Generates puzzles from user game critical positions and mistakes.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import chess
import chess.pgn

from ..data.db import Database
from ..data.models import Game, Analysis, Move, MoveClassification, PuzzleTheme
from .puzzle_manager import PuzzleManager


class PuzzleGenerator:
    """Generates puzzles from user games."""

    def __init__(self, db: Database, puzzle_manager: PuzzleManager):
        self.db = db
        self.puzzle_manager = puzzle_manager

    def generate_from_game(self, game_id: int) -> List[int]:
        """
        Generate puzzles from a single game.
        Extracts critical positions where user made mistakes.
        Returns list of created puzzle IDs.
        """
        session = self.db.get_session()
        try:
            game = session.query(Game).filter(Game.id == game_id).first()
            if not game:
                return []

            analysis = session.query(Analysis).filter(Analysis.game_id == game_id).first()
            if not analysis:
                return []

            # Get all moves from game
            moves = session.query(Move).filter(Move.game_id == game_id).order_by(Move.move_number).all()
            if not moves:
                return []

            puzzle_ids = []

            # Build board from PGN
            try:
                pgn = chess.pgn.read_game(game.get_pgn())
                if not pgn:
                    return []

                board = chess.Board()
                move_index = 0

                for node in pgn.mainline():
                    board.push(node.move)

                    # Check if there's a corresponding database move
                    if move_index < len(moves):
                        db_move = moves[move_index]

                        # Extract critical and blunder positions
                        if db_move.classification in [
                            MoveClassification.BLUNDER,
                            MoveClassification.CRITICAL,
                            MoveClassification.MISTAKE,
                        ]:
                            # Generate puzzle starting from 2 moves before mistake
                            puzzle_fen = self._get_position_before_move(pgn, move_index - 2)
                            if puzzle_fen:
                                solution_moves = self._extract_solution(pgn, move_index)
                                if solution_moves:
                                    theme = self._classify_mistake_theme(db_move.classification)
                                    rating = self._estimate_puzzle_rating(db_move)

                                    puzzle = self.puzzle_manager.create_puzzle(
                                        fen=puzzle_fen,
                                        solution_moves=solution_moves,
                                        theme=theme,
                                        rating=rating,
                                        source="own_game",
                                        source_game_id=game_id,
                                        theme_tags=[db_move.classification.value],
                                    )
                                    puzzle_ids.append(puzzle.id)

                    move_index += 1

            except Exception as e:
                print(f"Error generating puzzles from game {game_id}: {e}")

            return puzzle_ids
        finally:
            session.close()

    def generate_from_games(self, game_ids: Optional[List[int]] = None, limit: int = 50) -> int:
        """
        Generate puzzles from multiple games.
        If game_ids is None, generates from all games.
        Returns total number of puzzles created.
        """
        session = self.db.get_session()
        try:
            query = session.query(Game)
            if game_ids:
                query = query.filter(Game.id.in_(game_ids))
            games = query.limit(limit).all()

            total_puzzles = 0
            for game in games:
                puzzle_ids = self.generate_from_game(game.id)
                total_puzzles += len(puzzle_ids)

            return total_puzzles
        finally:
            session.close()

    def _get_position_before_move(self, pgn, move_index: int) -> Optional[str]:
        """Get FEN before a specific move index."""
        try:
            board = chess.Board()
            move_count = 0

            for node in pgn.mainline():
                if move_count == move_index:
                    return board.fen()
                board.push(node.move)
                move_count += 1

            return board.fen()
        except:
            return None

    def _extract_solution(self, pgn, from_move_index: int, max_moves: int = 3) -> Optional[List[str]]:
        """Extract next best moves starting from a position."""
        try:
            moves = []
            move_count = 0

            for node in pgn.mainline():
                if move_count >= from_move_index and move_count < from_move_index + max_moves:
                    moves.append(node.move.uci())

                if move_count >= from_move_index + max_moves:
                    break

                move_count += 1

            return moves if moves else None
        except:
            return None

    def _classify_mistake_theme(self, classification: MoveClassification) -> PuzzleTheme:
        """Classify puzzle theme based on move classification."""
        theme_map = {
            MoveClassification.BLUNDER: PuzzleTheme.TACTIC,
            MoveClassification.CRITICAL: PuzzleTheme.CALCULATION,
            MoveClassification.MISTAKE: PuzzleTheme.TACTIC,
            MoveClassification.INACCURACY: PuzzleTheme.POSITIONAL,
        }
        return theme_map.get(classification, PuzzleTheme.TACTIC)

    def _estimate_puzzle_rating(self, move: Move) -> int:
        """Estimate puzzle difficulty based on move characteristics."""
        # Simple heuristic: use eval loss as basis
        base_rating = 1500

        # Adjustments based on classification
        if move.classification == MoveClassification.BLUNDER:
            base_rating += 300
        elif move.classification == MoveClassification.CRITICAL:
            base_rating += 200
        elif move.classification == MoveClassification.MISTAKE:
            base_rating += 100

        # Range: 800-2800
        return max(800, min(2800, base_rating))
