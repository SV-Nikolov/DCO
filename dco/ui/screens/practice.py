"""
Practice mode screen for DCO.
Provides training sessions based on practice items.
"""

from datetime import datetime
from typing import List, Optional
import random

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QFrame, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
import chess

from ...data.db import Database
from ...data.models import (
    PracticeItem,
    PracticeProgress,
    PracticeCategory,
    PracticeResult,
    Session as TrainingSession,
    SessionType
)
from ...core.practice import select_practice_items, update_practice_progress
from ...core.engine import ChessEngine, EngineConfig
from ..widgets.chessboard import ChessboardWidget


class PracticeScreen(QWidget):
    """Practice mode screen."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.engine: Optional[ChessEngine] = None

        self.items: List[PracticeItem] = []
        self.current_item: Optional[PracticeItem] = None
        self.current_progress: Optional[PracticeProgress] = None
        self.current_index = 0

        self.selected_from_square: Optional[int] = None
        self.target_line: List[str] = []
        self.target_index = 0
        self.user_color: Optional[chess.Color] = None

        self.attempts_on_item = 0
        self.completed_items = 0
        self.correct_first_try = 0
        self.session_attempts = 0
        self.session_record_id: Optional[int] = None
        self.requeued_ids = set()

        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: #1f2937;
            }
            QLabel {
                color: #1f2937;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)

        # Settings panel
        settings = QFrame()
        settings.setFixedWidth(280)
        settings.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        settings_layout = QVBoxLayout(settings)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(15)

        title = QLabel("Practice Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        settings_layout.addWidget(title)

        self.blunder_cb = QCheckBox("Blunders")
        self.mistake_cb = QCheckBox("Mistakes")
        self.critical_cb = QCheckBox("Critical")
        self.inaccuracy_cb = QCheckBox("Inaccuracies")
        self.blunder_cb.setChecked(True)
        self.mistake_cb.setChecked(True)
        self.critical_cb.setChecked(True)

        settings_layout.addWidget(self.blunder_cb)
        settings_layout.addWidget(self.mistake_cb)
        settings_layout.addWidget(self.critical_cb)
        settings_layout.addWidget(self.inaccuracy_cb)

        length_label = QLabel("Session Length")
        length_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(length_label)

        self.length_combo = QComboBox()
        self.length_combo.addItems(["5", "10", "20"])
        settings_layout.addWidget(self.length_combo)

        mode_label = QLabel("Mode")
        mode_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(mode_label)

        self.strict_cb = QCheckBox("Strict (best move only)")
        self.strict_cb.setChecked(True)
        settings_layout.addWidget(self.strict_cb)

        self.due_only_cb = QCheckBox("Due only")
        self.due_only_cb.setChecked(False)
        settings_layout.addWidget(self.due_only_cb)

        self.start_btn = QPushButton("Start Session")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        self.start_btn.clicked.connect(self._start_session)
        settings_layout.addWidget(self.start_btn)

        self.restart_btn = QPushButton("Restart Position")
        self.restart_btn.setEnabled(False)
        self.restart_btn.clicked.connect(self._reset_current_position)
        settings_layout.addWidget(self.restart_btn)

        self.end_btn = QPushButton("End Session")
        self.end_btn.setEnabled(False)
        self.end_btn.clicked.connect(self._end_session)
        settings_layout.addWidget(self.end_btn)

        settings_layout.addStretch()
        layout.addWidget(settings)

        # Main practice area
        main = QVBoxLayout()

        self.status_label = QLabel("Start a practice session to begin.")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main.addWidget(self.status_label)

        self.board_widget = ChessboardWidget(size=460)
        self.board_widget.square_clicked.connect(self._on_square_clicked)
        main.addWidget(self.board_widget, alignment=Qt.AlignLeft)

        self.hint_label = QLabel("")
        self.hint_label.setStyleSheet("color: #6b7280;")
        main.addWidget(self.hint_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        main.addWidget(self.progress_bar)

        self.accuracy_label = QLabel("Accuracy: 0%")
        main.addWidget(self.accuracy_label)

        layout.addLayout(main, 1)

    def _start_session(self):
        """Start a practice session."""
        categories = self._selected_categories()
        if not categories:
            QMessageBox.warning(self, "Practice", "Select at least one category.")
            return

        length = int(self.length_combo.currentText())
        due_only = self.due_only_cb.isChecked()

        session = self.db.get_session()
        try:
            self.items = select_practice_items(session, categories, length, due_only)
            if not self.items:
                QMessageBox.information(self, "Practice", "No practice items available yet.")
                return

            # Create session record
            session_record = TrainingSession(
                type=SessionType.PRACTICE,
                started_at=datetime.utcnow(),
                accuracy=0.0
            )
            session.add(session_record)
            session.commit()
            self.session_record_id = session_record.id
        finally:
            session.close()

        self.current_index = 0
        self.completed_items = 0
        self.correct_first_try = 0
        self.session_attempts = 0
        self.requeued_ids = set()

        self.progress_bar.setMaximum(len(self.items))
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self.restart_btn.setEnabled(True)
        self.end_btn.setEnabled(True)

        self._load_current_item()

    def _load_current_item(self):
        """Load the current practice item into the UI."""
        if self.current_index >= len(self.items):
            self._end_session()
            return

        self.current_item = self.items[self.current_index]
        self.target_line = list(self.current_item.target_line_uci[:1])
        self.target_index = 0
        self.attempts_on_item = 0
        self.selected_from_square = None

        board = chess.Board(self.current_item.fen_start)
        self.user_color = board.turn
        self.board_widget.set_board(board)
        self.board_widget.set_flipped(self.user_color == chess.BLACK)
        self.board_widget.clear_arrows()
        self.board_widget.highlight_squares([])

        session = self.db.get_session()
        try:
            self.current_progress = session.query(PracticeProgress).filter(
                PracticeProgress.practice_item_id == self.current_item.id
            ).first()
        finally:
            session.close()

        self.status_label.setText(
            f"Item {self.current_index + 1}/{len(self.items)} • {self.current_item.category.name.title()}"
        )
        self.hint_label.setText("Make the best move.")

    def _reset_current_position(self, hint_text: Optional[str] = None):
        """Reset the board for the current item."""
        if not self.current_item:
            return
        board = chess.Board(self.current_item.fen_start)
        self.board_widget.set_board(board)
        self.board_widget.clear_arrows()
        self.board_widget.highlight_squares([])
        self.selected_from_square = None
        self.target_index = 0
        if hint_text is None:
            hint_text = "Try again."
        self.hint_label.setText(hint_text)

    def _on_square_clicked(self, square: int):
        """Handle board square click for move input."""
        if not self.current_item:
            return

        board = self.board_widget.board

        if self.selected_from_square is None:
            piece = board.piece_at(square)
            if piece and piece.color == board.turn:
                self.selected_from_square = square
                self.board_widget.highlight_squares([square])
            return

        move = chess.Move(self.selected_from_square, square)
        self.selected_from_square = None
        self.board_widget.highlight_squares([])

        # Handle promotion (default to queen)
        if board.piece_at(move.from_square) and board.piece_at(move.from_square).piece_type == chess.PAWN:
            rank = chess.square_rank(move.to_square)
            if rank == 0 or rank == 7:
                move = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)

        if move not in board.legal_moves:
            return

        self._evaluate_move(move)

    def _evaluate_move(self, move: chess.Move):
        """Evaluate the user's move against the target line."""
        if not self.current_item:
            return

        self.attempts_on_item += 1
        self.session_attempts += 1

        expected_uci = self.target_line[self.target_index] if self.target_line else None
        is_correct = expected_uci == move.uci() if expected_uci else False

        # Lenient mode: accept any top move
        if not self.strict_cb.isChecked() and not is_correct:
            is_correct = self._is_lenient_move(move)

        if not is_correct:
            # Wrong move: show arrow and hint
            self.board_widget.add_arrow(move.from_square, move.to_square, color="red")
            if expected_uci:
                correct_move = chess.Move.from_uci(expected_uci)
                san = self.board_widget.board.san(correct_move)
                self.board_widget.add_arrow(correct_move.from_square, correct_move.to_square, color="green")
                self.hint_label.setText(f"Correct move: {san}")
            else:
                self.hint_label.setText("Incorrect.")
            if self.current_item and self.current_item.id not in self.requeued_ids:
                self.items.append(self.current_item)
                self.requeued_ids.add(self.current_item.id)
            QTimer.singleShot(1000, self._advance_after_wrong)
            return

        # Correct move
        self.board_widget.board.push(move)
        self.board_widget.set_last_move(move)
        self.board_widget.update_board()
        self.board_widget.clear_arrows()

        if self.attempts_on_item == 1:
            self.correct_first_try += 1

        self._complete_item()

    def _complete_item(self):
        """Complete the current item and move to next."""
        if not self.current_item or not self.current_progress:
            return

        # Update progress
        result = PracticeResult.PASS_FIRST_TRY if self.attempts_on_item == 1 else PracticeResult.PASS
        update_practice_progress(self.current_progress, result, self.attempts_on_item == 1)

        session = self.db.get_session()
        try:
            session.merge(self.current_progress)
            session.commit()
        finally:
            session.close()

        self.completed_items += 1
        self.progress_bar.setValue(self.completed_items)

        accuracy = int((self.correct_first_try / max(1, self.completed_items)) * 100)
        self.accuracy_label.setText(f"Accuracy: {accuracy}%")

        self.current_index += 1
        if self.current_item.id not in self.requeued_ids and self.attempts_on_item > 1:
            self.items.append(self.current_item)
            self.requeued_ids.add(self.current_item.id)
        self._load_current_item()

    def _advance_after_wrong(self):
        """Switch to a different random item after a wrong move."""
        if not self.items:
            return
        if len(self.items) == 1:
            self._load_current_item()
            return

        current_id = self.current_item.id if self.current_item else None
        candidates = [item for item in self.items if item.id != current_id]
        if not candidates:
            self._load_current_item()
            return

        self.current_item = random.choice(candidates)
        self.target_line = list(self.current_item.target_line_uci[:1])
        self.target_index = 0
        self.attempts_on_item = 0
        self.selected_from_square = None

        board = chess.Board(self.current_item.fen_start)
        self.user_color = board.turn
        self.board_widget.set_board(board)
        self.board_widget.set_flipped(self.user_color == chess.BLACK)
        self.board_widget.clear_arrows()
        self.board_widget.highlight_squares([])

        self.status_label.setText(
            f"Item {self.current_index + 1}/{len(self.items)} • {self.current_item.category.name.title()}"
        )
        self.hint_label.setText("Make the best move.")

    def _end_session(self):
        """End the current practice session."""
        if self.session_record_id is not None:
            session = self.db.get_session()
            try:
                record = session.query(TrainingSession).get(self.session_record_id)
                if record:
                    accuracy = (self.correct_first_try / max(1, self.completed_items)) * 100
                    record.ended_at = datetime.utcnow()
                    record.accuracy = accuracy
                    session.commit()
            finally:
                session.close()

        self._stop_engine()
        self.start_btn.setEnabled(True)
        self.restart_btn.setEnabled(False)
        self.end_btn.setEnabled(False)
        self.status_label.setText("Session complete.")
        self.hint_label.setText("")

    def _selected_categories(self) -> List[PracticeCategory]:
        """Get selected practice categories from UI."""
        categories = []
        if self.blunder_cb.isChecked():
            categories.append(PracticeCategory.BLUNDER)
        if self.mistake_cb.isChecked():
            categories.append(PracticeCategory.MISTAKE)
        if self.critical_cb.isChecked():
            categories.append(PracticeCategory.CRITICAL)
        if self.inaccuracy_cb.isChecked():
            categories.append(PracticeCategory.INACCURACY)
        return categories

    def _is_lenient_move(self, move: chess.Move) -> bool:
        """Allow top moves in lenient mode using MultiPV."""
        if not self.current_item:
            return False

        self._ensure_engine()
        if not self.engine:
            return False

        board = self.board_widget.board
        original_multipv = self.engine.config.multipv

        try:
            self.engine.config.multipv = 3
            eval_info = self.engine.evaluate(board)
            pv_moves = []
            for pv in eval_info.pv_lines:
                if pv:
                    pv_moves.append(pv[0])
            return move in pv_moves
        finally:
            self.engine.config.multipv = original_multipv

    def _ensure_engine(self):
        """Start the engine if needed."""
        if self.engine:
            return
        config = EngineConfig(depth=14, time_per_move=0.3)
        self.engine = ChessEngine(config)
        self.engine.start()

    def _stop_engine(self):
        """Stop the engine if running."""
        if self.engine:
            self.engine.stop()
            self.engine = None
