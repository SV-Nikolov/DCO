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

        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Trebuchet MS, Verdana, sans-serif;
                    background: #f8fafc;
                    color: #0f172a;
                }}
                .wrap {{
                    padding: 12px 8px 24px 8px;
                }}
                .hero {{
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    color: #f8fafc;
                    border-radius: 16px;
                    padding: 20px 22px;
                    margin-bottom: 18px;
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
                    background: #ffffff;
                    border-radius: 14px;
                    padding: 14px 16px;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
                }}
                .card h3 {{
                    margin: 0 0 6px 0;
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    color: #64748b;
                }}
                .big {{
                    font-size: 26px;
                    font-weight: 700;
                    margin: 0;
                }}
                .subtle {{
                    color: #64748b;
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
                    background: #e2e8f0;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                .bar > span {{
                    display: block;
                    height: 100%;
                    background: #0ea5e9;
                }}
                .tag {{
                    display: inline-block;
                    padding: 2px 8px;
                    border-radius: 999px;
                    font-size: 11px;
                    background: #e2e8f0;
                    color: #0f172a;
                    margin-left: 6px;
                }}
                .section-title {{
                    margin: 18px 0 8px 0;
                    font-size: 15px;
                    color: #0f172a;
                }}
                .split {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 12px;
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

                <h4 class="section-title">CPL Distribution</h4>
                <div class="card">
                    <div class="row"><span>0-20</span><span>{pct(cpl_buckets["0_20"], cpl_total)}%</span></div>
                    <div class="bar"><span style="width: {pct(cpl_buckets["0_20"], cpl_total)}%"></span></div>
                    <div class="row"><span>20-50</span><span>{pct(cpl_buckets["20_50"], cpl_total)}%</span></div>
                    <div class="bar"><span style="width: {pct(cpl_buckets["20_50"], cpl_total)}%"></span></div>
                    <div class="row"><span>50-100</span><span>{pct(cpl_buckets["50_100"], cpl_total)}%</span></div>
                    <div class="bar"><span style="width: {pct(cpl_buckets["50_100"], cpl_total)}%"></span></div>
                    <div class="row"><span>100-200</span><span>{pct(cpl_buckets["100_200"], cpl_total)}%</span></div>
                    <div class="bar"><span style="width: {pct(cpl_buckets["100_200"], cpl_total)}%"></span></div>
                    <div class="row"><span>200+</span><span>{pct(cpl_buckets["200_plus"], cpl_total)}%</span></div>
                    <div class="bar"><span style="width: {pct(cpl_buckets["200_plus"], cpl_total)}%"></span></div>
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
