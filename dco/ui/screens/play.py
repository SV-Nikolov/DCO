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
    QFrame, QSlider, QComboBox, QCheckBox, QSpinBox, QMessageBox,
    QStackedWidget, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QThread

import chess
import chess.pgn

from ..widgets.chessboard import ChessboardWidget
from ..widgets.move_list import MoveListWidget
from ...data.db import Database
from ...data.models import Game, GameSource
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


class GameBoardView(QWidget):
    """The actual game board and controls during play."""
    
    game_ended = Signal()
    back_to_menu = Signal()
    
    def __init__(self, db: Database, engine: EngineController, parent=None):
        super().__init__(parent)
        self.db = db
        self.engine = engine
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
        """Initialize the game board UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)
        
        # Left: Move list and controls
        left_panel = self._create_left_panel()
        layout.addWidget(left_panel)
        
        # Center: Board and clocks
        center_area = self._create_center_area()
        layout.addWidget(center_area, 1)
        
        # Right: Game controls
        right_panel = self._create_right_panel()
        layout.addWidget(right_panel)
    
    def _create_left_panel(self) -> QWidget:
        """Create left panel with move list."""
        panel = QFrame()
        panel.setObjectName("cardFrame")
        panel.setFixedWidth(250)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Game Moves")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        self.move_list = MoveListWidget()
        layout.addWidget(self.move_list, 1)
        
        return panel
    
    def _create_center_area(self) -> QWidget:
        """Create center area with board and clocks."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Black clock (top)
        black_clock_frame = QFrame()
        black_clock_frame.setObjectName("cardFrame")
        black_clock_layout = QHBoxLayout(black_clock_frame)
        black_clock_layout.setContentsMargins(15, 10, 15, 10)
        
        self.black_name_label = QLabel("Stockfish (2000)")
        self.black_time_label = QLabel("5:00")
        self.black_time_label.setObjectName("statValue")
        self.black_time_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        
        black_clock_layout.addWidget(self.black_name_label)
        black_clock_layout.addStretch()
        black_clock_layout.addWidget(self.black_time_label)
        
        layout.addWidget(black_clock_frame)
        
        # Board
        self.board_widget = ChessboardWidget(size=600)
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
        self.white_time_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        
        white_clock_layout.addWidget(self.white_name_label)
        white_clock_layout.addStretch()
        white_clock_layout.addWidget(self.white_time_label)
        
        layout.addWidget(white_clock_frame)
        
        # Status label
        self.status_label = QLabel("Your turn")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; padding: 10px;")
        layout.addWidget(self.status_label)
        
        return widget
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel with game controls."""
        panel = QFrame()
        panel.setObjectName("cardFrame")
        panel.setFixedWidth(250)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Game Controls")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Hint button
        self.hint_button = QPushButton("💡 Request Hint")
        self.hint_button.setObjectName("secondaryButton")
        self.hint_button.setMinimumHeight(50)
        self.hint_button.clicked.connect(self._on_request_hint)
        layout.addWidget(self.hint_button)
        
        # Takeback button
        self.takeback_button = QPushButton("↶ Take Back Move")
        self.takeback_button.setObjectName("secondaryButton")
        self.takeback_button.setMinimumHeight(50)
        self.takeback_button.clicked.connect(self._on_takeback)
        layout.addWidget(self.takeback_button)
        
        layout.addStretch()
        
        # Resign button
        self.resign_button = QPushButton("🏳️ Resign Game")
        self.resign_button.setObjectName("dangerButton")
        self.resign_button.setMinimumHeight(50)
        self.resign_button.clicked.connect(self._on_resign)
        layout.addWidget(self.resign_button)
        
        # Back to menu
        self.menu_button = QPushButton("← Back to Menu")
        self.menu_button.setObjectName("secondaryButton")
        self.menu_button.setMinimumHeight(50)
        self.menu_button.clicked.connect(self._on_back_to_menu)
        layout.addWidget(self.menu_button)
        
        return panel
    
    def start_game(self, engine_elo: int, time_minutes: int, increment: int, 
                   user_color: chess.Color, takebacks: bool, hints: bool, auto_save: bool):
        """Start a new game with the given settings."""
        self.engine_elo = engine_elo
        self.time_control_minutes = time_minutes
        self.increment_seconds = increment
        self.user_color = user_color
        self.takebacks_enabled = takebacks
        self.hints_enabled = hints
        self.auto_save = auto_save
        
        # Configure engine
        self.engine.set_elo_strength(self.engine_elo)
        
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
        self.hint_button.setEnabled(self.hints_enabled and self.user_color == self.board.turn)
        self.takeback_button.setEnabled(False)
        self.resign_button.setEnabled(True)
        
        # Start clock
        self.game_clock.switch_turn(self.board.turn == chess.WHITE)
        
        # If engine plays first, make engine move
        if self.user_color != self.board.turn:
            self.status_label.setText("🤔 Engine is thinking...")
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
                self.status_label.setText("❌ Illegal move. Try again.")
        
        except ValueError:
            self.status_label.setText("❌ Invalid move.")
    
    def _make_move(self, move: chess.Move):
        """Make a move on the board."""
        # Push move
        san_move = self.board.san(move)
        self.board.push(move)
        
        # Update UI
        self.board_widget.set_board(self.board)
        self.board_widget.clear_arrows()
        self.move_list.add_move(san_move, self.board.turn != chess.WHITE)
        
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
            self.status_label.setText("🤔 Engine is thinking...")
            self.hint_button.setEnabled(False)
            self._make_engine_move()
        else:
            self.status_label.setText("✅ Your turn")
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
        
        self.status_label.setText("💡 Calculating hint...")
        top_moves = self.engine.get_top_moves(self.board, n=1, time_limit=1.0)
        if top_moves:
            best_move, eval_cp = top_moves[0]
            san = self.board.san(best_move)
            
            # Show hint as arrow
            self.board_widget.clear_arrows()
            self.board_widget.add_arrow(best_move.from_square, best_move.to_square, "green")
            
            self.status_label.setText(f"💡 Hint: {san} (eval: {eval_cp/100:.1f})")
        else:
            self.status_label.setText("❌ Could not calculate hint")
    
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
        self.board_widget.clear_arrows()
        self.move_list.remove_last_moves(moves_to_undo)
        
        # Reset clock to previous state (simplified - just pause)
        if self.game_clock:
            self.game_clock.pause_both()
            if self.board.turn == chess.WHITE:
                self.game_clock.start_white()
            else:
                self.game_clock.start_black()
        
        self.status_label.setText("↶ Move taken back. Your turn.")
        self.takeback_button.setEnabled(len(self.board.move_stack) > 0)
        self.hint_button.setEnabled(self.hints_enabled and self.board.turn == self.user_color)
    
    def _on_resign(self):
        """Resign the game."""
        reply = QMessageBox.question(self, "Resign", "Are you sure you want to resign?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._end_game(resignation=True)
    
    def _on_back_to_menu(self):
        """Return to setup menu."""
        if self.game_active:
            reply = QMessageBox.question(self, "Leave Game", 
                                       "Game is in progress. Return to menu?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
            
            # Stop game
            if self.game_clock:
                self.game_clock.stop_both()
            self.game_active = False
        
        self.back_to_menu.emit()
    
    def _on_time_expired(self, color: chess.Color):
        """Handle time expiry."""
        if not self.game_active:
            return
        
        color_name = "White" if color == chess.WHITE else "Black"
        self.status_label.setText(f"⏰ {color_name} ran out of time!")
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
        self.status_label.setText(f"🏁 Game Over: {result} ({termination})")
        
        # Disable controls
        self.hint_button.setEnabled(False)
        self.takeback_button.setEnabled(False)
        self.resign_button.setEnabled(False)
        
        # Save game if enabled
        if self.auto_save:
            self._save_game(result, termination)
        
        # Show result dialog
        msg = QMessageBox(self)
        msg.setWindowTitle("Game Over")
        msg.setText(f"Result: {result}")
        msg.setInformativeText(termination)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
        
        self.game_ended.emit()
    
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
                source=GameSource.ENGINE_PLAY,
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
            
            logger.info(f"Game saved: {result} ({termination})")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save game: {e}")
        finally:
            session.close()
    
    def _on_white_time_updated(self, seconds: float):
        """Update white clock display."""
        if self.game_clock:
            self.white_time_label.setText(self.game_clock.get_white_formatted())
    
    def _on_black_time_updated(self, seconds: float):
        """Update black clock display."""
        if self.game_clock:
            self.black_time_label.setText(self.game_clock.get_black_formatted())


class SetupMenuView(QWidget):
    """Setup menu for configuring game before starting."""
    
    start_game = Signal(int, int, int, bool, bool, bool, bool)  # elo, time, increment, color, takebacks, hints, auto_save
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the setup menu UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create scroll area to prevent squashing
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content widget
        content_container = QWidget()
        container_layout = QHBoxLayout(content_container)
        container_layout.setContentsMargins(20, 40, 20, 40)
        
        # Center everything
        content = QWidget()
        content.setMinimumWidth(500)
        content.setMaximumWidth(700)
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        
        # Title
        title = QLabel("Play vs Computer")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; margin-bottom: 20px;")
        content_layout.addWidget(title)
        
        subtitle = QLabel("Configure your game settings")
        subtitle.setObjectName("mutedText")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; margin-bottom: 30px;")
        content_layout.addWidget(subtitle)
        
        # Settings card
        settings_card = QFrame()
        settings_card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(settings_card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(25)
        
        # Opponent Strength
        strength_section = QFrame()
        strength_layout = QVBoxLayout(strength_section)
        strength_layout.setSpacing(10)
        
        strength_label = QLabel("🎯 Opponent Strength")
        strength_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        strength_layout.addWidget(strength_label)
        
        self.elo_slider = QSlider(Qt.Horizontal)
        self.elo_slider.setMinimum(1000)
        self.elo_slider.setMaximum(3200)
        self.elo_slider.setValue(2000)
        self.elo_slider.setTickPosition(QSlider.TicksBelow)
        self.elo_slider.setTickInterval(200)
        self.elo_slider.valueChanged.connect(self._on_elo_changed)
        strength_layout.addWidget(self.elo_slider)
        
        self.elo_label = QLabel("2000 Elo (Intermediate)")
        self.elo_label.setAlignment(Qt.AlignCenter)
        self.elo_label.setStyleSheet("font-size: 18px; color: #3b82f6; font-weight: bold;")
        strength_layout.addWidget(self.elo_label)
        
        card_layout.addWidget(strength_section)
        
        # Divider
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.HLine)
        divider1.setFrameShadow(QFrame.Sunken)
        divider1.setMinimumHeight(2)
        divider1.setStyleSheet("background-color: #e2e8f0; margin: 10px 0px;")
        card_layout.addWidget(divider1)
        
        # Time Control
        time_section = QFrame()
        time_layout = QVBoxLayout(time_section)
        time_layout.setSpacing(10)
        
        time_label = QLabel("⏱️ Time Control")
        time_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        time_layout.addWidget(time_label)
        
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
            "15+10 (Rapid)",
            "Custom"
        ])
        self.time_control_combo.setCurrentText("5+3 (Blitz)")
        self.time_control_combo.setStyleSheet("font-size: 14px; padding: 8px;")
        self.time_control_combo.currentTextChanged.connect(self._on_time_control_changed)
        time_layout.addWidget(self.time_control_combo)
        
        # Custom time controls (hidden by default)
        self.custom_time_frame = QFrame()
        custom_layout = QHBoxLayout(self.custom_time_frame)
        custom_layout.setContentsMargins(0, 10, 0, 0)
        custom_layout.setSpacing(15)
        
        minutes_group = QFrame()
        minutes_layout = QVBoxLayout(minutes_group)
        minutes_layout.setSpacing(5)
        minutes_layout.addWidget(QLabel("Minutes:"))
        self.custom_minutes_spin = QSpinBox()
        self.custom_minutes_spin.setMinimum(1)
        self.custom_minutes_spin.setMaximum(60)
        self.custom_minutes_spin.setValue(5)
        self.custom_minutes_spin.setStyleSheet("font-size: 14px;")
        minutes_layout.addWidget(self.custom_minutes_spin)
        custom_layout.addWidget(minutes_group)
        
        increment_group = QFrame()
        increment_layout = QVBoxLayout(increment_group)
        increment_layout.setSpacing(5)
        increment_layout.addWidget(QLabel("Increment (sec):"))
        self.custom_increment_spin = QSpinBox()
        self.custom_increment_spin.setMinimum(0)
        self.custom_increment_spin.setMaximum(30)
        self.custom_increment_spin.setValue(3)
        self.custom_increment_spin.setStyleSheet("font-size: 14px;")
        increment_layout.addWidget(self.custom_increment_spin)
        custom_layout.addWidget(increment_group)
        
        self.custom_time_frame.setVisible(False)
        time_layout.addWidget(self.custom_time_frame)
        
        card_layout.addWidget(time_section)
        
        # Divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setFrameShadow(QFrame.Sunken)
        divider2.setMinimumHeight(2)
        divider2.setStyleSheet("background-color: #e2e8f0; margin: 10px 0px;")
        card_layout.addWidget(divider2)
        
        # Color selection
        color_section = QFrame()
        color_layout = QVBoxLayout(color_section)
        color_layout.setSpacing(10)
        
        color_label = QLabel("♟️ Play As")
        color_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        color_layout.addWidget(color_label)
        
        self.color_combo = QComboBox()
        self.color_combo.addItems(["White", "Black", "Random"])
        self.color_combo.setStyleSheet("font-size: 14px; padding: 8px;")
        color_layout.addWidget(self.color_combo)
        
        card_layout.addWidget(color_section)
        
        # Divider
        divider3 = QFrame()
        divider3.setFrameShape(QFrame.HLine)
        divider3.setFrameShadow(QFrame.Sunken)
        divider3.setMinimumHeight(2)
        divider3.setStyleSheet("background-color: #e2e8f0; margin: 10px 0px;")
        card_layout.addWidget(divider3)
        
        # Options
        options_section = QFrame()
        options_layout = QVBoxLayout(options_section)
        options_layout.setSpacing(10)
        
        options_label = QLabel("⚙️ Game Options")
        options_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        options_layout.addWidget(options_label)
        
        self.takebacks_check = QCheckBox("Allow taking back moves")
        self.takebacks_check.setChecked(True)
        self.takebacks_check.setStyleSheet("font-size: 14px;")
        options_layout.addWidget(self.takebacks_check)
        
        self.hints_check = QCheckBox("Enable hint system")
        self.hints_check.setChecked(True)
        self.hints_check.setStyleSheet("font-size: 14px;")
        options_layout.addWidget(self.hints_check)
        
        self.autosave_check = QCheckBox("Auto-save completed games")
        self.autosave_check.setChecked(True)
        self.autosave_check.setStyleSheet("font-size: 14px;")
        options_layout.addWidget(self.autosave_check)
        
        card_layout.addWidget(options_section)
        
        content_layout.addWidget(settings_card)
        
        # Start button
        self.start_button = QPushButton("🎮 Start Game")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setMinimumHeight(60)
        self.start_button.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.start_button.clicked.connect(self._on_start_clicked)
        content_layout.addWidget(self.start_button)
        
        # Center the content horizontally
        container_layout.addStretch()
        container_layout.addWidget(content)
        container_layout.addStretch()
        
        scroll.setWidget(content_container)
        layout.addWidget(scroll)
    
    def _on_elo_changed(self, value: int):
        """Handle Elo slider change."""
        if value < 1200:
            level = "Beginner"
        elif value < 1600:
            level = "Novice"
        elif value < 2000:
            level = "Intermediate"
        elif value < 2400:
            level = "Advanced"
        elif value < 2800:
            level = "Expert"
        else:
            level = "Master"
        
        self.elo_label.setText(f"{value} Elo ({level})")
    
    def _on_time_control_changed(self, text: str):
        """Handle time control selection change."""
        is_custom = text == "Custom"
        self.custom_time_frame.setVisible(is_custom)
    
    def _on_start_clicked(self):
        """Start game with configured settings."""
        # Get settings
        elo = self.elo_slider.value()
        
        # Get time control
        if self.time_control_combo.currentText() == "Custom":
            time_minutes = self.custom_minutes_spin.value()
            increment = self.custom_increment_spin.value()
        else:
            parts = self.time_control_combo.currentText().split("+")
            time_minutes = int(parts[0])
            increment = int(parts[1].split()[0])
        
        # Get color
        color_text = self.color_combo.currentText()
        if color_text == "Random":
            user_is_white = random.choice([True, False])
        else:
            user_is_white = color_text == "White"
        
        # Get options
        takebacks = self.takebacks_check.isChecked()
        hints = self.hints_check.isChecked()
        auto_save = self.autosave_check.isChecked()
        
        # Emit signal with all settings
        self.start_game.emit(elo, time_minutes, increment, user_is_white, 
                           takebacks, hints, auto_save)


class PlayScreen(QWidget):
    """Main play screen that manages setup menu and game board."""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        
        # Initialize engine
        self.engine = EngineController()
        if not self.engine.start():
            QMessageBox.critical(self, "Engine Error", 
                               "Failed to start chess engine.\n\n"
                               "Please ensure Stockfish is installed correctly.\n"
                               f"Looking for: {self.engine.stockfish_path}")
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI with stacked widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # Setup menu
        self.setup_view = SetupMenuView()
        self.setup_view.start_game.connect(self._on_start_game)
        self.stack.addWidget(self.setup_view)
        
        # Game board
        self.game_view = GameBoardView(self.db, self.engine)
        self.game_view.game_ended.connect(self._on_game_ended)
        self.game_view.back_to_menu.connect(self._show_setup_menu)
        self.stack.addWidget(self.game_view)
        
        layout.addWidget(self.stack)
        
        # Start with setup menu
        self.stack.setCurrentWidget(self.setup_view)
    
    def _on_start_game(self, elo: int, time_minutes: int, increment: int, 
                       user_is_white: bool, takebacks: bool, hints: bool, auto_save: bool):
        """Handle game start from setup menu."""
        user_color = chess.WHITE if user_is_white else chess.BLACK
        self.game_view.start_game(elo, time_minutes, increment, user_color, 
                                 takebacks, hints, auto_save)
        self.stack.setCurrentWidget(self.game_view)
    
    def _on_game_ended(self):
        """Handle game end - stay on board to review."""
        pass
    
    def _show_setup_menu(self):
        """Show the setup menu."""
        self.stack.setCurrentWidget(self.setup_view)
    
    def closeEvent(self, event):
        """Clean up when screen is closed."""
        if hasattr(self.game_view, 'game_clock') and self.game_view.game_clock:
            self.game_view.game_clock.stop_both()
        
        if hasattr(self.game_view, 'engine_thread') and self.game_view.engine_thread is not None:
            if self.game_view.engine_thread.isRunning():
                self.game_view.engine_thread.wait()
        
        self.engine.quit()
        event.accept()
