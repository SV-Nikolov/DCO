"""
Statistics dashboard screen for DCO.
Displays accuracy, estimated Elo, and error trends over time.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, QDate, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QDateEdit, QFrame, QGridLayout, QGraphicsOpacityEffect
)

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from sqlalchemy import func

from ...data.db import Database
from ...data.models import Game, Analysis, Move, MoveClassification


class StatCarousel(QFrame):
    """Carousel widget for displaying statistics one at a time with navigation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        self.current_index = 0
        self.stats = []  # List of (label, value) tuples
        self.animating = False
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(20)
        
        # Left arrow button
        self.left_btn = QPushButton("◀")
        self.left_btn.setFixedSize(40, 40)
        self.left_btn.clicked.connect(self._previous_stat)
        self.left_btn.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.left_btn)
        
        # Stat display area
        stat_widget = QWidget()
        stat_layout = QVBoxLayout(stat_widget)
        stat_layout.setContentsMargins(20, 10, 20, 10)
        stat_layout.setSpacing(10)
        stat_layout.setAlignment(Qt.AlignCenter)
        
        self.label = QLabel("")
        self.label.setObjectName("statLabel")
        self.label.setAlignment(Qt.AlignCenter)
        stat_layout.addWidget(self.label)
        
        self.value = QLabel("0")
        self.value.setObjectName("statValue")
        self.value.setAlignment(Qt.AlignCenter)
        stat_layout.addWidget(self.value)
        
        # Indicator dots
        self.dots_layout = QHBoxLayout()
        self.dots_layout.setSpacing(8)
        self.dots_layout.setAlignment(Qt.AlignCenter)
        stat_layout.addLayout(self.dots_layout)
        
        self.dots = []
        
        layout.addWidget(stat_widget, 1)
        
        # Right arrow button
        self.right_btn = QPushButton("▶")
        self.right_btn.setFixedSize(40, 40)
        self.right_btn.clicked.connect(self._next_stat)
        self.right_btn.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.right_btn)
        
        # Opacity effect for fade animation
        self.opacity_effect = QGraphicsOpacityEffect()
        stat_widget.setGraphicsEffect(self.opacity_effect)
        
    def set_stats(self, stats: List[Tuple[str, str]]):
        """Set the statistics to display."""
        self.stats = stats
        self.current_index = 0
        
        # Create indicator dots
        for dot in self.dots:
            dot.deleteLater()
        self.dots.clear()
        
        for i in range(len(stats)):
            dot = QLabel("●")
            dot.setStyleSheet("color: #64748b; font-size: 12px;")
            dot.setAlignment(Qt.AlignCenter)
            self.dots_layout.addWidget(dot)
            self.dots.append(dot)
        
        self._update_display()
    
    def _update_display(self):
        """Update the displayed statistic."""
        if not self.stats:
            return
        
        label_text, value_text = self.stats[self.current_index]
        self.label.setText(label_text)
        self.value.setText(value_text)
        
        # Update dots
        for i, dot in enumerate(self.dots):
            if i == self.current_index:
                dot.setStyleSheet("color: #3b82f6; font-size: 14px;")
            else:
                dot.setStyleSheet("color: #64748b; font-size: 12px;")
        
        # Update button states
        self.left_btn.setEnabled(self.current_index > 0)
        self.right_btn.setEnabled(self.current_index < len(self.stats) - 1)
    
    def _animate_transition(self):
        """Animate the transition with fade effect."""
        if self.animating:
            return
        
        self.animating = True
        
        # Fade out
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Fade in
        fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_in.setDuration(200)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Update display in the middle
        def on_fade_out_finished():
            self._update_display()
            fade_in.start()
        
        def on_fade_in_finished():
            self.animating = False
        
        fade_out.finished.connect(on_fade_out_finished)
        fade_in.finished.connect(on_fade_in_finished)
        
        fade_out.start()
    
    def _next_stat(self):
        """Show next statistic."""
        if self.current_index < len(self.stats) - 1:
            self.current_index += 1
            self._animate_transition()
    
    def _previous_stat(self):
        """Show previous statistic."""
        if self.current_index > 0:
            self.current_index -= 1
            self._animate_transition()


