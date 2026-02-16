"""
Import screen for importing PGN games.
"""

from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QCheckBox, QProgressBar, QLineEdit, QComboBox,
    QDateEdit, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread, Slot, QDate

from ...data.db import Database
from ...core.pgn_import import PGNImporter
from ...core.chesscom_import import fetch_chesscom_pgns


class ImportWorker(QThread):
    """Worker thread for importing PGN games."""
    
    finished = Signal(int, list)  # (count, errors)
    
    def __init__(self, db: Database, pgn_text: str, skip_duplicates: bool):
        super().__init__()
        self.db = db
        self.pgn_text = pgn_text
        self.skip_duplicates = skip_duplicates
    
    def run(self):
        """Run the import in a background thread."""
        session = self.db.get_session()
        try:
            importer = PGNImporter(session)
            imported, errors = importer.import_pgn_text(
                self.pgn_text, 
                self.skip_duplicates
            )
            self.finished.emit(len(imported), errors)
        except Exception as e:
            self.finished.emit(0, [str(e)])
        finally:
            session.close()


class ChessComImportWorker(QThread):
    """Worker thread for importing Chess.com games by username."""

    finished = Signal(int, list)  # (count, errors)

    def __init__(
        self,
        db: Database,
        username: str,
        start_date: datetime | None,
        end_date: datetime | None,
        skip_duplicates: bool
    ):
        super().__init__()
        self.db = db
        self.username = username
        self.start_date = start_date
        self.end_date = end_date
        self.skip_duplicates = skip_duplicates

    def run(self):
        """Run the Chess.com import in a background thread."""
        session = self.db.get_session()
        try:
            pgns, errors = fetch_chesscom_pgns(
                username=self.username,
                start_date=self.start_date,
                end_date=self.end_date
            )

            if not pgns:
                self.finished.emit(0, errors or ["No games found for that range."])
                return

            importer = PGNImporter(session)
            imported, import_errors = importer.import_pgn_text(
                "\n\n".join(pgns),
                self.skip_duplicates
            )
            errors.extend(import_errors)
            self.finished.emit(len(imported), errors)
        except Exception as e:
            self.finished.emit(0, [str(e)])
        finally:
            session.close()


