"""
Import screen for importing PGN games.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QCheckBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread, Slot

from ...data.db import Database
from ...core.pgn_import import PGNImporter


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


class ImportScreen(QWidget):
    """Screen for importing PGN games."""
    
    import_completed = Signal(int)  # Signal emitted with number of games imported
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.import_worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
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
        self.skip_duplicates_cb.setStyleSheet("font-size: 14px;")
        options_layout.addWidget(self.skip_duplicates_cb)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
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
                font-size: 12px;
            }
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
        self.import_btn.setEnabled(False)
        self.import_file_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Start import in background thread
        self.import_worker = ImportWorker(
            self.db,
            pgn_text,
            self.skip_duplicates_cb.isChecked()
        )
        self.import_worker.finished.connect(self._on_import_finished)
        self.import_worker.start()
    
    @Slot(int, list)
    def _on_import_finished(self, count: int, errors: list):
        """Handle import completion."""
        # Re-enable buttons and hide progress
        self.import_btn.setEnabled(True)
        self.import_file_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
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