class StatisticsScreen(QWidget):
    """Statistics dashboard screen."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.refresh()

    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Styled by global stylesheet

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()
        title = QLabel("Statistics")
        title.setObjectName("screenTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        controls = QFrame()
        controls.setObjectName("cardFrame")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(15, 10, 15, 10)
        controls_layout.setSpacing(10)

        range_label = QLabel("Date Range")
        range_label.setStyleSheet("font-weight: bold;")  # Keep bold inline for form labels
        controls_layout.addWidget(range_label)

        self.range_combo = QComboBox()
        self.range_combo.addItems([
            "Last 7 days",
            "Last 30 days",
            "Last 90 days",
            "All time",
            "Custom"
        ])
        self.range_combo.currentIndexChanged.connect(self._on_range_changed)
        controls_layout.addWidget(self.range_combo)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setEnabled(False)
        controls_layout.addWidget(self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setEnabled(False)
        controls_layout.addWidget(self.end_date_edit)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("primaryButton")
        self.refresh_btn.clicked.connect(self.refresh)
        controls_layout.addWidget(self.refresh_btn)

        controls_layout.addStretch()
        layout.addWidget(controls)

        # Statistics carousel
        self.stat_carousel = StatCarousel()
        layout.addWidget(self.stat_carousel)

        charts = QFrame()
        charts_layout = QGridLayout(charts)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        charts_layout.setSpacing(15)

        self.accuracy_canvas, self.accuracy_ax = self._create_chart()
        self.elo_canvas, self.elo_ax = self._create_chart()
        self.blunders_canvas, self.blunders_ax = self._create_chart()
        self.mistakes_canvas, self.mistakes_ax = self._create_chart()

        charts_layout.addWidget(self.accuracy_canvas, 0, 0)
        charts_layout.addWidget(self.elo_canvas, 0, 1)
        charts_layout.addWidget(self.blunders_canvas, 1, 0)
        charts_layout.addWidget(self.mistakes_canvas, 1, 1)

        layout.addWidget(charts)

        today = datetime.utcnow().date()
        self.start_date_edit.setDate(QDate(today.year, today.month, today.day))
        self.end_date_edit.setDate(QDate(today.year, today.month, today.day))

    def _create_chart(self) -> Tuple[FigureCanvas, any]:
        """Create a matplotlib chart canvas and axis."""
        fig = Figure(figsize=(4, 3), tight_layout=True)
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        return canvas, ax

    def _on_range_changed(self) -> None:
        """Enable custom date selection when needed."""
        is_custom = self.range_combo.currentText() == "Custom"
        self.start_date_edit.setEnabled(is_custom)
        self.end_date_edit.setEnabled(is_custom)

    def _get_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get selected date range."""
        selection = self.range_combo.currentText()
        now = datetime.utcnow()

        if selection == "Last 7 days":
            return now - timedelta(days=7), now
        if selection == "Last 30 days":
            return now - timedelta(days=30), now
        if selection == "Last 90 days":
            return now - timedelta(days=90), now
        if selection == "All time":
            return None, None

        start_qdate = self.start_date_edit.date()
        end_qdate = self.end_date_edit.date()
        start = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
        end = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59)
        if start > end:
            start, end = end, start
        return start, end

    def refresh(self) -> None:
        """Refresh the statistics data and charts."""
        start_date, end_date = self._get_date_range()

        session = self.db.get_session()
        try:
            base_query = session.query(Game, Analysis).join(Analysis, Game.id == Analysis.game_id)
            if start_date:
                base_query = base_query.filter(Game.created_at >= start_date)
            if end_date:
                base_query = base_query.filter(Game.created_at <= end_date)

            rows = base_query.order_by(Game.created_at.asc()).all()

            dates: List[str] = []
            accuracies: List[float] = []
            elos: List[float] = []
            game_ids: List[int] = []

            for game, analysis in rows:
                avg_acc = self._avg_two(analysis.accuracy_white, analysis.accuracy_black)
                avg_elo = self._avg_two(analysis.perf_elo_white, analysis.perf_elo_black)
                if avg_acc is None or avg_elo is None:
                    continue
                dates.append(game.created_at.strftime("%Y-%m-%d"))
                accuracies.append(avg_acc)
                elos.append(avg_elo)
                game_ids.append(game.id)

            # Summary metrics
            total_games = len(game_ids)
            avg_accuracy = int(sum(accuracies) / total_games) if total_games else 0
            avg_elo = int(sum(elos) / total_games) if total_games else 0
            
            blunders_per_game = 0.0
            blunder_counts = []
            if game_ids:
                blunder_counts = self._blunder_counts(session, game_ids)
                blunders_per_game = sum(blunder_counts) / len(blunder_counts) if blunder_counts else 0.0
            
            # Update carousel with statistics
            stats = [
                ("GAMES ANALYZED", str(total_games)),
                ("AVERAGE ACCURACY", f"{avg_accuracy}%"),
                ("ESTIMATED ELO", str(avg_elo)),
                ("AVG BLUNDERS/GAME", f"{blunders_per_game:.1f}")
            ]
            self.stat_carousel.set_stats(stats)

            # Charts
            self._plot_line(self.accuracy_ax, "Accuracy Over Time", dates, accuracies, 0, 100)
            self._plot_line(self.elo_ax, "Estimated Elo Over Time", dates, elos, None, None)
            self._plot_bar(self.blunders_ax, "Blunders Per Game", blunder_counts)
            self._plot_mistake_pie(self.mistakes_ax, session, game_ids)

            self.accuracy_canvas.draw()
            self.elo_canvas.draw()
            self.blunders_canvas.draw()
            self.mistakes_canvas.draw()
        finally:
            session.close()

    def _avg_two(self, a: Optional[float], b: Optional[float]) -> Optional[float]:
        """Return average of two values if any is present."""
        values = [v for v in (a, b) if v is not None]
        if not values:
            return None
        return sum(values) / len(values)

    def _blunder_counts(self, session, game_ids: List[int]) -> List[int]:
        """Return blunder counts per game id in the same order as game_ids."""
        counts = {gid: 0 for gid in game_ids}
        rows = session.query(Move.game_id, func.count(Move.id)).filter(
            Move.game_id.in_(game_ids),
            Move.classification == MoveClassification.BLUNDER
        ).group_by(Move.game_id).all()
        for game_id, count in rows:
            counts[game_id] = count
        return [counts[gid] for gid in game_ids]

    def _plot_line(
        self,
        ax,
        title: str,
        labels: List[str],
        values: List[float],
        y_min: Optional[float],
        y_max: Optional[float]
    ) -> None:
        """Plot a line chart."""
        ax.clear()
        ax.set_title(title)
        if not labels:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])
            return

        x = list(range(len(labels)))
        ax.plot(x, values, marker="o", color="#2563eb")
        if y_min is not None and y_max is not None:
            ax.set_ylim(y_min, y_max)

        step = max(1, len(labels) // 6)
        tick_positions = list(range(0, len(labels), step))
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([labels[i] for i in tick_positions], rotation=45, ha="right")
        ax.grid(True, alpha=0.2)

    def _plot_bar(self, ax, title: str, values: List[int]) -> None:
        """Plot a bar chart."""
        ax.clear()
        ax.set_title(title)
        if not values:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])
            return

        x = list(range(1, len(values) + 1))
        ax.bar(x, values, color="#ef4444")
        ax.set_xlabel("Game")
        ax.set_ylabel("Blunders")
        ax.grid(True, axis="y", alpha=0.2)

    def _plot_mistake_pie(self, ax, session, game_ids: List[int]) -> None:
        """Plot a pie chart for error distribution."""
        ax.clear()
        ax.set_title("Mistakes by Type")
        if not game_ids:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])
            return

        rows = session.query(Move.classification, func.count(Move.id)).filter(
            Move.game_id.in_(game_ids),
            Move.classification.in_(
                [MoveClassification.INACCURACY, MoveClassification.MISTAKE, MoveClassification.BLUNDER]
            )
        ).group_by(Move.classification).all()

        labels = []
        sizes = []
        for classification, count in rows:
            labels.append(classification.name.title())
            sizes.append(count)

        if not sizes:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])
            return

        ax.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=140)
        ax.axis("equal")
