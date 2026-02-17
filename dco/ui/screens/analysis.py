"""
Analysis screen for viewing analyzed games with move-by-move evaluation.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread, Slot
import chess
import chess.pgn
import io

from ...data.db import Database
from ...data.models import Game, Analysis as AnalysisModel, Move
from ...core.engine import ChessEngine, EngineConfig
from ...core.analysis import GameAnalyzer, save_analysis_to_db
from ...core.practice import generate_practice_items
from ..widgets.chessboard import ChessboardWidget
from ..widgets.move_list import MoveListWidget


class AnalysisWorker(QThread):
    """Worker thread for analyzing games in the background."""
    
    progress = Signal(str)  # Progress message
    finished = Signal(bool, str)  # (success, message)
    
    def __init__(self, db: Database, game: Game):
        super().__init__()
        self.db = db
        self.game = game
    
    def run(self):
        """Run the analysis."""
        try:
            self.progress.emit("Initializing engine...")
            
            # Create engine
            config = EngineConfig(depth=20, time_per_move=0.5)
            engine = ChessEngine(config)
            engine.start()
            
            self.progress.emit(f"Analyzing game: {self.game.white} vs {self.game.black}")
            
            # Analyze game
            analyzer = GameAnalyzer(engine)
            result = analyzer.analyze_game(self.game)
            
            self.progress.emit("Saving analysis to database...")
            
            # Save to database
            session = self.db.get_session()
            try:
                save_analysis_to_db(session, self.game, result)
                generate_practice_items(
                    session=session,
                    game=self.game,
                    analysis_result=result,
                    engine=engine
                )
                session.commit()
            finally:
                session.close()
            
            # Clean up
            engine.stop()
            
            self.finished.emit(True, f"Analysis complete! Accuracy: White {result.accuracy_white:.1f}%, Black {result.accuracy_black:.1f}%")
            
        except Exception as e:
            error_msg = str(e)
            if "Stockfish not found" in error_msg or "Stockfish" in error_msg.lower():
                error_msg = (
                    "Stockfish engine not found.\n\n"
                    "To use the analysis feature:\n"
                    "1. Visit: https://stockfishchess.org/download/\n"
                    "2. Download Stockfish for your operating system\n"
                    "3. Extract/Install it to a convenient location\n"
                    "4. In Settings → Engine → Browse, select the stockfish executable\n\n"
                    "Or let DCO auto-detect from:\n"
                    "- Program Files/Stockfish/\n"
                    "- Your Downloads folder\n"
                    "- Your PATH environment variable\n\n"
                    "For more help, see INSTALL_STOCKFISH.md"
                )
            self.finished.emit(False, f"Analysis failed: {error_msg}")


class AnalysisScreen(QWidget):
    """Screen for viewing game analysis."""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_game = None
        self.current_analysis = None
        self.moves = []
        self.chess_game = None
        self.current_ply = 0
        self.analysis_worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Styled by global stylesheet
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Game Analysis")
        self.title_label.setObjectName("screenTitle")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.analyze_btn = QPushButton("Analyze Game")
        self.analyze_btn.setObjectName("primaryButton")
        self.analyze_btn.setMinimumHeight(35)
        self.analyze_btn.clicked.connect(self._on_analyze_clicked)
        self.analyze_btn.setVisible(False)
        header_layout.addWidget(self.analyze_btn)
        
        layout.addLayout(header_layout)
        
        # Game info
        self.game_info_label = QLabel("No game selected")
        self.game_info_label.setObjectName("mutedText")
        layout.addWidget(self.game_info_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        # Styled by global stylesheet
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("mutedText")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left side: Board and controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Chessboard
        self.board = ChessboardWidget(450, self)
        left_layout.addWidget(self.board, 0, Qt.AlignCenter)
        
        # Board controls
        controls_layout = QHBoxLayout()
        
        self.first_btn = QPushButton("⏮ First")
        self.first_btn.setObjectName("secondaryButton")
        self.first_btn.clicked.connect(self._go_to_first)
        controls_layout.addWidget(self.first_btn)
        
        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.setObjectName("secondaryButton")
        self.prev_btn.clicked.connect(self._go_to_prev)
        controls_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setObjectName("secondaryButton")
        self.next_btn.clicked.connect(self._go_to_next)
        controls_layout.addWidget(self.next_btn)
        
        self.last_btn = QPushButton("Last ⏭")
        self.last_btn.setObjectName("secondaryButton")
        self.last_btn.clicked.connect(self._go_to_last)
        controls_layout.addWidget(self.last_btn)
        
        left_layout.addLayout(controls_layout)
        
        # Move info
        self.move_info_label = QLabel("")
        self.move_info_label.setObjectName("cardFrame")
        self.move_info_label.setWordWrap(True)
        left_layout.addWidget(self.move_info_label)
        
        left_layout.addStretch()
        
        content_layout.addWidget(left_widget, 1)
        
        # Right side: Move list and stats
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        # Stats panel
        self.stats_frame = QFrame()
        self.stats_frame.setObjectName("cardFrame")
        stats_layout = QVBoxLayout(self.stats_frame)
        
        self.stats_label = QLabel("No analysis available")
        # Styled by global stylesheet
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        right_layout.addWidget(self.stats_frame)
        
        # Move list
        moves_label = QLabel("Moves")
        moves_label.setObjectName("cardTitle")
        right_layout.addWidget(moves_label)
        
        self.move_list = MoveListWidget(self)
        self.move_list.move_selected.connect(self._on_move_selected)
        right_layout.addWidget(self.move_list, 1)
        
        content_layout.addWidget(right_widget, 1)
        
        layout.addLayout(content_layout, 1)
        
        # Initial state
        self._update_controls()
    
    def load_game(self, game_id: int):
        """Load a game for analysis."""
        session = self.db.get_session()
        
        try:
            # Load game
            self.current_game = session.query(Game).filter_by(id=game_id).first()
            
            if not self.current_game:
                QMessageBox.warning(self, "Error", "Game not found")
                return
            
            # Load analysis if exists
            self.current_analysis = session.query(AnalysisModel).filter_by(
                game_id=game_id
            ).first()
            
            # Load moves if analyzed
            if self.current_analysis:
                self.moves = session.query(Move).filter_by(
                    game_id=game_id
                ).order_by(Move.ply_index).all()
            else:
                self.moves = []
            
            # Parse PGN
            pgn_io = io.StringIO(self.current_game.pgn_text)
            self.chess_game = chess.pgn.read_game(pgn_io)
            
            # Update UI
            self._update_game_info()
            self._update_stats()
            
            if self.moves:
                self.move_list.set_moves(self.moves)
                self._go_to_first()
            else:
                self.board.set_position(chess.STARTING_FEN)
                self.analyze_btn.setVisible(True)
            
        finally:
            session.close()
    
    def _update_game_info(self):
        """Update game information display."""
        if not self.current_game:
            return
        
        # Build info text with ECO opening if available
        info = f"{self.current_game.white} vs {self.current_game.black}"
        
        if self.current_game.eco_code or self.current_game.opening_name:
            opening_str = ""
            if self.current_game.eco_code:
                opening_str += self.current_game.eco_code
            if self.current_game.opening_name:
                if opening_str:
                    opening_str += ": "
                opening_str += self.current_game.opening_name
            if self.current_game.opening_variation:
                opening_str += f", {self.current_game.opening_variation}"
            info += f" • {opening_str}"
        
        if self.current_game.date:
            info += f" • {self.current_game.date}"
        if self.current_game.event:
            info += f" • {self.current_game.event}"
        
        self.game_info_label.setText(info)
        self.title_label.setText(f"Game Analysis: {self.current_game.white} vs {self.current_game.black}")
    
    def _update_stats(self):
        """Update statistics display."""
        if not self.current_analysis:
            self.stats_label.setText("Game not analyzed yet.\nClick 'Analyze Game' to start.")
            return
        
        # Build opening info if available
        opening_html = ""
        if self.current_game and (self.current_game.eco_code or self.current_game.opening_name):
            opening_html = "<b>Opening:</b><br/>"
            if self.current_game.eco_code:
                opening_html += f"{self.current_game.eco_code}"
            if self.current_game.opening_name:
                if self.current_game.eco_code:
                    opening_html += ": "
                opening_html += f"{self.current_game.opening_name}"
            if self.current_game.opening_variation:
                opening_html += f",<br/>{self.current_game.opening_variation}"
            opening_html += "<br/><br/>"
        
        stats_text = f"""
        {opening_html}
        <b>Accuracy:</b><br/>
        White: {self.current_analysis.accuracy_white:.1f}%<br/>
        Black: {self.current_analysis.accuracy_black:.1f}%<br/>
        <br/>
        <b>Performance Rating:</b><br/>
        White: {self.current_analysis.perf_elo_white}<br/>
        Black: {self.current_analysis.perf_elo_black}<br/>
        <br/>
        <b>Engine:</b> {self.current_analysis.engine_version}<br/>
        <b>Depth:</b> {self.current_analysis.depth}
        """
        
        self.stats_label.setText(stats_text)
    
    def _update_controls(self):
        """Update navigation button states."""
        has_moves = len(self.moves) > 0
        self.first_btn.setEnabled(has_moves and self.current_ply > 0)
        self.prev_btn.setEnabled(has_moves and self.current_ply > 0)
        self.next_btn.setEnabled(has_moves and self.current_ply < len(self.moves))
        self.last_btn.setEnabled(has_moves and self.current_ply < len(self.moves))
    
    def _go_to_first(self):
        """Go to starting position."""
        self.current_ply = 0
        self._show_position()
    
    def _go_to_prev(self):
        """Go to previous move."""
        if self.current_ply > 0:
            self.current_ply -= 1
            self._show_position()
    
    def _go_to_next(self):
        """Go to next move."""
        if self.current_ply < len(self.moves):
            self.current_ply += 1
            self._show_position()
    
    def _go_to_last(self):
        """Go to last move."""
        self.current_ply = len(self.moves)
        self._show_position()
    
    def _show_position(self):
        """Show the current position."""
        if self.current_ply == 0:
            # Starting position
            self.board.set_position(chess.STARTING_FEN)
            self.board.clear_arrows()
            self.move_info_label.setText("Starting position")
        elif self.current_ply <= len(self.moves):
            # Show position after move
            move = self.moves[self.current_ply - 1]
            self.board.set_position(move.fen_after)
            
            # Highlight last move
            try:
                chess_move = chess.Move.from_uci(move.uci)
                self.board.set_last_move(chess_move)
            except:
                pass
            
            # Show move info
            self._update_move_info(move)
            
            # Update move list selection
            self.move_list.select_move(move.ply_index)
        
        self._update_controls()
    
    def _update_move_info(self, move: Move):
        """Update move information display."""
        info = f"<b>Move {move.ply_index + 1}:</b> {move.san}<br/>"
        info += f"<b>Classification:</b> {move.classification.value.title()}<br/>"
        
        if move.eval_after_cp is not None:
            eval_pawns = move.eval_after_cp / 100.0
            info += f"<b>Evaluation:</b> {eval_pawns:+.2f}<br/>"
        
        if move.best_uci and move.best_uci != move.uci:
            info += f"<b>Best move:</b> {move.best_uci}<br/>"
        
        if move.comment:
            info += f"<br/>{move.comment}"
        
        self.move_info_label.setText(info)
    
    def _on_move_selected(self, ply_index: int):
        """Handle move selection from move list."""
        self.current_ply = ply_index + 1
        self._show_position()
    
    def _on_analyze_clicked(self):
        """Handle analyze button click."""
        if not self.current_game:
            return
        
        # Disable button and show progress
        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_label.setVisible(True)
        
        # Start analysis in background
        self.analysis_worker = AnalysisWorker(self.db, self.current_game)
        self.analysis_worker.progress.connect(self._on_analysis_progress)
        self.analysis_worker.finished.connect(self._on_analysis_finished)
        self.analysis_worker.start()
    
    @Slot(str)
    def _on_analysis_progress(self, message: str):
        """Handle analysis progress update."""
        self.progress_label.setText(message)
    
    @Slot(bool, str)
    def _on_analysis_finished(self, success: bool, message: str):
        """Handle analysis completion."""
        # Hide progress
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.analyze_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Analysis Complete", message)
            # Reload the game to show analysis
            if self.current_game:
                self.load_game(self.current_game.id)
        else:
            # Show detailed error message
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Analysis Failed")
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
