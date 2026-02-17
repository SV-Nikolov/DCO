"""
Play vs Computer screen for DCO.
Allows users to play against Stockfish with configurable settings.
"""

from __future__ import annotations

import random
import logging
from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSlider, QComboBox, QCheckBox, QSpinBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread

import chess
import chess.pgn

from ..widgets.chessboard import ChessboardWidget
from ..widgets.move_list import MoveListWidget
from ...data.db import Database
from ...data.models import Game
from ...engine import EngineController, DualGameClock

logger = logging.getLogger(__name__)


class EngineThread(QThread):
    """Thread for running engine calculations without blocking UI."""
    
    move_calculated = Signal(object)  # Emits chess.Move
    
    def __init__(self, engine: EngineController, board: chess.Board):
        super().__init__()
        self.engine = engine
        self.board = board.copy()
    
    def run(self):
        """Calculate engine move in background."""
        move = self.engine.get_best_move(self.board)
        if move:
            self.move_calculated.emit(move)


class PlayScreen(QWidget):
    """Screen for playing against the computer."""
    
    game_completed = Signal()
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.engine = EngineController()
        self.game_clock: Optional[DualGameClock] = None
        self.engine_thread: Optional[EngineThread] = None
        
        # Game state
        self.board = chess.Board()
        self.game_active = False
        self.user_color = chess.WHITE
        self.engine_elo = 2000
        self.time_control_minutes = 5
        self.increment_seconds = 3
        self.takebacks_enabled = True
        self.hints_enabled = True
        self.auto_save = True
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)
        
        # Left: Setup/Settings panel
        setup_panel = self._create_setup_panel()
        layout.addWidget(setup_panel)
        
        # Center: Game area
        game_area = self._create_game_area()
        layout.addWidget(game_area, 1)
        
        # Right: Info panel
        info_panel = self._create_info_panel()
        layout.addWidget(info_panel)
    
    def _create_setup_panel(self) -> QWidget:
        """Create the setup/settings panel."""
        panel = QFrame()
        panel.setObjectName("cardFrame")
        panel.setFixedWidth(280)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Game Setup")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Opponent Strength
        strength_label = QLabel("Opponent Strength")
        strength_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(strength_label)
        
        self.elo_slider = QSlider(Qt.Horizontal)
        self.elo_slider.setMinimum(1000)
        self.elo_slider.setMaximum(3200)
        self.elo_slider.setValue(2000)
        self.elo_slider.setTickPosition(QSlider.TicksBelow)
        self.elo_slider.setTickInterval(200)
        self.elo_slider.valueChanged.connect(self._on_elo_changed)
        layout.addWidget(self.elo_slider)
        
        self.elo_label = QLabel("2000 Elo")
        self.elo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.elo_label)
        
        # Time Control
        time_label = QLabel("Time Control")
        time_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(time_label)
        
        self.time_control_combo = QComboBox()
        self.time_control_combo.addItems([
            "1+0 (Bullet)",
            "2+1 (Bullet)",
            "3+0 (Blitz)",
            "3+2 (Blitz)",
            "5+0 (Blitz)",
            "5+3 (Blitz)",
            "10+0 (Rapid)",
            "10+5 (Rapid)",
            "Custom"
        ])
        self.time_control_combo.setCurrentText("5+3 (Blitz)")
        self.time_control_combo.currentTextChanged.connect(self._on_time_control_changed)
        layout.addWidget(self.time_control_combo)
        
        # Custom time controls (hidden by default)
        self.custom_time_frame = QFrame()
        custom_layout = QVBoxLayout(self.custom_time_frame)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(5)
        
        minutes_layout = QHBoxLayout()
        minutes_layout.addWidget(QLabel("Minutes:"))
        self.custom_minutes_spin = QSpinBox()
        self.custom_minutes_spin.setMinimum(1)
        self.custom_minutes_spin.setMaximum(60)
        self.custom_minutes_spin.setValue(5)
        minutes_layout.addWidget(self.custom_minutes_spin)
        custom_layout.addLayout(minutes_layout)
        
        increment_layout = QHBoxLayout()
        increment_layout.addWidget(QLabel("Increment:"))
        self.custom_increment_spin = QSpinBox()
        self.custom_increment_spin.setMinimum(0)
        self.custom_increment_spin.setMaximum(30)
        self.custom_increment_spin.setValue(3)
        increment_layout.addWidget(self.custom_increment_spin)
        custom_layout.addLayout(increment_layout)
        
        self.custom_time_frame.setVisible(False)
        layout.addWidget(self.custom_time_frame)
        
        # Color selection
        color_label = QLabel("Play As")
        color_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(color_label)
        
        self.color_combo = QComboBox()
        self.color_combo.addItems(["White", "Black", "Random"])
        layout.addWidget(self.color_combo)
        
        # Options
        options_label = QLabel("Options")
        options_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(options_label)
        
        self.takebacks_check = QCheckBox("Allow Takebacks")
        self.takebacks_check.setChecked(True)
        layout.addWidget(self.takebacks_check)
        
        self.hints_check = QCheckBox("Enable Hints")
        self.hints_check.setChecked(True)
        layout.addWidget(self.hints_check)
        
        self.autosave_check = QCheckBox("Auto-save Game")
        self.autosave_check.setChecked(True)
        layout.addWidget(self.autosave_check)
        
        layout.addStretch()
        
        # Start Game button
        self.start_button = QPushButton("Start New Game")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setMinimumHeight(50)
        self.start_button.clicked.connect(self._on_start_game)
        layout.addWidget(self.start_button)
        
        return panel
    
    def _create_game_area(self) -> QWidget:
        """Create the main game area with board and controls."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Clocks
        clocks_layout = QHBoxLayout()
        
        # Black clock (top)
        black_clock_frame = QFrame()
        black_clock_frame.setObjectName("cardFrame")
        black_clock_layout = QHBoxLayout(black_clock_frame)
        black_clock_layout.setContentsMargins(15, 10, 15, 10)
        
        self.black_name_label = QLabel("Stockfish (2000)")
        self.black_time_label = QLabel("5:00")
        self.black_time_label.setObjectName("statValue")
        self.black_time_label.setStyleSheet("font-size: 28px;")
        
        black_clock_layout.addWidget(self.black_name_label)
        black_clock_layout.addStretch()
        black_clock_layout.addWidget(self.black_time_label)
        
        clocks_layout.addWidget(black_clock_frame, 1)
        layout.addLayout(clocks_layout)
        
        # Board
        self.board_widget = ChessboardWidget(size=520)
        self.board_widget.square_clicked.connect(self._on_square_clicked)
        layout.addWidget(self.board_widget, alignment=Qt.AlignCenter)
        
        # White clock (bottom)
        white_clock_frame = QFrame()
        white_clock_frame.setObjectName("cardFrame")
        white_clock_layout = QHBoxLayout(white_clock_frame)
        white_clock_layout.setContentsMargins(15, 10, 15, 10)
        
        self.white_name_label = QLabel("You")
        self.white_time_label = QLabel("5:00")
        self.white_time_label.setObjectName("statValue")
        self.white_time_label.setStyleSheet("font-size: 28px;")
        
        white_clock_layout.addWidget(self.white_name_label)
        white_clock_layout.addStretch()
        white_clock_layout.addWidget(self.white_time_label)
        
        layout.addWidget(white_clock_frame)
        
        # Game controls
        controls_layout = QHBoxLayout()
        
        self.hint_button = QPushButton("Hint")
        self.hint_button.setObjectName("secondaryButton")
        self.hint_button.clicked.connect(self._on_request_hint)
        self.hint_button.setEnabled(False)
        controls_layout.addWidget(self.hint_button)
        
        self.takeback_button = QPushButton("Takeback")
        self.takeback_button.setObjectName("secondaryButton")
        self.takeback_button.clicked.connect(self._on_takeback)
        self.takeback_button.setEnabled(False)
        controls_layout.addWidget(self.takeback_button)
        
        self.resign_button = QPushButton("Resign")
        self.resign_button.setObjectName("secondaryButton")
        self.resign_button.clicked.connect(self._on_resign)
        self.resign_button.setEnabled(False)
        controls_layout.addWidget(self.resign_button)
        
        layout.addLayout(controls_layout)
        
        # Status label
        self.status_label = QLabel("Configure game settings and click 'Start New Game'")
        self.status_label.setObjectName("mutedText")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        return widget
    
    def _create_info_panel(self) -> QWidget:
        """Create the info panel with move list."""
        panel = QFrame()
        panel.setObjectName("cardFrame")
        panel.setFixedWidth(280)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Game Moves")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Move list
        self.move_list = MoveListWidget()
        self.move_list.move_selected.connect(self._on_move_selected)
        layout.addWidget(self.move_list, 1)
        
        return panel
    
    def _on_elo_changed(self, value: int):
        """Handle Elo slider change."""
        self.elo_label.setText(f"{value} Elo")
        self.engine_elo = value
        
        # Update opponent name label if game not started
        if not self.game_active:
            self.black_name_label.setText(f"Stockfish ({value})")
    
    def _on_time_control_changed(self, text: str):
        """Handle time control selection change."""
        is_custom = text == "Custom"
        self.custom_time_frame.setVisible(is_custom)
        
        if not is_custom:
            # Parse standard time control
            parts = text.split("+")
            if len(parts) >= 2:
                self.time_control_minutes = int(parts[0])
                self.increment_seconds = int(parts[1].split()[0])
    
    def _on_start_game(self):
        """Start a new game."""
        # Start engine if not already running
        if not self.engine.is_running():
            if not self.engine.start():
                QMessageBox.critical(self, "Engine Error", 
                                   "Failed to start chess engine. Make sure Stockfish is installed.")
                return
        
        # Get settings
        self.engine_elo = self.elo_slider.value()
        self.engine.set_elo_strength(self.engine_elo)
        
        # Get time control
        if self.time_control_combo.currentText() == "Custom":
            self.time_control_minutes = self.custom_minutes_spin.value()
            self.increment_seconds = self.custom_increment_spin.value()
        
        # Get color
        color_text = self.color_combo.currentText()
        if color_text == "Random":
            self.user_color = random.choice([chess.WHITE, chess.BLACK])
        else:
            self.user_color = chess.WHITE if color_text == "White" else chess.BLACK
        
        # Get options
        self.takebacks_enabled = self.takebacks_check.isChecked()
        self.hints_enabled = self.hints_check.isChecked()
        self.auto_save = self.autosave_check.isChecked()
        
        # Reset game state
        self.board = chess.Board()
        self.game_active = True
        
        # Setup clocks
        time_seconds = self.time_control_minutes * 60
        self.game_clock = DualGameClock(time_seconds, self.increment_seconds)
        self.game_clock.white_time_updated.connect(self._on_white_time_updated)
        self.game_clock.black_time_updated.connect(self._on_black_time_updated)
        self.game_clock.white_time_expired.connect(lambda: self._on_time_expired(chess.WHITE))
        self.game_clock.black_time_expired.connect(lambda: self._on_time_expired(chess.BLACK))
        
        # Update UI
        self.board_widget.set_board(self.board)
        self.board_widget.set_flipped(self.user_color == chess.BLACK)
        self.move_list.clear()
        
        # Update labels
        user_name = "You (White)" if self.user_color == chess.WHITE else "You (Black)"
        engine_name = f"Stockfish ({self.engine_elo})"
        
        if self.user_color == chess.WHITE:
            self.white_name_label.setText(user_name)
            self.black_name_label.setText(engine_name)
        else:
            self.white_name_label.setText(engine_name)
            self.black_name_label.setText(user_name)
        
        # Enable/disable controls
        self.start_button.setText("New Game")
        self.hint_button.setEnabled(self.hints_enabled and self.user_color == self.board.turn)
        self.takeback_button.setEnabled(self.takebacks_enabled and len(self.board.move_stack) > 0)
        self.resign_button.setEnabled(True)
        
        # Start clock
        self.game_clock.switch_turn(self.board.turn == chess.WHITE)
        
        # If engine plays first, make engine move
        if self.user_color != self.board.turn:
            self.status_label.setText("Engine is thinking...")
            self._make_engine_move()
        else:
            self.status_label.setText("Your turn")
    
    def _on_square_clicked(self, square: int):
        """Handle board square clicks."""
        if not self.game_active or self.board.turn != self.user_color:
            return
        
        # Simple click-to-move implementation
        if not hasattr(self, "_selected_square"):
            # First click - select piece
            piece = self.board.piece_at(square)
            if piece and piece.color == self.user_color:
                self._selected_square = square
                self.board_widget.highlight_squares([square])
        else:
            # Second click - try to make move
            from_square = self._selected_square
            to_square = square
            
            delattr(self, "_selected_square")
            self.board_widget.highlight_squares([])
            
            # Try to make the move
            self._try_make_user_move(from_square, to_square)
    
    def _try_make_user_move(self, from_square: int, to_square: int):
        """Attempt to make a user move."""
        try:
            # Check for promotion
            move = chess.Move(from_square, to_square)
            piece = self.board.piece_at(from_square)
            
            if piece and piece.piece_type == chess.PAWN:
                if (chess.square_rank(to_square) == 7 and piece.color == chess.WHITE) or \
                   (chess.square_rank(to_square) == 0 and piece.color == chess.BLACK):
                    move = chess.Move(from_square, to_square, promotion=chess.QUEEN)
            
            # Validate move
            if move in self.board.legal_moves:
                self._make_move(move)
            else:
                self.status_label.setText("Illegal move. Try again.")
        
        except ValueError:
            self.status_label.setText("Invalid move.")
    
    def _make_move(self, move: chess.Move):
        """Make a move on the board."""
        # Push move
        self.board.push(move)
        
        # Update UI
        self.board_widget.set_board(self.board)
        self.move_list.add_move(self.board.san(move), self.board.turn != chess.WHITE)
        
        # Switch clock
        if self.game_clock:
            self.game_clock.switch_turn(self.board.turn == chess.WHITE)
        
        # Update controls
        self.takeback_button.setEnabled(self.takebacks_enabled and len(self.board.move_stack) > 0)
        
        # Check game end
        if self.board.is_game_over():
            self._end_game()
            return
        
        # If it's now engine's turn, make engine move
        if self.board.turn != self.user_color:
            self.status_label.setText("Engine is thinking...")
            self.hint_button.setEnabled(False)
            self._make_engine_move()
        else:
            self.status_label.setText("Your turn")
            self.hint_button.setEnabled(self.hints_enabled)
    
    def _make_engine_move(self):
        """Make engine move in background thread."""
        if self.engine_thread is not None and self.engine_thread.isRunning():
            return
        
        self.engine_thread = EngineThread(self.engine, self.board)
        self.engine_thread.move_calculated.connect(self._on_engine_move_ready)
        self.engine_thread.start()
    
    def _on_engine_move_ready(self, move: chess.Move):
        """Handle engine move calculation complete."""
        if not self.game_active or move is None:
            return
        
        self._make_move(move)
    
    def _on_request_hint(self):
        """Show hint to user."""
        if not self.game_active or self.board.turn != self.user_color:
            return
        
        top_moves = self.engine.get_top_moves(self.board, n=1, time_limit=1.0)
        if top_moves:
            best_move, eval_cp = top_moves[0]
            san = self.board.san(best_move)
            
            # Show hint as arrow
            self.board_widget.clear_arrows()
            self.board_widget.add_arrow(best_move.from_square, best_move.to_square, "green")
            
            self.status_label.setText(f"Hint: {san} (eval: {eval_cp/100:.1f})")
        else:
            self.status_label.setText("Could not calculate hint")
    
    def _on_takeback(self):
        """Take back the last move."""
        if not self.game_active or len(self.board.move_stack) == 0:
            return
        
        # Take back last 2 moves (user + engine) if possible
        moves_to_undo = 2 if len(self.board.move_stack) >= 2 else 1
        
        for _ in range(moves_to_undo):
            if self.board.move_stack:
                self.board.pop()
        
        # Update UI
        self.board_widget.set_board(self.board)
        self.move_list.remove_last_moves(moves_to_undo)
        
        # Reset clock to previous state (simplified - just pause)
        if self.game_clock:
            self.game_clock.pause_both()
            if self.board.turn == chess.WHITE:
                self.game_clock.start_white()
            else:
                self.game_clock.start_black()
        
        self.status_label.setText("Move taken back. Your turn.")
        self.takeback_button.setEnabled(len(self.board.move_stack) > 0)
        self.hint_button.setEnabled(self.hints_enabled and self.board.turn == self.user_color)
    
    def _on_resign(self):
        """Resign the game."""
        reply = QMessageBox.question(self, "Resign", "Are you sure you want to resign?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._end_game(resignation=True)
    
    def _on_time_expired(self, color: chess.Color):
        """Handle time expiry."""
        if not self.game_active:
            return
        
        color_name = "White" if color == chess.WHITE else "Black"
        self.status_label.setText(f"{color_name} ran out of time!")
        self._end_game(timeout=color)
    
    def _end_game(self, resignation: bool = False, timeout: Optional[chess.Color] = None):
        """End the game and show result."""
        if not self.game_active:
            return
        
        self.game_active = False
        
        # Stop clocks
        if self.game_clock:
            self.game_clock.stop_both()
        
        # Determine result
        if resignation:
            result = "0-1" if self.user_color == chess.WHITE else "1-0"
            termination = "Resignation"
        elif timeout is not None:
            result = "0-1" if timeout == chess.WHITE else "1-0"
            termination = "Time forfeit"
        elif self.board.is_checkmate():
            result = "0-1" if self.board.turn == chess.WHITE else "1-0"
            termination = "Checkmate"
        elif self.board.is_stalemate():
            result = "1/2-1/2"
            termination = "Stalemate"
        elif self.board.is_insufficient_material():
            result = "1/2-1/2"
            termination = "Insufficient material"
        elif self.board.can_claim_threefold_repetition():
            result = "1/2-1/2"
            termination = "Threefold repetition"
        elif self.board.can_claim_fifty_moves():
            result = "1/2-1/2"
            termination = "50-move rule"
        else:
            result = "*"
            termination = "Unknown"
        
        # Show result
        self.status_label.setText(f"Game Over: {result} ({termination})")
        
        # Disable controls
        self.hint_button.setEnabled(False)
        self.takeback_button.setEnabled(False)
        self.resign_button.setEnabled(False)
        
        # Save game if enabled
        if self.auto_save:
            self._save_game(result, termination)
        
        # Show result dialog
        QMessageBox.information(self, "Game Over", f"Result: {result}\n{termination}")
        
        self.game_completed.emit()
    
    def _save_game(self, result: str, termination: str):
        """Save completed game to database."""
        session = self.db.get_session()
        try:
            # Create PGN
            game = chess.pgn.Game()
            game.headers["Event"] = "Engine Game"
            game.headers["Site"] = "DCO"
            game.headers["Date"] = datetime.utcnow().strftime("%Y.%m.%d")
            game.headers["White"] = "You" if self.user_color == chess.WHITE else f"Stockfish ({self.engine_elo})"
            game.headers["Black"] = f"Stockfish ({self.engine_elo})" if self.user_color == chess.WHITE else "You"
            game.headers["Result"] = result
            game.headers["TimeControl"] = f"{self.time_control_minutes * 60}+{self.increment_seconds}"
            game.headers["Termination"] = termination
            
            # Add moves
            node = game
            for move in self.board.move_stack:
                node = node.add_variation(move)
            
            # Save to database
            pgn_text = str(game)
            
            db_game = Game(
                source="engine_game",
                event="Engine Game",
                site="DCO",
                date=datetime.utcnow().strftime("%Y.%m.%d"),
                white="You" if self.user_color == chess.WHITE else f"Stockfish ({self.engine_elo})",
                black=f"Stockfish ({self.engine_elo})" if self.user_color == chess.WHITE else "You",
                result=result,
                white_elo=None if self.user_color == chess.WHITE else self.engine_elo,
                black_elo=self.engine_elo if self.user_color == chess.WHITE else None,
                time_control=f"{self.time_control_minutes}+{self.increment_seconds}",
                termination=termination,
                pgn_text=pgn_text,
                created_at=datetime.utcnow()
            )
            
            session.add(db_game)
            session.commit()
            
            self.status_label.setText(f"Game saved! {result} ({termination})")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save game: {e}")
        finally:
            session.close()
    
    def _on_move_selected(self, index: int):
        """Handle move selection from move list."""
        # TODO: Implement move navigation
        pass
    
    def _on_white_time_updated(self, seconds: float):
        """Update white clock display."""
        if self.game_clock:
            self.white_time_label.setText(self.game_clock.get_white_formatted())
    
    def _on_black_time_updated(self, seconds: float):
        """Update black clock display."""
        if self.game_clock:
            self.black_time_label.setText(self.game_clock.get_black_formatted())
    
    def closeEvent(self, event):
        """Clean up when screen is closed."""
        if self.game_clock:
            self.game_clock.stop_both()
        
        if self.engine_thread is not None and self.engine_thread.isRunning():
            self.engine_thread.wait()
        
        self.engine.quit()
        event.accept()
