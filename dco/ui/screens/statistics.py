"""
Statistics dashboard screen for DCO.
Displays backend analytics using an HTML/CSS layout.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from string import Template
import base64
from typing import Dict, Optional, Tuple

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QDateEdit, QFrame
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from ...data.db import Database
from ...data.models import Game, Analysis, GameAnalytics


class StatisticsScreen(QWidget):
    """Statistics dashboard screen."""

    SVG_FONT_FAMILY = "Segoe UI, Trebuchet MS, Verdana, sans-serif"
    SVG_TITLE_SIZE = 10
    SVG_DATA_SIZE = 9
    SVG_LABEL_SIZE = 9
    SVG_TITLE_COLOR = "#cbd5f5"
    SVG_DATA_COLOR = "#e2e8f0"
    SVG_MUTED_COLOR = "#94a3b8"

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.refresh()

    def init_ui(self) -> None:
        """Initialize the user interface."""
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
        self.refresh_btn.setObjectName("primaryButton")
        self.refresh_btn.clicked.connect(self.refresh)
        controls_layout.addWidget(self.refresh_btn)

        controls_layout.addStretch()
        layout.addWidget(controls)

        self.html_view = QWebEngineView()
        self.html_view.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.html_view, 1)

        today = datetime.utcnow().date()
        self.start_date_edit.setDate(QDate(today.year, today.month, today.day))
        self.end_date_edit.setDate(QDate(today.year, today.month, today.day))

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
        """Refresh the statistics data and HTML view."""
        start_date, end_date = self._get_date_range()

        session = self.db.get_session()
        try:
            query = (
                session.query(Game, Analysis, GameAnalytics)
                .join(Analysis, Game.id == Analysis.game_id)
                .join(GameAnalytics, Game.id == GameAnalytics.game_id)
            )
            if start_date:
                query = query.filter(Game.created_at >= start_date)
            if end_date:
                query = query.filter(Game.created_at <= end_date)

            rows = query.order_by(Game.created_at.asc()).all()

            if not rows:
                self.html_view.setHtml(self._build_empty_state())
                return

            total_games = 0
            accuracies = []
            elos = []
            acpl_overall_sum = 0.0
            acpl_overall_count = 0
            acpl_series = []

            phase_totals = self._init_phase_totals()
            phase_games = {"opening": 0, "middlegame": 0, "endgame": 0}

            cpl_buckets = {"0_20": 0, "20_50": 0, "50_100": 0, "100_200": 0, "200_plus": 0, "total": 0}

            critical_faced = 0
            critical_solved = 0
            critical_failed = 0
            acpl_critical_sum = 0.0
            acpl_critical_count = 0

            color_stats = {
                "white": {"acpl_sum": 0.0, "acpl_count": 0, "blunders": 0, "mistakes": 0, "inaccuracies": 0},
                "black": {"acpl_sum": 0.0, "acpl_count": 0, "blunders": 0, "mistakes": 0, "inaccuracies": 0},
            }

            for game, analysis, analytics in rows:
                total_games += 1
                avg_acc = self._avg_two(analysis.accuracy_white, analysis.accuracy_black)
                avg_elo = self._avg_two(analysis.perf_elo_white, analysis.perf_elo_black)
                if avg_acc is not None:
                    accuracies.append(avg_acc)
                if avg_elo is not None:
                    elos.append(avg_elo)

                if analytics.acpl_overall is not None:
                    acpl_overall_sum += analytics.acpl_overall
                    acpl_overall_count += 1
                    acpl_series.append(analytics.acpl_overall)

                phase_counts = analytics.phase_error_counts or {}
                for phase_key in ("opening", "middlegame", "endgame"):
                    phase_data = phase_counts.get(phase_key, {})
                    if phase_data.get("total_moves", 0) > 0:
                        phase_games[phase_key] += 1
                    self._accumulate_phase(phase_totals[phase_key], phase_data)

                cpl_dist = analytics.cpl_distribution or {}
                for key in cpl_buckets:
                    cpl_buckets[key] += int(cpl_dist.get(key, 0) or 0)

                critical_faced += int(analytics.critical_faced or 0)
                critical_solved += int(analytics.critical_solved or 0)
                critical_failed += int(analytics.critical_failed or 0)
                if analytics.acpl_critical is not None:
                    acpl_critical_sum += analytics.acpl_critical
                    acpl_critical_count += 1

                if analytics.acpl_white is not None:
                    color_stats["white"]["acpl_sum"] += analytics.acpl_white
                    color_stats["white"]["acpl_count"] += 1
                if analytics.acpl_black is not None:
                    color_stats["black"]["acpl_sum"] += analytics.acpl_black
                    color_stats["black"]["acpl_count"] += 1

                color_stats["white"]["blunders"] += int(analytics.blunders_white or 0)
                color_stats["black"]["blunders"] += int(analytics.blunders_black or 0)
                color_stats["white"]["mistakes"] += int(analytics.mistakes_white or 0)
                color_stats["black"]["mistakes"] += int(analytics.mistakes_black or 0)
                color_stats["white"]["inaccuracies"] += int(analytics.inaccuracies_white or 0)
                color_stats["black"]["inaccuracies"] += int(analytics.inaccuracies_black or 0)

            html = self._build_html(
                total_games=total_games,
                avg_accuracy=self._avg_list(accuracies),
                avg_elo=self._avg_list(elos),
                acpl_overall=self._avg_safe(acpl_overall_sum, acpl_overall_count),
                accuracy_series=accuracies,
                elo_series=elos,
                acpl_series=acpl_series,
                phase_totals=phase_totals,
                phase_games=phase_games,
                cpl_buckets=cpl_buckets,
                critical_faced=critical_faced,
                critical_solved=critical_solved,
                critical_failed=critical_failed,
                acpl_critical=self._avg_safe(acpl_critical_sum, acpl_critical_count),
                color_stats=color_stats,
            )
            self.html_view.setHtml(html)
        finally:
            session.close()

    def _init_phase_totals(self) -> Dict[str, Dict[str, float]]:
        return {
            "opening": {"blunders": 0, "mistakes": 0, "inaccuracies": 0, "total_moves": 0, "cpl_sum": 0, "cpl_count": 0},
            "middlegame": {"blunders": 0, "mistakes": 0, "inaccuracies": 0, "total_moves": 0, "cpl_sum": 0, "cpl_count": 0},
            "endgame": {"blunders": 0, "mistakes": 0, "inaccuracies": 0, "total_moves": 0, "cpl_sum": 0, "cpl_count": 0},
        }

    def _accumulate_phase(self, totals: Dict[str, float], data: Dict) -> None:
        totals["blunders"] += int(data.get("blunders", 0) or 0)
        totals["mistakes"] += int(data.get("mistakes", 0) or 0)
        totals["inaccuracies"] += int(data.get("inaccuracies", 0) or 0)
        totals["total_moves"] += int(data.get("total_moves", 0) or 0)
        totals["cpl_sum"] += float(data.get("cpl_sum", 0) or 0)
        totals["cpl_count"] += int(data.get("cpl_count", 0) or 0)

    def _avg_two(self, a: Optional[float], b: Optional[float]) -> Optional[float]:
        values = [v for v in (a, b) if v is not None]
        if not values:
            return None
        return sum(values) / len(values)

    def _avg_list(self, values) -> float:
        return sum(values) / len(values) if values else 0.0

    def _avg_safe(self, total: float, count: int) -> float:
        return total / count if count else 0.0

    def _per_game(self, total: int, games: int) -> float:
        return total / games if games else 0.0

    def _build_sparkline(self, values, title: str, color: str) -> str:
        if not values:
            return (
                "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 180 60' class='spark-svg'>"
                "<rect x='0' y='0' width='180' height='60' rx='10' fill='#0b1220'/>"
                f"<text x='10' y='20' fill='{self.SVG_TITLE_COLOR}' font-size='{self.SVG_TITLE_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>{title}</text>"
                f"<text x='10' y='40' fill='{self.SVG_DATA_COLOR}' font-size='{self.SVG_DATA_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>No data</text>"
                "</svg>"
            )

        max_val = max(values)
        min_val = min(values)
        span = max(max_val - min_val, 1e-6)
        points = []
        count = len(values)
        for idx, val in enumerate(values):
            x = 10 + (idx / max(1, count - 1)) * 160
            y = 45 - ((val - min_val) / span) * 28
            points.append(f"{x:.1f},{y:.1f}")
        polyline = " ".join(points)

        return (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 180 60' class='spark-svg'>"
            "<defs><linearGradient id='spark' x1='0' x2='1' y1='0' y2='0'>"
            f"<stop offset='0%' stop-color='{color}' stop-opacity='0.2'/>"
            f"<stop offset='100%' stop-color='{color}' stop-opacity='0.6'/>"
            "</linearGradient></defs>"
            "<rect x='0' y='0' width='180' height='60' rx='10' fill='#0b1220'/>"
            f"<text x='10' y='18' fill='{self.SVG_TITLE_COLOR}' font-size='{self.SVG_TITLE_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>{title}</text>"
            f"<polyline fill='none' stroke='{color}' stroke-width='2' points='{polyline}'/>"
            f"<polyline fill='url(#spark)' opacity='0.35' points='10,50 {polyline} 170,50'/>"
            "</svg>"
        )

    def _build_cpl_svg(self, cpl_buckets: Dict[str, int]) -> str:
        total = max(1, int(cpl_buckets.get("total", 0)))
        buckets = [
            ("0-20", int(cpl_buckets.get("0_20", 0))),
            ("20-50", int(cpl_buckets.get("20_50", 0))),
            ("50-100", int(cpl_buckets.get("50_100", 0))),
            ("100-200", int(cpl_buckets.get("100_200", 0))),
            ("200+", int(cpl_buckets.get("200_plus", 0))),
        ]
        max_pct = max((count / total) for _, count in buckets) if buckets else 0
        max_pct = max(max_pct, 0.01)

        bars = []
        labels = []
        for idx, (label, count) in enumerate(buckets):
            pct = (count / total) if total else 0
            height = int(90 * (pct / max_pct))
            x = 20 + idx * 68
            y = 110 - height
            bars.append(
                f"<rect x='{x}' y='{y}' width='34' height='{height}' rx='6' fill='#0ea5e9'></rect>"
            )
            labels.append(
                f"<text x='{x + 17}' y='130' text-anchor='middle' fill='{self.SVG_TITLE_COLOR}' font-size='{self.SVG_LABEL_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>{label}</text>"
            )
            labels.append(
                f"<text x='{x + 17}' y='{y - 6}' text-anchor='middle' fill='{self.SVG_DATA_COLOR}' font-size='{self.SVG_DATA_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>{pct * 100:.1f}%</text>"
            )

        return (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 380 140' class='chart-svg'>"
            "<rect x='0' y='0' width='380' height='140' rx='12' fill='#0b1220'/>"
            f"<text x='16' y='22' fill='{self.SVG_TITLE_COLOR}' font-size='{self.SVG_TITLE_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>CPL Distribution</text>"
            + "".join(bars)
            + "".join(labels)
            + "</svg>"
        )

    def _build_phase_svg(self, phase_totals: Dict[str, Dict[str, float]], phase_games: Dict[str, int]) -> str:
        phases = ["opening", "middlegame", "endgame"]
        phase_labels = {"opening": "Opening", "middlegame": "Middlegame", "endgame": "Endgame"}

        values = []
        for phase in phases:
            games = phase_games.get(phase, 0)
            blunders = self._per_game(int(phase_totals[phase]["blunders"]), games)
            mistakes = self._per_game(int(phase_totals[phase]["mistakes"]), games)
            inaccuracies = self._per_game(int(phase_totals[phase]["inaccuracies"]), games)
            values.append((blunders, mistakes, inaccuracies))

        max_val = max((sum(v) for v in values), default=1.0)
        max_val = max(max_val, 0.1)

        bars = []
        labels = []
        for idx, phase in enumerate(phases):
            blunders, mistakes, inaccuracies = values[idx]
            x = 40 + idx * 110
            y_base = 130

            b_height = int(80 * (blunders / max_val))
            m_height = int(80 * (mistakes / max_val))
            i_height = int(80 * (inaccuracies / max_val))

            y_b = y_base - b_height
            y_m = y_b - m_height
            y_i = y_m - i_height

            bars.append(f"<rect x='{x}' y='{y_b}' width='40' height='{b_height}' rx='6' fill='#ef4444'></rect>")
            bars.append(f"<rect x='{x}' y='{y_m}' width='40' height='{m_height}' rx='6' fill='#f59e0b'></rect>")
            bars.append(f"<rect x='{x}' y='{y_i}' width='40' height='{i_height}' rx='6' fill='#22c55e'></rect>")
            labels.append(
                f"<text x='{x + 20}' y='145' text-anchor='middle' fill='{self.SVG_TITLE_COLOR}' font-size='{self.SVG_LABEL_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>{phase_labels[phase]}</text>"
            )
            labels.append(
                f"<text x='{x + 20}' y='{y_i - 6}' text-anchor='middle' fill='{self.SVG_DATA_COLOR}' font-size='{self.SVG_DATA_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>{(blunders + mistakes + inaccuracies):.2f}</text>"
            )

        return (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 380 160' class='chart-svg'>"
            "<rect x='0' y='0' width='380' height='160' rx='12' fill='#0b1220'/>"
            f"<text x='16' y='22' fill='{self.SVG_TITLE_COLOR}' font-size='{self.SVG_TITLE_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>Errors per Game (Phase)</text>"
            f"<text x='16' y='38' fill='{self.SVG_MUTED_COLOR}' font-size='{self.SVG_DATA_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>Red=Blunders · Amber=Mistakes · Green=Inaccuracies</text>"
            + "".join(bars)
            + "".join(labels)
            + "</svg>"
        )

    def _build_critical_gauge(self, solved: int, faced: int) -> str:
        rate = (solved / faced) if faced else 0.0
        radius = 46
        circumference = 2 * 3.1416 * radius
        dash = circumference * rate
        gap = circumference - dash
        pct = rate * 100

        return (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 140 140' class='gauge-svg'>"
            "<circle cx='70' cy='70' r='52' fill='#0b1220'/>"
            "<circle cx='70' cy='70' r='46' fill='none' stroke='#1f2937' stroke-width='10'/>"
            f"<circle cx='70' cy='70' r='{radius}' fill='none' stroke='#38bdf8' stroke-width='10' stroke-dasharray='{dash:.1f} {gap:.1f}' stroke-linecap='round' transform='rotate(-90 70 70)'/>"
            f"<text x='70' y='72' text-anchor='middle' fill='#f8fafc' font-size='15' font-weight='700' font-family='{self.SVG_FONT_FAMILY}'>{pct:.1f}%</text>"
            f"<text x='70' y='92' text-anchor='middle' fill='{self.SVG_TITLE_COLOR}' font-size='{self.SVG_LABEL_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>Critical</text>"
            "</svg>"
        )

    def _build_color_bias_svg(self, color_stats: Dict[str, Dict[str, float]]) -> str:
        white_acpl = self._avg_safe(color_stats["white"]["acpl_sum"], int(color_stats["white"]["acpl_count"]))
        black_acpl = self._avg_safe(color_stats["black"]["acpl_sum"], int(color_stats["black"]["acpl_count"]))
        max_val = max(white_acpl, black_acpl, 1.0)
        bar_max = 64
        base_y = 102
        label_y = 124
        white_height = int(bar_max * (white_acpl / max_val))
        black_height = int(bar_max * (black_acpl / max_val))

        return (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 130' class='chart-svg'>"
            "<rect x='0' y='0' width='200' height='130' rx='12' fill='#0b1220'/>"
            f"<text x='14' y='18' fill='{self.SVG_TITLE_COLOR}' font-size='{self.SVG_TITLE_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>ACPL by Color</text>"
            f"<rect x='50' y='{base_y - white_height}' width='30' height='{white_height}' rx='6' fill='#38bdf8'></rect>"
            f"<rect x='120' y='{base_y - black_height}' width='30' height='{black_height}' rx='6' fill='#f97316'></rect>"
            f"<text x='65' y='{label_y}' text-anchor='middle' fill='{self.SVG_TITLE_COLOR}' font-size='{self.SVG_LABEL_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>White</text>"
            f"<text x='135' y='{label_y}' text-anchor='middle' fill='{self.SVG_TITLE_COLOR}' font-size='{self.SVG_LABEL_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>Black</text>"
            f"<text x='65' y='{base_y - white_height - 10}' text-anchor='middle' fill='{self.SVG_DATA_COLOR}' font-size='{self.SVG_DATA_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>{white_acpl:.1f}</text>"
            f"<text x='135' y='{base_y - black_height - 10}' text-anchor='middle' fill='{self.SVG_DATA_COLOR}' font-size='{self.SVG_DATA_SIZE}' font-family='{self.SVG_FONT_FAMILY}'>{black_acpl:.1f}</text>"
            "</svg>"
        )

    def _svg_to_data_uri(self, svg_markup: str) -> str:
        """Convert SVG markup to a data URI for reliable HTML rendering."""
        safe_svg = svg_markup.replace("\n", "").replace("\r", "")
        encoded = base64.b64encode(safe_svg.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    def _build_empty_state(self) -> str:
        return (
            "<html><body style='font-family: Trebuchet MS, Verdana, sans-serif; color: #1f2937;'>"
            "<div style='padding: 24px;'>"
            "<h2 style='margin: 0 0 8px 0;'>No analytics yet</h2>"
            "<p style='margin: 0;'>Analyze games to populate statistics.</p>"
            "</div></body></html>"
        )

    def _build_html(
        self,
        total_games: int,
        avg_accuracy: float,
        avg_elo: float,
        acpl_overall: float,
        accuracy_series,
        elo_series,
        acpl_series,
        phase_totals: Dict[str, Dict[str, float]],
        phase_games: Dict[str, int],
        cpl_buckets: Dict[str, int],
        critical_faced: int,
        critical_solved: int,
        critical_failed: int,
        acpl_critical: float,
        color_stats: Dict[str, Dict[str, float]],
    ) -> str:
        def fmt(num: float, digits: int = 1) -> str:
            return f"{num:.{digits}f}"

        def pct(part: int, whole: int) -> str:
            return fmt((part / whole) * 100, 1) if whole else "0.0"

        def phase_cpl(phase_key: str) -> float:
            totals = phase_totals[phase_key]
            return self._avg_safe(totals["cpl_sum"], int(totals["cpl_count"]))

        def per_game_phase(phase_key: str, key: str) -> float:
            totals = phase_totals[phase_key]
            return self._per_game(int(totals[key]), phase_games[phase_key])

        cpl_total = max(1, cpl_buckets.get("total", 0))

        cpl_img = self._svg_to_data_uri(self._build_cpl_svg(cpl_buckets))
        phase_img = self._svg_to_data_uri(self._build_phase_svg(phase_totals, phase_games))
        critical_img = self._svg_to_data_uri(self._build_critical_gauge(critical_solved, critical_faced))
        accuracy_img = self._svg_to_data_uri(self._build_sparkline(accuracy_series[-24:], "Accuracy", "#22c55e"))
        elo_img = self._svg_to_data_uri(self._build_sparkline(elo_series[-24:], "Elo", "#f97316"))
        acpl_img = self._svg_to_data_uri(self._build_sparkline(acpl_series[-24:], "ACPL", "#38bdf8"))
        color_bias_img = self._svg_to_data_uri(self._build_color_bias_svg(color_stats))

        css = """
            :root {
                --ink: #0f172a;
                --muted: #475569;
                --card: #ffffff;
                --line: #e2e8f0;
                --accent: #0ea5e9;
                --deep: #0b1220;
                --glow: rgba(14, 165, 233, 0.18);
                --bg: radial-gradient(circle at top left, #e2e8f0 0%, #f8fafc 42%, #f1f5f9 100%);
                --hero-bg: linear-gradient(135deg, #0b1220 0%, #1f2937 100%);
                --hero-text: #f8fafc;
                --hero-subtext: #cbd5f5;
            }
            @media (prefers-color-scheme: dark) {
                :root {
                    --ink: #e2e8f0;
                    --muted: #94a3b8;
                    --card: #0f172a;
                    --line: #1e293b;
                    --accent: #38bdf8;
                    --glow: rgba(14, 165, 233, 0.22);
                    --bg: radial-gradient(circle at top left, #0b1220 0%, #0f172a 45%, #111827 100%);
                    --hero-bg: linear-gradient(135deg, #111827 0%, #0b1220 100%);
                    --hero-text: #f8fafc;
                    --hero-subtext: #cbd5f5;
                }
            }
            body {
                font-family: "Segoe UI", "Trebuchet MS", Verdana, sans-serif;
                background: var(--bg);
                color: var(--ink);
                font-size: 13px;
                line-height: 1.45;
                letter-spacing: 0.1px;
            }
            .wrap {
                padding: 12px 8px 24px 8px;
            }
            .hero {
                background: var(--hero-bg);
                color: var(--hero-text);
                border-radius: 16px;
                padding: 20px 22px;
                margin-bottom: 18px;
                box-shadow: 0 20px 40px rgba(15, 23, 42, 0.25);
            }
            .hero h2 {
                margin: 0 0 6px 0;
                font-size: 22px;
                font-weight: 700;
            }
            .hero p {
                margin: 0;
                color: var(--hero-subtext);
                font-size: 12px;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 14px;
            }
            .card {
                background: var(--card);
                border-radius: 14px;
                padding: 14px 16px;
                border: 1px solid var(--line);
                box-shadow: 0 12px 26px rgba(15, 23, 42, 0.08);
            }
            .card h3 {
                margin: 0 0 6px 0;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                color: var(--muted);
            }
            .big {
                font-size: 21px;
                font-weight: 700;
                margin: 0;
            }
            .subtle {
                color: var(--muted);
                font-size: 11px;
            }
            .row {
                display: flex;
                justify-content: space-between;
                margin: 6px 0;
                font-size: 12px;
                gap: 12px;
            }
            .row span:last-child {
                text-align: right;
                font-weight: 600;
            }
            .bar {
                height: 8px;
                background: var(--line);
                border-radius: 8px;
                overflow: hidden;
            }
            .bar > span {
                display: block;
                height: 100%;
                background: var(--accent);
            }
            .tag {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 999px;
                font-size: 11px;
                background: var(--line);
                color: var(--ink);
                margin-left: 6px;
            }
            .section-title {
                margin: 18px 0 8px 0;
                font-size: 13px;
                color: var(--ink);
                font-weight: 600;
            }
            .split {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }
            .chart-row {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 14px;
                margin-bottom: 14px;
            }
            .spark-row {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin-bottom: 12px;
            }
            .chart-card {
                background: var(--card);
                border-radius: 16px;
                padding: 12px;
                border: 1px solid var(--line);
                box-shadow: 0 12px 30px var(--glow);
            }
            .chart-img {
                width: 100%;
                height: auto;
                display: block;
            }
            .chart-svg {
                width: 100%;
                height: auto;
            }
            .spark-svg {
                width: 100%;
                height: auto;
            }
            .svg-title {
                font-size: 12px;
                fill: #94a3b8;
                letter-spacing: 0.1em;
                text-transform: uppercase;
            }
            .svg-label {
                font-size: 10px;
                fill: #cbd5f5;
            }
            .svg-value {
                font-size: 10px;
                fill: #e2e8f0;
            }
            .svg-legend {
                font-size: 9px;
                fill: #64748b;
            }
            .gauge-svg {
                width: 100%;
                height: auto;
            }
            .gauge-value {
                font-size: 18px;
                fill: #f8fafc;
                font-weight: 700;
            }
            .gauge-label {
                font-size: 10px;
                fill: #94a3b8;
            }
        """

        html_template = Template(
            """
            <html>
            <head>
                <style>$css</style>
            </head>
            <body>
                <div class="wrap">
                    <div class="hero">
                        <h2>DCO Analytics Overview</h2>
                        <p>Backend metrics for training, performance, and reliability.</p>
                    </div>

                    <div class="grid">
                        <div class="card">
                            <h3>Games Analyzed</h3>
                            <p class="big">$total_games</p>
                            <p class="subtle">Range filter applied</p>
                        </div>
                        <div class="card">
                            <h3>Average ACPL</h3>
                            <p class="big">$acpl_overall</p>
                            <p class="subtle">Lower is better</p>
                        </div>
                        <div class="card">
                            <h3>Average Accuracy</h3>
                            <p class="big">$avg_accuracy</p>
                            <p class="subtle">From analysis results</p>
                        </div>
                        <div class="card">
                            <h3>Estimated Elo</h3>
                            <p class="big">$avg_elo</p>
                            <p class="subtle">Aggregate performance</p>
                        </div>
                    </div>

                    <h4 class="section-title">Performance Visuals</h4>
                    <div class="spark-row">
                        <div class="chart-card"><img class="chart-img" src="$accuracy_img" alt="Accuracy trend"/></div>
                        <div class="chart-card"><img class="chart-img" src="$elo_img" alt="Elo trend"/></div>
                        <div class="chart-card"><img class="chart-img" src="$acpl_img" alt="ACPL trend"/></div>
                    </div>
                    <div class="chart-row">
                        <div class="chart-card"><img class="chart-img" src="$phase_img" alt="Phase errors"/></div>
                        <div class="chart-card"><img class="chart-img" src="$critical_img" alt="Critical success"/></div>
                    </div>
                    <div class="chart-card"><img class="chart-img" src="$cpl_img" alt="CPL distribution"/></div>

                    <h4 class="section-title">Error Diagnostics by Phase</h4>
                    <div class="grid">
                        <div class="card">
                            <h3>Opening</h3>
                            <p class="big">$opening_acpl ACPL</p>
                            <div class="row"><span>Blunders/game</span><span>$opening_blunders</span></div>
                            <div class="row"><span>Mistakes/game</span><span>$opening_mistakes</span></div>
                            <div class="row"><span>Inaccuracies/game</span><span>$opening_inaccuracies</span></div>
                            <p class="subtle">Games with opening: $opening_games</p>
                        </div>
                        <div class="card">
                            <h3>Middlegame</h3>
                            <p class="big">$middlegame_acpl ACPL</p>
                            <div class="row"><span>Blunders/game</span><span>$middlegame_blunders</span></div>
                            <div class="row"><span>Mistakes/game</span><span>$middlegame_mistakes</span></div>
                            <div class="row"><span>Inaccuracies/game</span><span>$middlegame_inaccuracies</span></div>
                            <p class="subtle">Games with middlegame: $middlegame_games</p>
                        </div>
                        <div class="card">
                            <h3>Endgame</h3>
                            <p class="big">$endgame_acpl ACPL</p>
                            <div class="row"><span>Blunders/game</span><span>$endgame_blunders</span></div>
                            <div class="row"><span>Mistakes/game</span><span>$endgame_mistakes</span></div>
                            <div class="row"><span>Inaccuracies/game</span><span>$endgame_inaccuracies</span></div>
                            <p class="subtle">Games with endgame: $endgame_games</p>
                        </div>
                        <div class="card">
                            <h3>Critical Positions</h3>
                            <p class="big">$critical_rate%</p>
                            <div class="row"><span>Faced</span><span>$critical_faced</span></div>
                            <div class="row"><span>Solved</span><span>$critical_solved</span></div>
                            <div class="row"><span>Failed</span><span>$critical_failed</span></div>
                            <p class="subtle">ACPL in critical: $acpl_critical</p>
                        </div>
                    </div>

                    <h4 class="section-title">Color Bias</h4>
                    <div class="chart-card"><img class="chart-img" src="$color_bias_img" alt="Color bias"/></div>
                    <div class="split">
                        <div class="card">
                            <h3>White</h3>
                            <p class="big">$white_acpl ACPL</p>
                            <div class="row"><span>Blunders</span><span>$white_blunders</span></div>
                            <div class="row"><span>Mistakes</span><span>$white_mistakes</span></div>
                            <div class="row"><span>Inaccuracies</span><span>$white_inaccuracies</span></div>
                        </div>
                        <div class="card">
                            <h3>Black</h3>
                            <p class="big">$black_acpl ACPL</p>
                            <div class="row"><span>Blunders</span><span>$black_blunders</span></div>
                            <div class="row"><span>Mistakes</span><span>$black_mistakes</span></div>
                            <div class="row"><span>Inaccuracies</span><span>$black_inaccuracies</span></div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
        )

        values = {
            "css": css,
            "total_games": str(total_games),
            "acpl_overall": fmt(acpl_overall, 1),
            "avg_accuracy": f"{fmt(avg_accuracy, 1)}%",
            "avg_elo": fmt(avg_elo, 0),
            "accuracy_img": accuracy_img,
            "elo_img": elo_img,
            "acpl_img": acpl_img,
            "phase_img": phase_img,
            "critical_img": critical_img,
            "cpl_img": cpl_img,
            "opening_acpl": fmt(phase_cpl("opening"), 1),
            "opening_blunders": fmt(per_game_phase("opening", "blunders"), 2),
            "opening_mistakes": fmt(per_game_phase("opening", "mistakes"), 2),
            "opening_inaccuracies": fmt(per_game_phase("opening", "inaccuracies"), 2),
            "opening_games": str(phase_games["opening"]),
            "middlegame_acpl": fmt(phase_cpl("middlegame"), 1),
            "middlegame_blunders": fmt(per_game_phase("middlegame", "blunders"), 2),
            "middlegame_mistakes": fmt(per_game_phase("middlegame", "mistakes"), 2),
            "middlegame_inaccuracies": fmt(per_game_phase("middlegame", "inaccuracies"), 2),
            "middlegame_games": str(phase_games["middlegame"]),
            "endgame_acpl": fmt(phase_cpl("endgame"), 1),
            "endgame_blunders": fmt(per_game_phase("endgame", "blunders"), 2),
            "endgame_mistakes": fmt(per_game_phase("endgame", "mistakes"), 2),
            "endgame_inaccuracies": fmt(per_game_phase("endgame", "inaccuracies"), 2),
            "endgame_games": str(phase_games["endgame"]),
            "critical_rate": pct(critical_solved, critical_faced),
            "critical_faced": str(critical_faced),
            "critical_solved": str(critical_solved),
            "critical_failed": str(critical_failed),
            "acpl_critical": fmt(acpl_critical, 1),
            "color_bias_img": color_bias_img,
            "white_acpl": fmt(self._avg_safe(color_stats["white"]["acpl_sum"], int(color_stats["white"]["acpl_count"])), 1),
            "white_blunders": str(int(color_stats["white"]["blunders"])),
            "white_mistakes": str(int(color_stats["white"]["mistakes"])),
            "white_inaccuracies": str(int(color_stats["white"]["inaccuracies"])),
            "black_acpl": fmt(self._avg_safe(color_stats["black"]["acpl_sum"], int(color_stats["black"]["acpl_count"])), 1),
            "black_blunders": str(int(color_stats["black"]["blunders"])),
            "black_mistakes": str(int(color_stats["black"]["mistakes"])),
            "black_inaccuracies": str(int(color_stats["black"]["inaccuracies"])),
        }

        return html_template.substitute(values)
