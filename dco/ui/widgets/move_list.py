"""
Move list widget for displaying game moves with classifications.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import List, Optional

from ...data.models import Move, MoveClassification


# Colors for move classifications
CLASSIFICATION_COLORS = {
    MoveClassification.BOOK: QColor(200, 200, 200),  # Gray
    MoveClassification.BEST: QColor(144, 238, 144),  # Light green
    MoveClassification.EXCELLENT: QColor(173, 216, 230),  # Light blue
    MoveClassification.GOOD: QColor(255, 255, 224),  # Light yellow
    MoveClassification.INACCURACY: QColor(255, 228, 181),  # Moccasin
    MoveClassification.MISTAKE: QColor(255, 200, 124),  # Light orange
    MoveClassification.BLUNDER: QColor(255, 160, 122),  # Light coral/red
    MoveClassification.CRITICAL: QColor(255, 215, 0),  # Gold
    MoveClassification.BRILLIANT: QColor(147, 112, 219),  # Medium purple
}

# String-based lookup for when values come from DB (enum names, uppercase)
CLASSIFICATION_COLORS_STR = {
    "BOOK": QColor(200, 200, 200),  # Gray
    "BEST": QColor(144, 238, 144),  # Light green
    "EXCELLENT": QColor(173, 216, 230),  # Light blue
    "GOOD": QColor(255, 255, 224),  # Light yellow
    "INACCURACY": QColor(255, 228, 181),  # Moccasin
    "MISTAKE": QColor(255, 200, 124),  # Light orange
    "BLUNDER": QColor(255, 160, 122),  # Light coral/red
    "CRITICAL": QColor(255, 215, 0),  # Gold
    "BRILLIANT": QColor(147, 112, 219),  # Medium purple
}

# Symbols for classifications
CLASSIFICATION_SYMBOLS = {
    MoveClassification.BOOK: "📖",
    MoveClassification.BEST: "✓",
    MoveClassification.EXCELLENT: "👍",
    MoveClassification.GOOD: "○",
    MoveClassification.INACCURACY: "?!",
    MoveClassification.MISTAKE: "?",
    MoveClassification.BLUNDER: "??",
    MoveClassification.CRITICAL: "⚠",
    MoveClassification.BRILLIANT: "!!",
}

# String-based lookup for symbols (enum names, uppercase)
CLASSIFICATION_SYMBOLS_STR = {
    "BOOK": "📖",
    "BEST": "✓",
    "EXCELLENT": "👍",
    "GOOD": "○",
    "INACCURACY": "?!",
    "MISTAKE": "?",
    "BLUNDER": "??",
    "CRITICAL": "⚠",
    "BRILLIANT": "!!",
}


class MoveListWidget(QWidget):
    """Widget for displaying a list of moves with classifications."""
    
    move_selected = Signal(int)  # Emits move index (ply) when selected
    
    def __init__(self, parent=None):
        """Initialize move list widget."""
        super().__init__(parent)
        self.moves_data = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "#", "White", "Black", "Eval"
        ])
        
        # Set table stylesheet for proper text colors
        self.table.setStyleSheet("""
            QTableWidget {
                color: #000000;
            }
            QTableWidget::item {
                color: #000000;
            }
            QHeaderView::section {
                color: #1f2937;
                background-color: #f3f4f6;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #d1d5db;
                font-weight: bold;
            }
        """)
        
        # Configure table
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Move number
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # White's move
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Black's move
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Eval
        
        # Connect selection signal
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.table)
    
    def set_moves(self, moves: List[Move]):
        """
        Set the list of moves to display.
        
        Args:
            moves: List of Move objects from database
        """
        self.moves_data = moves
        self._update_table()
    
    def _update_table(self):
        """Update the table display."""
        # Group moves by pairs (White and Black)
        move_pairs = []
        for i in range(0, len(self.moves_data), 2):
            white_move = self.moves_data[i]
            black_move = self.moves_data[i + 1] if i + 1 < len(self.moves_data) else None
            move_pairs.append((white_move, black_move))
        
        # Set row count
        self.table.setRowCount(len(move_pairs))
        
        # Populate table
        for row, (white_move, black_move) in enumerate(move_pairs):
            # Move number
            move_num = QTableWidgetItem(str(row + 1))
            move_num.setTextAlignment(Qt.AlignCenter)
            move_num.setForeground(QColor(0, 0, 0))  # Black text
            self.table.setItem(row, 0, move_num)
            
            # White's move
            white_item = self._create_move_item(white_move)
            self.table.setItem(row, 1, white_item)
            
            # Black's move
            if black_move:
                black_item = self._create_move_item(black_move)
                self.table.setItem(row, 2, black_item)
            else:
                empty_item = QTableWidgetItem("")
                empty_item.setForeground(QColor(0, 0, 0))
                self.table.setItem(row, 2, empty_item)
            
            # Evaluation (show after White's move)
            eval_text = self._format_eval(white_move.eval_after_cp)
            eval_item = QTableWidgetItem(eval_text)
            eval_item.setTextAlignment(Qt.AlignCenter)
            eval_item.setForeground(QColor(0, 0, 0))  # Black text
            self.table.setItem(row, 3, eval_item)
    
    def _create_move_item(self, move: Move) -> QTableWidgetItem:
        """
        Create a table item for a move.
        
        Args:
            move: Move object
            
        Returns:
            QTableWidgetItem with move text and styling
        """
        # Get classification - handle both enum and string values
        classification = move.classification
        
        if isinstance(classification, MoveClassification):
            # Enum object
            symbol = CLASSIFICATION_SYMBOLS.get(classification, "")
            color = CLASSIFICATION_COLORS.get(classification)
        else:
            # String value from database (enum name in uppercase)
            classification_str = str(classification).upper()
            symbol = CLASSIFICATION_SYMBOLS_STR.get(classification_str, "")
            color = CLASSIFICATION_COLORS_STR.get(classification_str)
        
        # Create text
        text = f"{move.san} {symbol}".strip()
        
        # Create item
        item = QTableWidgetItem(text)
        
        # Set background color based on classification
        if color:
            item.setBackground(color)
        
        # Set text color to black for visibility
        item.setForeground(QColor(0, 0, 0))
        
        # Bold for brilliant moves
        if move.is_brilliant:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        
        # Store move index in item data
        item.setData(Qt.UserRole, move.ply_index)
        
        return item
    
    def _format_eval(self, eval_cp: Optional[int]) -> str:
        """
        Format evaluation score for display.
        
        Args:
            eval_cp: Evaluation in centipawns
            
        Returns:
            Formatted string
        """
        if eval_cp is None:
            return ""
        
        # Convert to pawns
        eval_pawns = eval_cp / 100.0
        
        # Format with sign
        if eval_pawns > 0:
            return f"+{eval_pawns:.2f}"
        else:
            return f"{eval_pawns:.2f}"
    
    def _on_selection_changed(self):
        """Handle move selection."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        
        # Get the move index from the first selected item
        for item in selected_items:
            ply_index = item.data(Qt.UserRole)
            if ply_index is not None:
                self.move_selected.emit(ply_index)
                break
    
    def select_move(self, ply_index: int):
        """
        Select a move by its ply index.
        
        Args:
            ply_index: The ply index to select
        """
        # Find the row and column for this move
        row = ply_index // 2
        col = 1 if ply_index % 2 == 0 else 2
        
        if row < self.table.rowCount():
            item = self.table.item(row, col)
            if item:
                self.table.setCurrentItem(item)
                self.table.scrollToItem(item)
