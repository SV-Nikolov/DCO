"""
Chessboard widget for displaying chess positions.
Uses python-chess to render SVG boards.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPainter, QImage, QPaintEvent
import chess
import chess.svg
from typing import Optional, List

from ...core.settings import get_settings


class ChessboardWidget(QWidget):
    """Interactive chessboard widget using SVG rendering."""
    
    square_clicked = Signal(int)  # Emits square index when clicked
    
    def __init__(self, size: int = 400, parent=None):
        """
        Initialize the chessboard widget.
        
        Args:
            size: Size of the board in pixels
            parent: Parent widget
        """
        super().__init__(parent)
        self.board = chess.Board()
        self.flipped = False
        self.highlighted_squares = []
        self.arrows = []  # List of (from_square, to_square, color) tuples
        self.last_move = None
        
        self._size = size
        self.setMinimumSize(size, size)
        self.setMaximumSize(size, size)
        
        # Load board colors from settings
        settings = get_settings()
        self.light_square_color = settings.get_board_light_color()
        self.dark_square_color = settings.get_board_dark_color()
        self.show_coordinates = settings.get_show_coordinates()
        
        # SVG renderer
        self.svg_renderer = QSvgRenderer()
        
        # Update display
        self.update_board()
    
    def set_position(self, fen: str):
        """
        Set the board position from FEN.
        
        Args:
            fen: FEN string
        """
        try:
            self.board = chess.Board(fen)
            self.update_board()
        except ValueError as e:
            print(f"Invalid FEN: {e}")
    
    def set_board(self, board: chess.Board):
        """
        Set the board position from a chess.Board object.
        
        Args:
            board: chess.Board object
        """
        self.board = board.copy()
        self.update_board()
    
    def flip_board(self):
        """Flip the board orientation."""
        self.flipped = not self.flipped
        self.update_board()
    
    def set_flipped(self, flipped: bool):
        """Set board orientation."""
        self.flipped = flipped
        self.update_board()
    
    def highlight_squares(self, squares: List[int]):
        """
        Highlight specific squares.
        
        Args:
            squares: List of square indices (0-63)
        """
        self.highlighted_squares = squares
        self.update_board()
    
    def add_arrow(self, from_square: int, to_square: int, color: str = "green"):
        """
        Add an arrow to the board.
        
        Args:
            from_square: Starting square index
            to_square: Ending square index
            color: Arrow color (green, red, blue, yellow)
        """
        self.arrows.append((from_square, to_square, color))
        self.update_board()
    
    def clear_arrows(self):
        """Clear all arrows from the board."""
        self.arrows = []
        self.update_board()
    
    def set_last_move(self, move: Optional[chess.Move]):
        """
        Highlight the last move played.
        
        Args:
            move: The last move, or None to clear
        """
        self.last_move = move
        self.update_board()
    
    def reload_settings(self):
        """Reload board colors and coordinates from settings."""
        from ...core.settings import get_settings
        settings = get_settings()
        self.light_square_color = settings.get_board_light_color()
        self.dark_square_color = settings.get_board_dark_color()
        self.show_coordinates = settings.get_show_coordinates()
        self.update_board()
    
    def update_board(self):
        """Update the board display."""
        # Generate SVG
        svg_data = self._generate_svg()
        
        # Load into renderer
        self.svg_renderer.load(svg_data)
        
        # Trigger repaint
        self.update()
    
    def _generate_svg(self) -> bytes:
        """
        Generate SVG representation of the current board state.
        
        Returns:
            SVG data as bytes
        """
        # Build fill dict for highlighted squares
        fill = {}
        for square in self.highlighted_squares:
            fill[square] = "#ffff0080"  # Yellow with transparency
        
        # Highlight last move
        if self.last_move:
            fill[self.last_move.from_square] = "#ffff0060"
            fill[self.last_move.to_square] = "#ffff0060"
        
        # Build arrows list
        arrows_list = []
        for from_sq, to_sq, color in self.arrows:
            arrows_list.append(chess.svg.Arrow(from_sq, to_sq, color=color))
        
        # Custom board colors
        colors = {
            'square light': self.light_square_color,
            'square dark': self.dark_square_color
        }
        
        # Generate SVG
        svg = chess.svg.board(
            self.board,
            flipped=self.flipped,
            size=self._size,
            fill=fill,
            arrows=arrows_list,
            coordinates=self.show_coordinates,
            colors=colors
        )
        
        return svg.encode('utf-8')
    
    def paintEvent(self, event: QPaintEvent):
        """Paint the chessboard."""
        if not self.svg_renderer.isValid():
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Render the SVG
        self.svg_renderer.render(painter)
    
    def sizeHint(self):
        """Preferred size of the widget."""
        from PySide6.QtCore import QSize
        return QSize(self._size, self._size)
    
    def mousePressEvent(self, event):
        """Handle mouse clicks on the board."""
        # Calculate which square was clicked
        square_size = self._size / 8
        x = event.position().x()
        y = event.position().y()
        
        file = int(x / square_size)
        rank = 7 - int(y / square_size)
        
        if self.flipped:
            file = 7 - file
            rank = 7 - rank
        
        square = chess.square(file, rank)
        self.square_clicked.emit(square)


class SimpleBoardDisplay(QWidget):
    """Simple non-interactive board display for showing positions."""
    
    def __init__(self, size: int = 300, parent=None):
        """
        Initialize simple board display.
        
        Args:
            size: Size of the board in pixels
            parent: Parent widget
        """
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Board widget
        self.board_widget = ChessboardWidget(size, self)
        layout.addWidget(self.board_widget)
    
    def set_position(self, fen: str):
        """Set board position from FEN."""
        self.board_widget.set_position(fen)
    
    def set_board(self, board: chess.Board):
        """Set board from chess.Board object."""
        self.board_widget.set_board(board)
    
    def flip_board(self):
        """Flip the board."""
        self.board_widget.flip_board()
    
    def highlight_squares(self, squares: List[int]):
        """Highlight squares."""
        self.board_widget.highlight_squares(squares)
    
    def add_arrow(self, from_square: int, to_square: int, color: str = "green"):
        """Add an arrow."""
        self.board_widget.add_arrow(from_square, to_square, color)
    
    def clear_arrows(self):
        """Clear arrows."""
        self.board_widget.clear_arrows()
    
    def set_last_move(self, move: Optional[chess.Move]):
        """Set last move highlight."""
        self.board_widget.set_last_move(move)