class ImportScreen(QWidget):
    """Screen for importing PGN games."""
    
    import_completed = Signal(int)  # Signal emitted with number of games imported
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.import_worker = None
        self.chesscom_worker = None
        self.init_ui()
    
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
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Import Games")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #1f2937;")
        layout.addWidget(header)
        
        # Description
        desc = QLabel(
            "Import chess games from PGN format. You can paste PGN text below "
            "or import from a file."
        )
        desc.setStyleSheet("font-size: 14px; color: #6b7280;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.skip_duplicates_cb = QCheckBox("Skip duplicate games")
        self.skip_duplicates_cb.setChecked(True)
        self.skip_duplicates_cb.setStyleSheet("font-size: 14px; color: #1f2937;")
        options_layout.addWidget(self.skip_duplicates_cb)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)

        # Chess.com import section
        chesscom_frame = QFrame()
        chesscom_frame.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        chesscom_layout = QVBoxLayout(chesscom_frame)
        chesscom_layout.setContentsMargins(15, 15, 15, 15)
        chesscom_layout.setSpacing(10)

        chesscom_title = QLabel("Chess.com Username Import")
        chesscom_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        chesscom_layout.addWidget(chesscom_title)

        username_layout = QHBoxLayout()
        username_label = QLabel("Username")
        username_label.setStyleSheet("font-weight: bold;")
        username_layout.addWidget(username_label)

        self.chesscom_username_input = QLineEdit()
        self.chesscom_username_input.setPlaceholderText("e.g., hikaru")
        username_layout.addWidget(self.chesscom_username_input, 1)
        chesscom_layout.addLayout(username_layout)

        range_layout = QHBoxLayout()
        range_label = QLabel("Date Range")
        range_label.setStyleSheet("font-weight: bold;")
        range_layout.addWidget(range_label)

        self.chesscom_range_combo = QComboBox()
        self.chesscom_range_combo.addItems([
            "Last 30 days",
            "Last 90 days",
            "All time",
            "Custom"
        ])
        self.chesscom_range_combo.currentIndexChanged.connect(self._on_chesscom_range_changed)
        range_layout.addWidget(self.chesscom_range_combo)

        self.chesscom_start_date = QDateEdit()
        self.chesscom_start_date.setCalendarPopup(True)
        self.chesscom_start_date.setDisplayFormat("yyyy-MM-dd")
        self.chesscom_start_date.setEnabled(False)
        range_layout.addWidget(self.chesscom_start_date)

        self.chesscom_end_date = QDateEdit()
        self.chesscom_end_date.setCalendarPopup(True)
        self.chesscom_end_date.setDisplayFormat("yyyy-MM-dd")
        self.chesscom_end_date.setEnabled(False)
        range_layout.addWidget(self.chesscom_end_date)

        range_layout.addStretch()
        chesscom_layout.addLayout(range_layout)

        self.chesscom_import_btn = QPushButton("Import from Chess.com")
        self.chesscom_import_btn.setMinimumHeight(36)
        self.chesscom_import_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        self.chesscom_import_btn.clicked.connect(self._on_chesscom_import)
        chesscom_layout.addWidget(self.chesscom_import_btn, alignment=Qt.AlignLeft)

        layout.addWidget(chesscom_frame)
        
        # PGN text area
        pgn_label = QLabel("PGN Text:")
        pgn_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1f2937;")
        layout.addWidget(pgn_label)
        
        self.pgn_text = QTextEdit()
        self.pgn_text.setPlaceholderText(
            "Paste PGN text here...\n\n"
            "Example:\n"
            "[Event \"Casual Game\"]\n"
            "[Site \"Chess.com\"]\n"
            "[Date \"2026.02.15\"]\n"
            "[White \"Player1\"]\n"
            "[Black \"Player2\"]\n"
            "[Result \"1-0\"]\n\n"
            "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 ..."
        )
        self.pgn_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 10px;
                font-family: monospace;
                font-size: 12px;                color: #1f2937;
                background-color: white;            }
        """)
        layout.addWidget(self.pgn_text, 1)  # Stretch to fill space
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.import_file_btn = QPushButton("Import from File...")
        self.import_file_btn.setMinimumHeight(40)
        self.import_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.import_file_btn.clicked.connect(self._on_import_file)
        buttons_layout.addWidget(self.import_file_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6b7280;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)
        self.clear_btn.clicked.connect(self._on_clear)
        buttons_layout.addWidget(self.clear_btn)
        
        buttons_layout.addStretch()
        
        self.import_btn = QPushButton("Import Games")
        self.import_btn.setMinimumHeight(40)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
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
        self.import_btn.clicked.connect(self._on_import)
        buttons_layout.addWidget(self.import_btn)
        
        layout.addLayout(buttons_layout)

        today = datetime.utcnow().date()
        qtoday = QDate(today.year, today.month, today.day)
        self.chesscom_start_date.setDate(qtoday)
        self.chesscom_end_date.setDate(qtoday)
    
    def _on_import_file(self):
        """Handle import from file button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PGN File",
            "",
            "PGN Files (*.pgn);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    pgn_text = f.read()
                self.pgn_text.setPlainText(pgn_text)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to read file: {str(e)}"
                )
    
    def _on_clear(self):
        """Handle clear button click."""
        self.pgn_text.clear()
    
    def _on_import(self):
        """Handle import button click."""
        pgn_text = self.pgn_text.toPlainText().strip()
        
        if not pgn_text:
            QMessageBox.warning(
                self,
                "No PGN Text",
                "Please paste PGN text or import from a file."
            )
            return
        
        # Disable buttons and show progress
        self._set_busy(True)
        
        # Start import in background thread
        self.import_worker = ImportWorker(
            self.db,
            pgn_text,
            self.skip_duplicates_cb.isChecked()
        )
        self.import_worker.finished.connect(self._on_import_finished)
        self.import_worker.start()

    def _on_chesscom_import(self):
        """Handle Chess.com username import."""
        username = self.chesscom_username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Chess.com Import", "Please enter a username.")
            return

        start_date, end_date = self._get_chesscom_date_range()

        self._set_busy(True)
        self.chesscom_worker = ChessComImportWorker(
            self.db,
            username,
            start_date,
            end_date,
            self.skip_duplicates_cb.isChecked()
        )
        self.chesscom_worker.finished.connect(self._on_import_finished)
        self.chesscom_worker.start()
    
    @Slot(int, list)
    def _on_import_finished(self, count: int, errors: list):
        """Handle import completion."""
        # Re-enable buttons and hide progress
        self._set_busy(False)
        
        # Show result
        if count > 0:
            message = f"Successfully imported {count} game(s)."
            if errors:
                message += f"\n\n{len(errors)} issue(s) encountered:\n"
                message += "\n".join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    message += f"\n... and {len(errors) - 5} more"
            
            QMessageBox.information(self, "Import Complete", message)
            self.pgn_text.clear()
            
            # Emit signal
            self.import_completed.emit(count)
        else:
            error_msg = "Failed to import games."
            if errors:
                error_msg += "\n\nErrors:\n" + "\n".join(errors[:5])
            QMessageBox.critical(self, "Import Failed", error_msg)

    def _set_busy(self, busy: bool) -> None:
        """Toggle busy state for import actions."""
        enabled = not busy
        self.import_btn.setEnabled(enabled)
        self.import_file_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        self.chesscom_import_btn.setEnabled(enabled)
        self.progress_bar.setVisible(busy)
        if busy:
            self.progress_bar.setRange(0, 0)

    def _on_chesscom_range_changed(self) -> None:
        """Enable custom date fields when needed."""
        is_custom = self.chesscom_range_combo.currentText() == "Custom"
        self.chesscom_start_date.setEnabled(is_custom)
        self.chesscom_end_date.setEnabled(is_custom)

    def _get_chesscom_date_range(self) -> tuple[datetime | None, datetime | None]:
        """Return the date range for Chess.com import."""
        selection = self.chesscom_range_combo.currentText()
        now = datetime.utcnow()

        if selection == "Last 30 days":
            return now - timedelta(days=30), now
        if selection == "Last 90 days":
            return now - timedelta(days=90), now
        if selection == "All time":
            return None, None

        start_qdate = self.chesscom_start_date.date()
        end_qdate = self.chesscom_end_date.date()
        start = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
        end = datetime(end_qdate.year(), end_qdate.month(), end_qdate.day(), 23, 59, 59)
        if start > end:
            start, end = end, start
        return start, end
