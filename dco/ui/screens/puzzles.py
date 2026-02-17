"""
Puzzle solving screen for DCO.
Interactive puzzle interface with hints and progress tracking.
"""

from __future__ import annotations

import random
from typing import Optional, List
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QSpinBox, QProgressBar, QMessageBox
)
from PySide6.QtGui import QFont

import chess
from ..widgets.chessboard import ChessboardWidget

from ...data.db import Database
from ...data.models import PuzzleTheme
from ...puzzles import PuzzleManager


class PuzzleScreen(QWidget):
    """Interactive puzzle solving screen."""

    puzzle_completed = Signal()
    puzzle_skipped = Signal()

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.puzzle_manager = PuzzleManager(db)

        self.current_puzzle = None
        self.current_board = None
        self.solution_moves = []
        self.move_index = 0
        self.hints_used = 0
        self.session_puzzles_solved = 0
        self.session_hints_used = 0
        self.session_start_time = None

        self.init_ui()
        self.load_next_puzzle()

    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Styled by global stylesheet

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)

        # Settings panel
        settings = QFrame()
        settings.setObjectName("cardFrame")
        settings.setFixedWidth(280)
        settings_layout = QVBoxLayout(settings)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(15)

        title = QLabel("Puzzle Settings")
        title.setObjectName("sectionTitle")
        settings_layout.addWidget(title)

        # Theme filter
        theme_label = QLabel("Theme")
        theme_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("All Themes", None)
        for theme in PuzzleTheme:
            self.theme_combo.addItem(theme.value.capitalize(), theme)
        settings_layout.addWidget(self.theme_combo)

        # Rating range
        rating_label = QLabel("Rating Range")
        rating_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(rating_label)

        rating_layout = QHBoxLayout()
        self.min_rating_spin = QSpinBox()
        self.min_rating_spin.setRange(800, 2800)
        self.min_rating_spin.setValue(1200)
        rating_layout.addWidget(QLabel("Min:"))
        rating_layout.addWidget(self.min_rating_spin)
        settings_layout.addLayout(rating_layout)

        rating_layout2 = QHBoxLayout()
        self.max_rating_spin = QSpinBox()
        self.max_rating_spin.setRange(800, 2800)
        self.max_rating_spin.setValue(1800)
        rating_layout2.addWidget(QLabel("Max:"))
        rating_layout2.addWidget(self.max_rating_spin)
        settings_layout.addLayout(rating_layout2)

        # Mode selection
        mode_label = QLabel("Mode")
        mode_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(mode_label)

        self.training_mode_btn = QPushButton("Training")
        self.training_mode_btn.setObjectName("primaryButton")
        self.training_mode_btn.setCheckable(True)
        self.training_mode_btn.setChecked(True)
        self.training_mode_btn.clicked.connect(self._on_training_mode)
        settings_layout.addWidget(self.training_mode_btn)

        self.blitz_mode_btn = QPushButton("Blitz")
        self.blitz_mode_btn.setObjectName("secondaryButton")
        self.blitz_mode_btn.setCheckable(True)
        self.blitz_mode_btn.clicked.connect(self._on_blitz_mode)
        settings_layout.addWidget(self.blitz_mode_btn)

        # Stats section
        stats_label = QLabel("Session Stats")
        stats_label.setObjectName("sectionTitle")
        settings_layout.addWidget(stats_label)

        self.solved_label = QLabel("Solved: 0")
        settings_layout.addWidget(self.solved_label)

        self.accuracy_label = QLabel("Accuracy: 0%")
        settings_layout.addWidget(self.accuracy_label)

        # Action buttons
        settings_layout.addSpacing(20)

        self.retry_btn = QPushButton("Retry Puzzle")
        self.retry_btn.setObjectName("secondaryButton")
        self.retry_btn.clicked.connect(self._on_retry)
        settings_layout.addWidget(self.retry_btn)

        self.skip_btn = QPushButton("Skip Puzzle")
        self.skip_btn.setObjectName("secondaryButton")
        self.skip_btn.clicked.connect(self._on_skip)
        settings_layout.addWidget(self.skip_btn)

        self.give_up_btn = QPushButton("Give Up")
        self.give_up_btn.setObjectName("secondaryButton")
        self.give_up_btn.clicked.connect(self._on_give_up)
        settings_layout.addWidget(self.give_up_btn)

        settings_layout.addStretch()
        layout.addWidget(settings)

        # Main puzzle area
        main = QVBoxLayout()

        # Puzzle info
        self.puzzle_info = QLabel("Loading puzzle...")
        self.puzzle_info.setObjectName("cardTitle")
        main.addWidget(self.puzzle_info)

        # Board
        self.board_widget = ChessboardWidget(size=460)
        self.board_widget.square_clicked.connect(self._on_square_clicked)
        main.addWidget(self.board_widget, alignment=Qt.AlignLeft)

        # Hints section
        hints_frame = QFrame()
        hints_frame.setObjectName("cardFrame")
        hints_layout = QVBoxLayout(hints_frame)

        hints_title = QLabel("Hints")
        hints_title.setObjectName("cardTitle")
        hints_layout.addWidget(hints_title)

        self.hint_btn = QPushButton("Show First Move")
        self.hint_btn.setObjectName("secondaryButton")
        self.hint_btn.clicked.connect(self._on_show_hint)
        hints_layout.addWidget(self.hint_btn)

        self.hint_label = QLabel("")
        self.hint_label.setObjectName("mutedText")
        self.hint_label.setWordWrap(True)
        hints_layout.addWidget(self.hint_label)

        main.addWidget(hints_frame)

        # Status/feedback
        self.status_label = QLabel("")
        self.status_label.setObjectName("mutedText")
        main.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main.addWidget(self.progress_bar)

        main.addStretch()
        layout.addLayout(main, 1)

    def load_next_puzzle(self) -> None:
        """Load the next puzzle based on current filters."""
        try:
            theme = self.theme_combo.currentData()
            min_rating = self.min_rating_spin.value()
            max_rating = self.max_rating_spin.value()

            if theme:
                puzzles = self.puzzle_manager.get_puzzles_by_theme(theme, limit=50)
            else:
                puzzles = self.puzzle_manager.get_puzzles_by_rating_range(min_rating, max_rating, limit=50)

            if not puzzles:
                QMessageBox.information(self, "No Puzzles", "No puzzles available with selected filters.")
                return

            # Select random puzzle from available
            self.current_puzzle = random.choice(puzzles)
            self.move_index = 0
            self.hints_used = 0

            # Setup board
            self.current_board = chess.Board(self.current_puzzle.fen)
            self.solution_moves = self.current_puzzle.solution_line
            self.initial_fen = self.current_puzzle.fen  # Store initial position for retry

            # Flip board if playing as black
            is_black_to_move = self.current_board.turn == chess.BLACK
            self.board_widget.set_flipped(is_black_to_move)

            # Update UI
            theme_name = self.current_puzzle.theme.value.capitalize() if self.current_puzzle.theme else "Unknown"
            side = "Black" if is_black_to_move else "White"
            self.puzzle_info.setText(f"{theme_name} • Rating: {self.current_puzzle.rating} • Playing as {side}")
            self.hint_label.setText("")
            self.status_label.setText("")
            self.hint_btn.setEnabled(True)

            # Clear any selected square
            if hasattr(self, "_selected_square"):
                delattr(self, "_selected_square")

            self._update_board_display()

            if not self.session_start_time:
                self.session_start_time = datetime.utcnow()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load puzzle: {e}")

    def _update_board_display(self) -> None:
        """Update the board display."""
        if self.current_board and self.board_widget:
            self.board_widget.set_board(self.current_board)
            self.board_widget.clear_arrows()
            # Highlight last move if available
            if self.move_index > 0 and self.solution_moves:
                move_uci = self.solution_moves[self.move_index - 1]
                move = chess.Move.from_uci(move_uci)
                self.board_widget.set_last_move(move)

    def _on_square_clicked(self, square: int) -> None:
        """Handle board square clicks for move input."""
        if not self.current_puzzle or self.move_index >= len(self.solution_moves):
            return

        if not hasattr(self, "_selected_square"):
            self._selected_square = square
            # Highlight selected square
            self.board_widget.highlight_squares([square])
        else:
            from_square = self._selected_square
            to_square = square
            
            # Clear selection
            delattr(self, "_selected_square")
            self.board_widget.highlight_squares([])

            try:
                # Try to construct move
                move = chess.Move(from_square, to_square)
                
                # Check for promotion
                if self.current_board.piece_at(from_square) and \
                   self.current_board.piece_at(from_square).piece_type == chess.PAWN:
                    if (chess.square_rank(to_square) == 7 and self.current_board.turn == chess.WHITE) or \
                       (chess.square_rank(to_square) == 0 and self.current_board.turn == chess.BLACK):
                        move = chess.Move(from_square, to_square, promotion=chess.QUEEN)

                # Check if it's a legal move
                if move in self.current_board.legal_moves:
                    # Check if it's the correct solution move
                    solution_uci = self.solution_moves[self.move_index]
                    solution_move = chess.Move.from_uci(solution_uci)

                    if move == solution_move:
                        # Correct move!
                        self.current_board.push(move)
                        self.move_index += 1
                        self.status_label.setText("✓ Correct!")
                        self._update_board_display()

                        if self.move_index >= len(self.solution_moves):
                            # Puzzle complete
                            self._on_puzzle_complete()
                        else:
                            # Re-enable hint for next move
                            self.hint_btn.setEnabled(True)
                    else:
                        # Wrong move
                        self.status_label.setText("✗ Wrong move. Try again.")
                else:
                    self.status_label.setText("✗ Illegal move.")

            except ValueError:
                pass

    def _on_show_hint(self) -> None:
        """Show hint for current puzzle."""
        if not self.current_puzzle or self.move_index >= len(self.solution_moves):
            return

        solution_uci = self.solution_moves[self.move_index]
        move = chess.Move.from_uci(solution_uci)
        san = self.current_board.san(move)

        # Show text hint
        self.hint_label.setText(f"Next move: {san}")
        
        # Show green arrow on board
        self.board_widget.clear_arrows()
        self.board_widget.add_arrow(move.from_square, move.to_square, "green")
        
        self.hints_used += 1
        self.hint_btn.setEnabled(False)

    def _on_puzzle_complete(self) -> None:
        """Handle puzzle completion."""
        self.session_puzzles_solved += 1
        self.session_hints_used += self.hints_used

        success = self.hints_used == 0
        self.puzzle_manager.record_puzzle_attempt(self.current_puzzle.id, success, self.hints_used)

        accuracy = (self.session_puzzles_solved - self.session_hints_used / max(1, self.session_puzzles_solved)) * 100
        self.solved_label.setText(f"Solved: {self.session_puzzles_solved}")
        self.accuracy_label.setText(f"Accuracy: {int(accuracy)}%")

        self.status_label.setText("✓ Puzzle solved!")

        # Load next puzzle after delay
        QTimer.singleShot(2000, self.load_next_puzzle)

    def _on_retry(self) -> None:
        """Retry current puzzle from the beginning."""
        if not self.current_puzzle:
            return
        
        # Reset to initial position
        self.current_board = chess.Board(self.initial_fen)
        self.move_index = 0
        self.hints_used = 0
        
        # Clear UI
        self.hint_label.setText("")
        self.status_label.setText("Puzzle reset. Try again!")
        self.hint_btn.setEnabled(True)
        
        # Clear any selected square
        if hasattr(self, "_selected_square"):
            delattr(self, "_selected_square")
        
        self._update_board_display()

    def _on_skip(self) -> None:
        """Skip current puzzle."""
        if self.current_puzzle:
            self.puzzle_skipped.emit()
        self.load_next_puzzle()

    def _on_give_up(self) -> None:
        """Give up on current puzzle and show solution."""
        if not self.current_puzzle:
            return

        # Show remaining solution moves
        remaining = self.solution_moves[self.move_index:]
        if remaining:
            move = chess.Move.from_uci(remaining[0])
            san = self.current_board.san(move)
            self.status_label.setText(f"Solution: {' '.join([chess.Move.from_uci(m).uci() for m in remaining])}")

        # Record as failed
        self.puzzle_manager.record_puzzle_attempt(self.current_puzzle.id, False, self.hints_used)

        QTimer.singleShot(3000, self.load_next_puzzle)

    def _on_training_mode(self) -> None:
        """Lock to training mode."""
        if self.training_mode_btn.isChecked():
            self.blitz_mode_btn.setChecked(False)

    def _on_blitz_mode(self) -> None:
        """Lock to blitz mode."""
        if self.blitz_mode_btn.isChecked():
            self.training_mode_btn.setChecked(False)
