"""
Library screen for viewing imported games.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional
import time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QLineEdit,
    QHeaderView, QComboBox, QMessageBox, QFrame, QProgressBar,
    QDateEdit, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThread, Slot, QDate
from sqlalchemy import or_, desc

from ...data.db import Database
from ...data.models import Game, Analysis
from ...core.engine import ChessEngine, EngineConfig
from ...core.analysis import GameAnalyzer, save_analysis_to_db
from ...core.practice import generate_practice_items


class BatchAnalysisWorker(QThread):
    """Background worker for batch analysis."""

    progress = Signal(int, int, int)
    finished = Signal(int, list)

    def __init__(self, db: Database, game_ids: List[int], depth: int):
        super().__init__()
        self.db = db
        self.game_ids = game_ids
        self.depth = depth

    def run(self):
        """Analyze games sequentially in a background thread."""
        analyzed_count = 0
        errors: List[str] = []
        total = len(self.game_ids)

        if total == 0:
            self.finished.emit(0, ["No games to analyze."])
            return

        engine = None

        try:
            # Get Stockfish path from settings
            from ...core.settings import get_settings
            settings = get_settings()
            
            config = EngineConfig(
                path=settings.get_engine_path(),
                depth=self.depth,
                time_per_move=0.5
            )
            engine = ChessEngine(config)
            engine.start()
            analyzer = GameAnalyzer(engine)

            for idx, game_id in enumerate(self.game_ids, start=1):
                # Create a fresh session for this game to avoid threading issues
                session = self.db.get_session()
                
                try:
                    game = session.query(Game).filter(Game.id == game_id).first()
                    if not game:
                        errors.append(f"Game id {game_id} not found.")
                        self.progress.emit(idx, total, game_id)
                        continue

                    # Analyze the game
                    result = analyzer.analyze_game(game, depth=self.depth)
                    
                    # Save to database
                    save_analysis_to_db(session, game, result)
                    generate_practice_items(session, game, result, engine)
                    session.commit()
                    analyzed_count += 1
                    
                except Exception as exc:
                    session.rollback()
                    errors.append(f"Game {game_id}: {str(exc)}")
                finally:
                    session.close()
                    self.progress.emit(idx, total, game_id)

            self.finished.emit(analyzed_count, errors)
        except RuntimeError as stock_exc:
            # Handle Stockfish not found error specifically
            if "Stockfish" in str(stock_exc):
                stock_error = (
                    "Stockfish engine not found.\n\n"
                    "Batch analysis requires the Stockfish chess engine.\n\n"
                    "To fix this:\n"
                    "1. Download Stockfish: https://stockfishchess.org/download/\n"
                    "2. Extract/install it to your system\n"
                    "3. Go to Settings → Engine → Browse to specify the path\n\n"
                    "See docs/INSTALL_STOCKFISH.md for detailed instructions."
                )
                self.finished.emit(0, [stock_error])
            else:
                self.finished.emit(analyzed_count, errors + [str(stock_exc)])
        except Exception as outer_exc:
            self.finished.emit(analyzed_count, errors + [str(outer_exc)])
        finally:
            if engine:
                engine.stop()


class LibraryScreen(QWidget):
    """Screen for viewing the game library."""
    
    game_selected = Signal(int)  # Signal emitted with game ID
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.games = []
        self.analysis_status = {}
        self.batch_worker: Optional[BatchAnalysisWorker] = None
        self.batch_start_time: Optional[float] = None
        self.batch_game_details: dict = {}
        self.init_ui()
        self.refresh()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        header = QLabel("Game Library")
        header.setObjectName("screenTitle")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("primaryButton")
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)

        self.batch_progress = QProgressBar()
        self.batch_progress.setVisible(False)
        self.batch_progress.setTextVisible(False)
        # Styled by global stylesheet
        layout.addWidget(self.batch_progress)

        self.batch_status_label = QLabel("")
        self.batch_status_label.setObjectName("mutedText")
        self.batch_status_label.setVisible(False)
        layout.addWidget(self.batch_status_label)
        
        # Search and filter
        filter_layout = QHBoxLayout()
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by player names, event, or date...")
        self.search_box.setMinimumHeight(40)
        self.search_box.textChanged.connect(self._on_search)
        filter_layout.addWidget(self.search_box, 3)
        
        self.result_filter = QComboBox()
        self.result_filter.addItems(["All Results", "White Won", "Black Won", "Draw"])
        self.result_filter.setMinimumHeight(40)
        self.result_filter.currentTextChanged.connect(self._on_filter)
        filter_layout.addWidget(self.result_filter, 1)

        self.time_control_filter = QComboBox()
        self.time_control_filter.addItems(["All Time Controls"])
        self.time_control_filter.setMinimumHeight(40)
        self.time_control_filter.currentTextChanged.connect(self._on_filter)
        filter_layout.addWidget(self.time_control_filter, 1)
        
        layout.addLayout(filter_layout)

        # Batch analysis controls
        batch_frame = QFrame()
        batch_frame.setObjectName("cardFrame")
        batch_layout = QVBoxLayout(batch_frame)
        batch_layout.setContentsMargins(15, 15, 15, 15)
        batch_layout.setSpacing(10)

        batch_title = QLabel("Batch Analysis")
        batch_title.setObjectName("cardTitle")
        batch_layout.addWidget(batch_title)

        batch_controls = QHBoxLayout()

        self.batch_max_games = QSpinBox()
        self.batch_max_games.setRange(1, 5000)
        self.batch_max_games.setValue(20)
        self.batch_max_games.setPrefix("Max: ")
        batch_controls.addWidget(self.batch_max_games)

        self.batch_time_control = QComboBox()
        self.batch_time_control.addItems(["All Time Controls"])
        batch_controls.addWidget(self.batch_time_control)

        self.batch_result_filter = QComboBox()
        self.batch_result_filter.addItems(["All Results", "White Won", "Black Won", "Draw"])
        batch_controls.addWidget(self.batch_result_filter)

        self.batch_start_date = QDateEdit()
        self.batch_start_date.setCalendarPopup(True)
        self.batch_start_date.setDisplayFormat("yyyy-MM-dd")
        batch_controls.addWidget(self.batch_start_date)

        self.batch_end_date = QDateEdit()
        self.batch_end_date.setCalendarPopup(True)
        self.batch_end_date.setDisplayFormat("yyyy-MM-dd")
        batch_controls.addWidget(self.batch_end_date)

        self.batch_depth = QSpinBox()
        self.batch_depth.setRange(8, 30)
        self.batch_depth.setValue(20)
        self.batch_depth.setPrefix("Depth: ")
        batch_controls.addWidget(self.batch_depth)

        self.batch_include_analyzed = QCheckBox("Reanalyze already analyzed games")
        self.batch_include_analyzed.setChecked(False)
        batch_controls.addWidget(self.batch_include_analyzed)

        self.batch_analyze_btn = QPushButton("Analyze Filtered")
        self.batch_analyze_btn.setObjectName("primaryButton")
        self.batch_analyze_btn.setMinimumHeight(36)
        self.batch_analyze_btn.clicked.connect(self._on_batch_analyze)
        batch_controls.addWidget(self.batch_analyze_btn)

        batch_controls.addStretch()
        batch_layout.addLayout(batch_controls)

        layout.addWidget(batch_frame)
        
        # Games table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "", "Date", "White", "Black", "Result", "Time Control", "Event", "Site"
        ])
        
        # Configure table
        # Styled by global stylesheet
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # White
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Black
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Result
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Time Control
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # Event
        header.setSectionResizeMode(7, QHeaderView.Stretch)  # Site
        
        self.table.doubleClicked.connect(self._on_game_double_clicked)
        
        layout.addWidget(self.table, 1)
        
        # Status bar
        self.status_label = QLabel("No games in library")
        self.status_label.setObjectName("mutedText")
        layout.addWidget(self.status_label)

        today = datetime.utcnow().date()
        qtoday = QDate(today.year, today.month, today.day)
        self.batch_start_date.setDate(qtoday)
        self.batch_end_date.setDate(qtoday)
    
    def refresh(self):
        """Refresh the game list from database."""
        session = self.db.get_session()
        
        try:
            # Query all games with analysis status, sorted by game date (newest first)
            rows = session.query(Game, Analysis).outerjoin(
                Analysis, Game.id == Analysis.game_id
            ).order_by(desc(Game.date)).all()

            self.games = [game for game, _ in rows]
            self.analysis_status = {game.id: analysis is not None for game, analysis in rows}

            # Update time control filters
            time_controls = sorted({g.time_control for g in self.games if g.time_control})
            self._set_time_control_options(self.time_control_filter, time_controls)
            self._set_time_control_options(self.batch_time_control, time_controls)
            
            # Update table with active filters
            self._apply_filters()
            
            # Update status
            count = len(self.games)
            if count == 0:
                self.status_label.setText("No games in library")
            elif count == 1:
                self.status_label.setText("1 game")
            else:
                self.status_label.setText(f"{count} games")
        
        finally:
            session.close()
    
    def _update_table(self, games: list):
        """Update the table with the given games."""
        self.table.setRowCount(len(games))
        
        for row, game in enumerate(games):
            is_analyzed = self.analysis_status.get(game.id, False)

            status_item = QTableWidgetItem("✓" if is_analyzed else "?")
            status_item.setTextAlignment(Qt.AlignCenter)
            if is_analyzed:
                status_item.setForeground(Qt.darkGreen)
                status_item.setBackground(Qt.green)
            else:
                status_item.setForeground(Qt.darkYellow)
                status_item.setBackground(Qt.yellow)
            self.table.setItem(row, 0, status_item)

            # Date
            self.table.setItem(row, 1, QTableWidgetItem(game.date or ""))
            
            # White
            white_text = game.white or ""
            if game.white_elo:
                white_text += f" ({game.white_elo})"
            self.table.setItem(row, 2, QTableWidgetItem(white_text))
            
            # Black
            black_text = game.black or ""
            if game.black_elo:
                black_text += f" ({game.black_elo})"
            self.table.setItem(row, 3, QTableWidgetItem(black_text))
            
            # Result
            result_item = QTableWidgetItem(game.result or "*")
            result_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, result_item)
            
            # Time Control
            self.table.setItem(row, 5, QTableWidgetItem(game.time_control or ""))
            
            # Event
            self.table.setItem(row, 6, QTableWidgetItem(game.event or ""))
            
            # Site
            self.table.setItem(row, 7, QTableWidgetItem(game.site or ""))
            
            # Store game ID in row data
            self.table.item(row, 1).setData(Qt.UserRole, game.id)
    
    def _on_search(self, text: str):
        """Handle search text change."""
        self._apply_filters()
    
    def _on_filter(self, filter_text: str):
        """Handle result filter change."""
        self._apply_filters()
    
    def _on_game_double_clicked(self, index):
        """Handle game double-click."""
        row = index.row()
        game_id = self.table.item(row, 1).data(Qt.UserRole)
        
        if game_id:
            # Open the analysis screen
            self.game_selected.emit(game_id)

    def _apply_filters(self) -> None:
        """Apply search, result, and time control filters."""
        filtered = list(self.games)

        text = self.search_box.text().strip().lower()
        if text:
            filtered = [
                game for game in filtered
                if any(
                    text in (field or "").lower()
                    for field in [game.white, game.black, game.event, game.site, game.date]
                )
            ]

        result_text = self.result_filter.currentText()
        if result_text != "All Results":
            result_map = {
                "White Won": "1-0",
                "Black Won": "0-1",
                "Draw": "1/2-1/2"
            }
            result_value = result_map.get(result_text)
            if result_value:
                filtered = [g for g in filtered if g.result == result_value]

        time_control = self.time_control_filter.currentText()
        if time_control != "All Time Controls":
            filtered = [g for g in filtered if g.time_control == time_control]

        self._update_table(filtered)
        self.status_label.setText(
            f"Showing {len(filtered)} of {len(self.games)} games"
        )

    def _set_time_control_options(self, combo: QComboBox, values: List[str]) -> None:
        """Populate time control dropdown."""
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("All Time Controls")
        for value in values:
            combo.addItem(value)
        if current in values:
            combo.setCurrentText(current)
        combo.blockSignals(False)

    def _on_batch_analyze(self) -> None:
        """Start batch analysis based on current filters."""
        if self.batch_worker:
            return

        game_ids = self._get_batch_game_ids()
        if not game_ids:
            QMessageBox.information(self, "Batch Analysis", "No games match the selected filters.")
            return

        depth = self.batch_depth.value()

        # Create a map of game_id -> game details for progress display
        self.batch_game_details = {}
        for g in self.games:
            if g.id in game_ids:
                self.batch_game_details[g.id] = f"{g.white} vs {g.black}"

        self.batch_progress.setVisible(True)
        self.batch_progress.setRange(0, len(game_ids))
        self.batch_progress.setValue(0)
        self.batch_status_label.setVisible(True)
        self.batch_status_label.setText(f"Analyzing 0/{len(game_ids)} • Time: 0s")
        self.batch_analyze_btn.setEnabled(False)
        self.batch_start_time = time.time()

        self.batch_worker = BatchAnalysisWorker(self.db, game_ids, depth)
        self.batch_worker.progress.connect(self._on_batch_progress)
        self.batch_worker.finished.connect(self._on_batch_finished)
        self.batch_worker.start()

    @Slot(int, int, int)
    def _on_batch_progress(self, done: int, total: int, game_id: int) -> None:
        """Update batch analysis progress UI."""
        self.batch_progress.setValue(done)
        self._mark_game_analyzed(game_id)
        
        # Get game details for display
        game_detail = self.batch_game_details.get(game_id, f"Game {game_id}")
        
        elapsed = 0.0
        if self.batch_start_time is not None:
            elapsed = time.time() - self.batch_start_time
        
        self.batch_status_label.setText(
            f"Analyzing {game_detail} ({done}/{total}) • Time: {self._format_duration(elapsed)}"
        )

    @Slot(int, list)
    def _on_batch_finished(self, analyzed_count: int, errors: list) -> None:
        """Handle batch analysis completion."""
        self.batch_progress.setVisible(False)
        self.batch_analyze_btn.setEnabled(True)
        if self.batch_start_time is not None:
            elapsed = time.time() - self.batch_start_time
            self.batch_status_label.setText(
                f"Analyzed {analyzed_count}/{analyzed_count} • Time: {self._format_duration(elapsed)}"
            )
        self.batch_start_time = None

        if errors:
            message = f"Analyzed {analyzed_count} game(s) with {len(errors)} issue(s).\n\n"
            message += "\n".join(errors[:5])
            if len(errors) > 5:
                message += f"\n... and {len(errors) - 5} more"
            QMessageBox.warning(self, "Batch Analysis", message)
        else:
            QMessageBox.information(self, "Batch Analysis", f"Analyzed {analyzed_count} game(s).")

        self.batch_worker = None
        self.refresh()

    def _get_batch_game_ids(self) -> List[int]:
        """Collect game ids for batch analysis based on filters."""
        filtered = list(self.games)

        time_control = self.batch_time_control.currentText()
        if time_control != "All Time Controls":
            filtered = [g for g in filtered if g.time_control == time_control]

        result_text = self.batch_result_filter.currentText()
        if result_text != "All Results":
            result_map = {
                "White Won": "1-0",
                "Black Won": "0-1",
                "Draw": "1/2-1/2"
            }
            result_value = result_map.get(result_text)
            if result_value:
                filtered = [g for g in filtered if g.result == result_value]

        start_qdate = self.batch_start_date.date()
        end_qdate = self.batch_end_date.date()
        start = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
        end = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59)
        if start > end:
            start, end = end, start
        filtered = [g for g in filtered if g.created_at and start <= g.created_at <= end]

        if not self.batch_include_analyzed.isChecked():
            filtered = [g for g in filtered if not self.analysis_status.get(g.id, False)]

        max_games = self.batch_max_games.value()
        return [g.id for g in filtered[:max_games]]

    def _mark_game_analyzed(self, game_id: int) -> None:
        """Update analysis status in the table after a game finishes."""
        self.analysis_status[game_id] = True
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if not item:
                continue
            row_game_id = item.data(Qt.UserRole)
            if row_game_id == game_id:
                status_item = QTableWidgetItem("✓")
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setForeground(Qt.darkGreen)
                status_item.setBackground(Qt.green)
                self.table.setItem(row, 0, status_item)
                break

    def _format_duration(self, seconds: float) -> str:
        """Format seconds into a human-readable duration."""
        if seconds <= 0:
            return "0s"
        minutes, sec = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}h {minutes}m"
        if minutes:
            return f"{minutes}m {sec}s"
        return f"{sec}s"
