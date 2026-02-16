"""
Home screen for DCO.
Shows quick stats and recent activity.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from sqlalchemy import func, desc

from ...data.models import Game, Session as TrainingSession, SessionType, PracticeItem
from ...data.db import Database


class StatCard(QFrame):
    """Card widget for displaying a statistic."""
    
    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 20px;
            }
            QLabel {
                color: #1f2937;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #6b7280;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #1f2937;")
        layout.addWidget(value_label)


class HomeScreen(QWidget):
    """Home screen of the application."""

    practice_requested = Signal()
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.refresh()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Set base styling for visibility
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: #1f2937;
            }
            QLabel {
                color: #1f2937;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Welcome header
        welcome_label = QLabel("Welcome to Daily Chess Offline")
        welcome_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #1f2937;")
        layout.addWidget(welcome_label)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        self.practice_btn = QPushButton("Continue Practice")
        self.practice_btn.setMinimumHeight(50)
        self.practice_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        self.practice_btn.setEnabled(False)  # Disabled until we have practice items
        self.practice_btn.clicked.connect(self.practice_requested.emit)
        actions_layout.addWidget(self.practice_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        # Stats section
        stats_label = QLabel("Quick Stats")
        stats_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1f2937;")
        layout.addWidget(stats_label)
        
        # Stats cards
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(20)
        
        self.games_card = StatCard("Total Games", "0")
        self.stats_layout.addWidget(self.games_card)
        
        self.practice_card = StatCard("Practice Sessions", "0")
        self.stats_layout.addWidget(self.practice_card)
        
        self.accuracy_card = StatCard("Avg Accuracy", "-%")
        self.stats_layout.addWidget(self.accuracy_card)
        
        self.stats_layout.addStretch()
        layout.addLayout(self.stats_layout)
        
        # Recent activity
        activity_label = QLabel("Recent Activity")
        activity_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1f2937;")
        layout.addWidget(activity_label)
        
        # Scroll area for recent games
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: white;
            }
        """)
        
        self.activity_widget = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_widget)
        self.activity_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.activity_widget)
        
        layout.addWidget(scroll, 1)  # Stretch to fill remaining space
    
    def refresh(self):
        """Refresh the home screen data."""
        session = self.db.get_session()
        
        try:
            # Get total games count
            total_games = session.query(func.count(Game.id)).scalar() or 0
            self.games_card.findChild(QLabel, options=Qt.FindChildrenRecursively).setText(str(total_games))
            
            # Get practice sessions count
            total_sessions = session.query(func.count(TrainingSession.id)).filter(
                TrainingSession.type == SessionType.PRACTICE
            ).scalar() or 0

            # Enable practice button if we have items
            total_practice_items = session.query(func.count(PracticeItem.id)).scalar() or 0
            self.practice_btn.setEnabled(total_practice_items > 0)
            self.practice_card.findChild(QLabel, options=Qt.FindChildrenRecursively).setText(str(total_sessions))
            
            # Update stats card values
            for card in [self.games_card, self.practice_card, self.accuracy_card]:
                labels = [child for child in card.children() if isinstance(child, QLabel)]
                if len(labels) >= 2:
                    if card == self.games_card:
                        labels[1].setText(str(total_games))
                    elif card == self.practice_card:
                        labels[1].setText(str(total_sessions))
            
            # Get recent games
            recent_games = session.query(Game).order_by(
                desc(Game.created_at)
            ).limit(10).all()
            
            # Clear existing activity items
            for i in reversed(range(self.activity_layout.count())):
                widget = self.activity_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            # Add recent games
            if recent_games:
                for game in recent_games:
                    item = self._create_activity_item(game)
                    self.activity_layout.addWidget(item)
            else:
                no_data = QLabel("No games imported yet. Go to Import to add games.")
                no_data.setStyleSheet("color: #6b7280; padding: 20px;")
                no_data.setAlignment(Qt.AlignCenter)
                self.activity_layout.addWidget(no_data)
        
        finally:
            session.close()
    
    def _create_activity_item(self, game: Game) -> QWidget:
        """Create an activity item widget for a game."""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 15px;
                margin-bottom: 5px;
            }
        """)
        
        layout = QVBoxLayout(item)
        layout.setSpacing(5)
        
        # Players and result
        header = QLabel(f"{game.white} vs {game.black} • {game.result}")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #1f2937;")
        layout.addWidget(header)
        
        # Details
        details = []
        if game.date:
            details.append(game.date)
        if game.time_control:
            details.append(game.time_control)
        if game.event:
            details.append(game.event)
        
        details_label = QLabel(" • ".join(details))
        details_label.setStyleSheet("font-size: 12px; color: #6b7280;")
        layout.addWidget(details_label)
        
        return item
