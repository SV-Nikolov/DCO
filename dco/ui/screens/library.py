"""
Library screen for viewing imported games.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QLineEdit,
    QHeaderView, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from sqlalchemy import or_, desc

from ...data.db import Database
from ...data.models import Game


class LibraryScreen(QWidget):
    """Screen for viewing the game library."""
    
    game_selected = Signal(int)  # Signal emitted with game ID
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.games = []
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
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #1f2937;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setMinimumHeight(35)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Search and filter
        filter_layout = QHBoxLayout()
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by player names, event, or date...")
        self.search_box.setMinimumHeight(35)
        self.search_box.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 14px;
            }
        """)
        self.search_box.textChanged.connect(self._on_search)
        filter_layout.addWidget(self.search_box, 3)
        
        self.result_filter = QComboBox()
        self.result_filter.addItems(["All Results", "White Won", "Black Won", "Draw"])
        self.result_filter.setMinimumHeight(35)
        self.result_filter.setStyleSheet("""
            QComboBox {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 14px;
            }
        """)
        self.result_filter.currentTextChanged.connect(self._on_filter)
        filter_layout.addWidget(self.result_filter, 1)
        
        layout.addLayout(filter_layout)
        
        # Games table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Date", "White", "Black", "Result", "Time Control", "Event", "Site"
        ])
        
        # Configure table
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background-color: white;
                gridline-color: #e5e7eb;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #d1d5db;
                font-weight: bold;
                color: #1f2937;
            }
        """)
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # White
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Black
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Result
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Time Control
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Event
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # Site
        
        self.table.doubleClicked.connect(self._on_game_double_clicked)
        
        layout.addWidget(self.table, 1)
        
        # Status bar
        self.status_label = QLabel("No games in library")
        self.status_label.setStyleSheet("font-size: 12px; color: #6b7280;")
        layout.addWidget(self.status_label)
    
    def refresh(self):
        """Refresh the game list from database."""
        session = self.db.get_session()
        
        try:
            # Query all games
            self.games = session.query(Game).order_by(
                desc(Game.created_at)
            ).all()
            
            # Update table
            self._update_table(self.games)
            
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
            # Date
            self.table.setItem(row, 0, QTableWidgetItem(game.date or ""))
            
            # White
            white_text = game.white or ""
            if game.white_elo:
                white_text += f" ({game.white_elo})"
            self.table.setItem(row, 1, QTableWidgetItem(white_text))
            
            # Black
            black_text = game.black or ""
            if game.black_elo:
                black_text += f" ({game.black_elo})"
            self.table.setItem(row, 2, QTableWidgetItem(black_text))
            
            # Result
            result_item = QTableWidgetItem(game.result or "*")
            result_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, result_item)
            
            # Time Control
            self.table.setItem(row, 4, QTableWidgetItem(game.time_control or ""))
            
            # Event
            self.table.setItem(row, 5, QTableWidgetItem(game.event or ""))
            
            # Site
            self.table.setItem(row, 6, QTableWidgetItem(game.site or ""))
            
            # Store game ID in row data
            self.table.item(row, 0).setData(Qt.UserRole, game.id)
    
    def _on_search(self, text: str):
        """Handle search text change."""
        if not text:
            self._update_table(self.games)
            return
        
        # Filter games by search text
        text_lower = text.lower()
        filtered = []
        
        for game in self.games:
            # Search in player names, event, site, and date
            searchable = [
                game.white or "",
                game.black or "",
                game.event or "",
                game.site or "",
                game.date or ""
            ]
            
            if any(text_lower in field.lower() for field in searchable):
                filtered.append(game)
        
        self._update_table(filtered)
        
        # Update status
        self.status_label.setText(
            f"Showing {len(filtered)} of {len(self.games)} games"
        )
    
    def _on_filter(self, filter_text: str):
        """Handle result filter change."""
        if filter_text == "All Results":
            self._update_table(self.games)
            return
        
        # Map filter text to result values
        result_map = {
            "White Won": "1-0",
            "Black Won": "0-1",
            "Draw": "1/2-1/2"
        }
        
        result_value = result_map.get(filter_text)
        if not result_value:
            return
        
        # Filter games by result
        filtered = [g for g in self.games if g.result == result_value]
        self._update_table(filtered)
        
        # Update status
        self.status_label.setText(
            f"Showing {len(filtered)} of {len(self.games)} games"
        )
    
    def _on_game_double_clicked(self, index):
        """Handle game double-click."""
        row = index.row()
        game_id = self.table.item(row, 0).data(Qt.UserRole)
        
        if game_id:
            # Open the analysis screen
            self.game_selected.emit(game_id)
