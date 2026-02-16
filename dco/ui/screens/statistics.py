"""
Statistics dashboard screen for DCO.
Displays accuracy, estimated Elo, and error trends over time.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QDateEdit, QFrame, QGridLayout
)

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from sqlalchemy import func

from ...data.db import Database
from ...data.models import Game, Analysis, Move, MoveClassification


class StatisticsScreen(QWidget):
    """Statistics dashboard screen."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.refresh()

    def init_ui(self) -> None:
        """Initialize the user interface."""
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()
        title = QLabel("Statistics")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        controls = QFrame()
        controls.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(15, 10, 15, 10)
        controls_layout.setSpacing(10)

        range_label = QLabel("Date Range")
        range_label.setStyleSheet("font-weight: bold;")
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
        self.refresh_btn.clicked.connect(self.refresh)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        controls_layout.addWidget(self.refresh_btn)

        controls_layout.addStretch()
        layout.addWidget(controls)

        summary = QFrame()
        summary.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        summary_layout = QHBoxLayout(summary)
        summary_layout.setContentsMargins(15, 10, 15, 10)
        summary_layout.setSpacing(20)

        self.games_label = QLabel("Games: 0")
        self.accuracy_label = QLabel("Avg Accuracy: 0%")
        self.elo_label = QLabel("Avg Elo: 0")
        self.blunders_label = QLabel("Blunders/Game: 0")

        summary_layout.addWidget(self.games_label)
        summary_layout.addWidget(self.accuracy_label)
        summary_layout.addWidget(self.elo_label)
        summary_layout.addWidget(self.blunders_label)
        summary_layout.addStretch()
        layout.addWidget(summary)

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
            if game_ids:
                blunder_counts = self._blunder_counts(session, game_ids)
                blunders_per_game = sum(blunder_counts) / len(blunder_counts) if blunder_counts else 0.0

            self.games_label.setText(f"Games: {total_games}")
            self.accuracy_label.setText(f"Avg Accuracy: {avg_accuracy}%")
            self.elo_label.setText(f"Avg Elo: {avg_elo}")
            self.blunders_label.setText(f"Blunders/Game: {blunders_per_game:.2f}")

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
