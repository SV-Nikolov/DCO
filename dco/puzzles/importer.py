"""
Puzzle importer for DCO.
Imports puzzles from various formats: Lichess CSV, PGN, EPD, FEN.
"""

from __future__ import annotations

import csv
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
import chess
import chess.pgn

from ..data.models import PuzzleTheme
from .puzzle_manager import PuzzleManager


class PuzzleImporter:
    """Imports puzzles from various formats."""

    def __init__(self, puzzle_manager: PuzzleManager):
        self.puzzle_manager = puzzle_manager

    def import_lichess_csv(self, filepath: str) -> int:
        """
        Import lichess puzzle data from CSV format.
        Format: PuzzleID,FEN,Moves,Rating,RatingDeviation,Popularity,Themes,GameUrl
        """
        count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    fen = row["FEN"]
                    moves = row["Moves"].split()
                    rating = int(row["Rating"]) if row["Rating"] else 1500
                    themes = row.get("Themes", "").split(",") if row.get("Themes") else []

                    # Map Lichess themes to our PuzzleTheme enum
                    primary_theme = self._map_lichess_theme(themes[0] if themes else "")
                    if not primary_theme:
                        primary_theme = PuzzleTheme.TACTIC

                    puzzle = self.puzzle_manager.create_puzzle(
                        fen=fen,
                        solution_moves=moves,
                        theme=primary_theme,
                        rating=rating,
                        source="lichess",
                        theme_tags=themes,
                    )
                    count += 1
                except Exception as e:
                    print(f"Error importing puzzle: {e}")
                    continue

        return count

    def import_pgn_puzzles(self, filepath: str, theme: PuzzleTheme = PuzzleTheme.TACTIC) -> int:
        """
        Import puzzles from PGN format.
        Each game should have:
        - [FEN "..."] header
        - [Puzzle "yes"] header (optional)
        - Solution moves in the main line
        """
        count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            game = chess.pgn.read_game(f)
            while game:
                try:
                    fen = game.headers.get("FEN")
                    if not fen:
                        game = chess.pgn.read_game(f)
                        continue

                    # Extract solution moves from main line
                    moves = []
                    board = chess.Board(fen)
                    node = game
                    while node.variations:
                        move = node.variations[0].move
                        moves.append(move.uci())
                        board.push(move)
                        node = node.variations[0]

                    if moves:
                        rating = self._extract_rating(game.headers)
                        theme_str = game.headers.get("Puzzle", "").lower()
                        puzzle_theme = self._map_theme(theme_str, theme)

                        puzzle = self.puzzle_manager.create_puzzle(
                            fen=fen,
                            solution_moves=moves,
                            theme=puzzle_theme,
                            rating=rating,
                            source="pgn",
                        )
                        count += 1

                except Exception as e:
                    print(f"Error importing puzzle from PGN: {e}")

                game = chess.pgn.read_game(f)

        return count

    def import_epd_puzzles(self, filepath: str, theme: PuzzleTheme = PuzzleTheme.TACTIC) -> int:
        """
        Import puzzles from EPD format.
        Each line is an EPD record. The 'bm' (best moves) field contains solutions.
        """
        count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    # Parse EPD line
                    parts = line.split(";")
                    fen_part = parts[0].strip()

                    # Extract FEN and operations
                    tokens = fen_part.split()
                    if len(tokens) < 6:
                        continue

                    fen = " ".join(tokens[:4]) if len(tokens) >= 4 else " ".join(tokens)
                    operations_str = " ".join(tokens[4:])

                    # Extract best moves from 'bm' operation
                    moves = []
                    if "bm" in operations_str:
                        start = operations_str.find("bm ") + 3
                        end = operations_str.find(";", start)
                        if end == -1:
                            end = len(operations_str)
                        bm_str = operations_str[start:end].strip()
                        # Parse moves
                        board = chess.Board(fen)
                        move_strs = bm_str.split()
                        for move_str in move_strs:
                            try:
                                move = board.parse_san(move_str)
                                moves.append(move.uci())
                            except:
                                pass

                    if moves:
                        rating = 1500  # Default rating
                        puzzle = self.puzzle_manager.create_puzzle(
                            fen=fen,
                            solution_moves=moves,
                            theme=theme,
                            rating=rating,
                            source="epd",
                        )
                        count += 1

                except Exception as e:
                    print(f"Error importing puzzle from EPD: {e}")
                    continue

        return count

    def _map_lichess_theme(self, theme_str: str) -> Optional[PuzzleTheme]:
        """Map Lichess theme names to our PuzzleTheme enum."""
        mapping = {
            "mateIn1": PuzzleTheme.MATE,
            "mateIn2": PuzzleTheme.MATE,
            "mateIn3": PuzzleTheme.MATE,
            "mateIn4": PuzzleTheme.MATE,
            "mateIn5": PuzzleTheme.MATE,
            "mate": PuzzleTheme.MATE,
            "winMaterial": PuzzleTheme.MATERIAL,
            "material": PuzzleTheme.MATERIAL,
            "fork": PuzzleTheme.TACTIC,
            "pin": PuzzleTheme.TACTIC,
            "skewer": PuzzleTheme.TACTIC,
            "sacrifice": PuzzleTheme.TACTIC,
            "tactic": PuzzleTheme.TACTIC,
            "endgame": PuzzleTheme.ENDGAME,
            "opening": PuzzleTheme.OPENING,
            "defense": PuzzleTheme.DEFENSE,
            "positional": PuzzleTheme.POSITIONAL,
        }
        return mapping.get(theme_str)

    def _map_theme(self, theme_str: str, default: PuzzleTheme) -> PuzzleTheme:
        """Map theme string to PuzzleTheme enum."""
        if not theme_str:
            return default

        theme_str = theme_str.lower()
        mapped = self._map_lichess_theme(theme_str)
        return mapped if mapped else default

    def _extract_rating(self, headers: Dict[str, Any]) -> int:
        """Extract rating from PGN headers."""
        if "Rating" in headers:
            try:
                return int(headers["Rating"])
            except ValueError:
                pass
        return 1500  # Default rating
