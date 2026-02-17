"""
Statistics dashboard screen for DCO.
Displays backend analytics using an HTML/CSS layout.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QDateEdit, QFrame, QTextBrowser
)

from ...data.db import Database
from ...data.models import Game, Analysis, GameAnalytics


class StatisticsScreen(QWidget):
    """Statistics dashboard screen."""

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

        self.html_view = QTextBrowser()
        self.html_view.setOpenExternalLinks(True)
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
                f"<text x='{x + 17}' y='130' text-anchor='middle' class='svg-label'>{label}</text>"
            )
            labels.append(
                f"<text x='{x + 17}' y='{y - 6}' text-anchor='middle' class='svg-value'>{pct * 100:.1f}%</text>"
            )

        return (
            "<svg viewBox='0 0 380 140' class='chart-svg'>"
            "<rect x='0' y='0' width='380' height='140' rx='12' fill='#0b1220'/>"
            "<text x='16' y='22' class='svg-title'>CPL Distribution</text>"
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
            labels.append(f"<text x='{x + 20}' y='145' text-anchor='middle' class='svg-label'>{phase_labels[phase]}</text>")
            labels.append(
                f"<text x='{x + 20}' y='{y_i - 6}' text-anchor='middle' class='svg-value'>{(blunders + mistakes + inaccuracies):.2f}</text>"
            )

        return (
            "<svg viewBox='0 0 380 160' class='chart-svg'>"
            "<rect x='0' y='0' width='380' height='160' rx='12' fill='#0b1220'/>"
            "<text x='16' y='22' class='svg-title'>Errors per Game (Phase)</text>"
            "<text x='260' y='22' class='svg-legend'>Red=Blunders · Amber=Mistakes · Green=Inaccuracies</text>"
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
            "<svg viewBox='0 0 140 140' class='gauge-svg'>"
            "<circle cx='70' cy='70' r='52' fill='#0b1220'/>"
            "<circle cx='70' cy='70' r='46' fill='none' stroke='#1f2937' stroke-width='10'/>"
            f"<circle cx='70' cy='70' r='{radius}' fill='none' stroke='#38bdf8' stroke-width='10' stroke-dasharray='{dash:.1f} {gap:.1f}' stroke-linecap='round' transform='rotate(-90 70 70)'/>"
            f"<text x='70' y='72' text-anchor='middle' class='gauge-value'>{pct:.1f}%</text>"
            "<text x='70' y='92' text-anchor='middle' class='gauge-label'>Critical</text>"
            "</svg>"
        )

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

        cpl_svg = self._build_cpl_svg(cpl_buckets)
        phase_svg = self._build_phase_svg(phase_totals, phase_games)
        critical_svg = self._build_critical_gauge(critical_solved, critical_faced)

        html = f"""
        <html>
        <head>
            <style>
                :root {{
                    --ink: #0f172a;
                    --muted: #64748b;
                    --card: #ffffff;
                    --line: #e2e8f0;
                    --accent: #38bdf8;
                    --deep: #0b1220;
                    --glow: rgba(14, 165, 233, 0.15);
                }}
                body {{
                    font-family: Trebuchet MS, Verdana, sans-serif;
                    background: radial-gradient(circle at top left, #e2e8f0 0%, #f8fafc 42%, #f1f5f9 100%);
                    color: var(--ink);
                }}
                .wrap {{
                    padding: 12px 8px 24px 8px;
                }}
                .hero {{
                    background: linear-gradient(135deg, #0b1220 0%, #1f2937 100%);
                    color: #f8fafc;
                    border-radius: 16px;
                    padding: 20px 22px;
                    margin-bottom: 18px;
                    box-shadow: 0 20px 40px rgba(15, 23, 42, 0.25);
                }}
                .hero h2 {{
                    margin: 0 0 6px 0;
                    font-size: 22px;
                }}
                .hero p {{
                    margin: 0;
                    color: #cbd5f5;
                }}
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 14px;
                }}
                .card {{
                    background: var(--card);
                    border-radius: 14px;
                    padding: 14px 16px;
                    border: 1px solid var(--line);
                    box-shadow: 0 12px 26px rgba(15, 23, 42, 0.08);
                }}
                .card h3 {{
                    margin: 0 0 6px 0;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    color: var(--muted);
                }}
                .big {{
                    font-size: 26px;
                    font-weight: 700;
                    margin: 0;
                }}
                .subtle {{
                    color: var(--muted);
                    font-size: 12px;
                }}
                .row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 6px 0;
                    font-size: 13px;
                }}
                .bar {{
                    height: 8px;
                    background: var(--line);
                    border-radius: 8px;
                    overflow: hidden;
                }}
                .bar > span {{
                    display: block;
                    height: 100%;
                    background: var(--accent);
                }}
                .tag {{
                    display: inline-block;
                    padding: 2px 8px;
                    border-radius: 999px;
                    font-size: 11px;
                    background: var(--line);
                    color: var(--ink);
                    margin-left: 6px;
                }}
                .section-title {{
                    margin: 18px 0 8px 0;
                    font-size: 15px;
                    color: var(--ink);
                }}
                .split {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 12px;
                }}
                .chart-row {{
                    display: grid;
                    grid-template-columns: 2fr 1fr;
                    gap: 14px;
                    margin-bottom: 14px;
                }}
                .chart-card {{
                    background: var(--card);
                    border-radius: 16px;
                    padding: 12px;
                    border: 1px solid var(--line);
                    box-shadow: 0 12px 30px var(--glow);
                }}
                .chart-svg {{
                    width: 100%;
                    height: auto;
                }}
                .svg-title {{
                    font-size: 12px;
                    fill: #94a3b8;
                    letter-spacing: 0.1em;
                    text-transform: uppercase;
                }}
                .svg-label {{
                    font-size: 10px;
                    fill: #cbd5f5;
                }}
                .svg-value {{
                    font-size: 10px;
                    fill: #e2e8f0;
                }}
                .svg-legend {{
                    font-size: 9px;
                    fill: #64748b;
                }}
                .gauge-svg {{
                    width: 100%;
                    height: auto;
                }}
                .gauge-value {{
                    font-size: 18px;
                    fill: #f8fafc;
                    font-weight: 700;
                }}
                .gauge-label {{
                    font-size: 10px;
                    fill: #94a3b8;
                }}
            </style>
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
                        <p class="big">{total_games}</p>
                        <p class="subtle">Range filter applied</p>
                    </div>
                    <div class="card">
                        <h3>Average ACPL</h3>
                        <p class="big">{fmt(acpl_overall, 1)}</p>
                        <p class="subtle">Lower is better</p>
                    </div>
                    <div class="card">
                        <h3>Average Accuracy</h3>
                        <p class="big">{fmt(avg_accuracy, 1)}%</p>
                        <p class="subtle">From analysis results</p>
                    </div>
                    <div class="card">
                        <h3>Estimated Elo</h3>
                        <p class="big">{fmt(avg_elo, 0)}</p>
                        <p class="subtle">Aggregate performance</p>
                    </div>
                </div>

                <h4 class="section-title">Performance Visuals</h4>
                <div class="chart-row">
                    <div class="chart-card">{phase_svg}</div>
                    <div class="chart-card">{critical_svg}</div>
                </div>
                <div class="chart-card">{cpl_svg}</div>

                <h4 class="section-title">Error Diagnostics by Phase</h4>
                <div class="grid">
                    <div class="card">
                        <h3>Opening</h3>
                        <p class="big">{fmt(phase_cpl("opening"), 1)} ACPL</p>
                        <div class="row"><span>Blunders/game</span><span>{fmt(per_game_phase("opening", "blunders"), 2)}</span></div>
                        <div class="row"><span>Mistakes/game</span><span>{fmt(per_game_phase("opening", "mistakes"), 2)}</span></div>
                        <div class="row"><span>Inaccuracies/game</span><span>{fmt(per_game_phase("opening", "inaccuracies"), 2)}</span></div>
                        <p class="subtle">Games with opening: {phase_games["opening"]}</p>
                    </div>
                    <div class="card">
                        <h3>Middlegame</h3>
                        <p class="big">{fmt(phase_cpl("middlegame"), 1)} ACPL</p>
                        <div class="row"><span>Blunders/game</span><span>{fmt(per_game_phase("middlegame", "blunders"), 2)}</span></div>
                        <div class="row"><span>Mistakes/game</span><span>{fmt(per_game_phase("middlegame", "mistakes"), 2)}</span></div>
                        <div class="row"><span>Inaccuracies/game</span><span>{fmt(per_game_phase("middlegame", "inaccuracies"), 2)}</span></div>
                        <p class="subtle">Games with middlegame: {phase_games["middlegame"]}</p>
                    </div>
                    <div class="card">
                        <h3>Endgame</h3>
                        <p class="big">{fmt(phase_cpl("endgame"), 1)} ACPL</p>
                        <div class="row"><span>Blunders/game</span><span>{fmt(per_game_phase("endgame", "blunders"), 2)}</span></div>
                        <div class="row"><span>Mistakes/game</span><span>{fmt(per_game_phase("endgame", "mistakes"), 2)}</span></div>
                        <div class="row"><span>Inaccuracies/game</span><span>{fmt(per_game_phase("endgame", "inaccuracies"), 2)}</span></div>
                        <p class="subtle">Games with endgame: {phase_games["endgame"]}</p>
                    </div>
                    <div class="card">
                        <h3>Critical Positions</h3>
                        <p class="big">{pct(critical_solved, critical_faced)}%</p>
                        <div class="row"><span>Faced</span><span>{critical_faced}</span></div>
                        <div class="row"><span>Solved</span><span>{critical_solved}</span></div>
                        <div class="row"><span>Failed</span><span>{critical_failed}</span></div>
                        <p class="subtle">ACPL in critical: {fmt(acpl_critical, 1)}</p>
                    </div>
                </div>

                <h4 class="section-title">Color Bias</h4>
                <div class="split">
                    <div class="card">
                        <h3>White</h3>
                        <p class="big">{fmt(self._avg_safe(color_stats["white"]["acpl_sum"], int(color_stats["white"]["acpl_count"])), 1)} ACPL</p>
                        <div class="row"><span>Blunders</span><span>{int(color_stats["white"]["blunders"])}</span></div>
                        <div class="row"><span>Mistakes</span><span>{int(color_stats["white"]["mistakes"])}</span></div>
                        <div class="row"><span>Inaccuracies</span><span>{int(color_stats["white"]["inaccuracies"])}</span></div>
                    </div>
                    <div class="card">
                        <h3>Black</h3>
                        <p class="big">{fmt(self._avg_safe(color_stats["black"]["acpl_sum"], int(color_stats["black"]["acpl_count"])), 1)} ACPL</p>
                        <div class="row"><span>Blunders</span><span>{int(color_stats["black"]["blunders"])}</span></div>
                        <div class="row"><span>Mistakes</span><span>{int(color_stats["black"]["mistakes"])}</span></div>
                        <div class="row"><span>Inaccuracies</span><span>{int(color_stats["black"]["inaccuracies"])}</span></div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return html
