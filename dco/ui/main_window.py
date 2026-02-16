"""
Main window for the DCO application.
Contains the navigation rail and content area.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from .screens.home import HomeScreen
from .screens.library import LibraryScreen
from .screens.import_pgn import ImportScreen
from .screens.analysis import AnalysisScreen
from .screens.practice import PracticeScreen
from .screens.puzzles import PuzzleScreen
from .screens.statistics import StatisticsScreen
from ..data.db import get_db


class NavigationButton(QPushButton):
    """Custom button for navigation rail."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setMinimumHeight(50)
        # Styling is handled by modern_stylesheet.py


class MainWindow(QMainWindow):
    """Main application window with navigation."""
    
    def __init__(self):
        super().__init__()
        self.db = get_db()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Daily Chess Offline (DCO)")
        self.setMinimumSize(1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout (horizontal: nav rail + content)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Navigation rail
        nav_widget = self._create_navigation()
        main_layout.addWidget(nav_widget)
        
        # Content area
        self.content_stack = QStackedWidget()
        # Modern stylesheet handles background
        main_layout.addWidget(self.content_stack)
        
        # Add screens
        self._add_screens()
        
        # Select Home by default
        self.nav_buttons[0].setChecked(True)
        self.content_stack.setCurrentIndex(0)
    
    def _create_navigation(self) -> QWidget:
        """Create the navigation rail."""
        nav_widget = QFrame()
        nav_widget.setObjectName("navWidget")  # CSS styling
        nav_widget.setFixedWidth(200)
        
        layout = QVBoxLayout(nav_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # App title
        title_label = QLabel("DCO")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            padding: 20px;
            color: #1f2937;
        """)
        layout.addWidget(title_label)
        
        # Navigation buttons
        nav_items = [
            "Home",
            "Play",
            "Import",
            "Library",
            "Analysis",
            "Practice",
            "Puzzles",
            "Statistics",
            "Settings"
        ]
        
        self.nav_buttons = []
        for item in nav_items:
            btn = NavigationButton(item)
            btn.clicked.connect(lambda checked, i=len(self.nav_buttons): self._on_nav_click(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        layout.addStretch()
        
        # Version info
        version_label = QLabel("v0.1.0")
        version_label.setObjectName("versionLabel")
        layout.addWidget(version_label)
        
        return nav_widget
    
    def _add_screens(self):
        """Add all screens to the content stack."""
        # Home screen
        self.home_screen = HomeScreen(self.db)
        self.home_screen.practice_requested.connect(self._go_to_practice)
        self.content_stack.addWidget(self.home_screen)
        
        # Play screen (placeholder)
        play_placeholder = QLabel("Play vs Computer - Coming Soon")
        play_placeholder.setAlignment(Qt.AlignCenter)
        play_placeholder.setObjectName("placeholderText")
        self.content_stack.addWidget(play_placeholder)
        
        # Import screen
        self.import_screen = ImportScreen(self.db)
        self.import_screen.import_completed.connect(self._on_import_completed)
        self.content_stack.addWidget(self.import_screen)
        
        # Library screen
        self.library_screen = LibraryScreen(self.db)
        self.library_screen.game_selected.connect(self._on_game_selected)
        self.content_stack.addWidget(self.library_screen)
        
        # Analysis screen
        self.analysis_screen = AnalysisScreen(self.db)
        self.content_stack.addWidget(self.analysis_screen)
        
        # Practice screen
        self.practice_screen = PracticeScreen(self.db)
        self.content_stack.addWidget(self.practice_screen)
        
        # Puzzles screen
        self.puzzles_screen = PuzzleScreen(self.db)
        self.content_stack.addWidget(self.puzzles_screen)
        
        # Statistics screen
        self.statistics_screen = StatisticsScreen(self.db)
        self.content_stack.addWidget(self.statistics_screen)
        
        # Settings screen (placeholder)
        settings_placeholder = QLabel("Settings - Coming Soon")
        settings_placeholder.setAlignment(Qt.AlignCenter)
        settings_placeholder.setStyleSheet("font-size: 18px; color: #6b7280;")
        self.content_stack.addWidget(settings_placeholder)
    
    def _on_nav_click(self, index: int):
        """Handle navigation button click."""
        # Uncheck all buttons
        for btn in self.nav_buttons:
            btn.setChecked(False)
        
        # Check clicked button
        self.nav_buttons[index].setChecked(True)
        
        # Switch content
        self.content_stack.setCurrentIndex(index)
    
    def _on_import_completed(self, count: int):
        """Handle import completion."""
        # Refresh home screen to show new games
        self.home_screen.refresh()
        
        # Refresh library screen if needed
        if hasattr(self, 'library_screen'):
            self.library_screen.refresh()
    
    def _on_game_selected(self, game_id: int):
        """Handle game selection from library."""
        # Load game in analysis screen
        self.analysis_screen.load_game(game_id)
        
        # Navigate to analysis screen (index 4)
        self._on_nav_click(4)

    def _go_to_practice(self):
        """Navigate directly to the Practice screen."""
        self._on_nav_click(5)
