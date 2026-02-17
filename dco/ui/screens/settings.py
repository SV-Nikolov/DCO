"""
Settings screen for configuring application preferences.
"""

import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QFormLayout, QSpinBox, QDoubleSpinBox,
    QCheckBox, QLineEdit, QComboBox, QGroupBox, QFileDialog,
    QMessageBox, QScrollArea, QColorDialog
)
from PySide6.QtCore import Qt, Signal, QCoreApplication
from PySide6.QtGui import QColor

from ...core.settings import get_settings
from ...data.db import Database


class SettingsScreen(QWidget):
    """Settings screen with tabs for different configuration categories."""
    
    settings_changed = Signal()  # Emitted when settings are saved
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.settings = get_settings()
        
        # Store current color values
        self.current_light_color = self.settings.get_board_light_color()
        self.current_dark_color = self.settings.get_board_dark_color()
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Settings")
        header.setObjectName("screenTitle")
        header.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(header)
        
        subtitle = QLabel("Configure application preferences")
        subtitle.setObjectName("mutedText")
        subtitle.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background: white;
                padding: 20px;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 2px;
                background: #f3f4f6;
                border: 1px solid #e5e7eb;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover {
                background: #e5e7eb;
            }
        """)
        
        # Create tabs
        self.tabs.addTab(self._create_engine_tab(), "Engine")
        self.tabs.addTab(self._create_analysis_tab(), "Analysis")
        self.tabs.addTab(self._create_practice_tab(), "Practice")
        self.tabs.addTab(self._create_appearance_tab(), "Appearance")
        self.tabs.addTab(self._create_general_tab(), "General")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        restart_btn = QPushButton("Restart Application")
        restart_btn.clicked.connect(self._on_restart)
        restart_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)
        button_layout.addWidget(restart_btn)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._on_reset)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        button_layout.addWidget(reset_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.load_settings)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4b5563;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._on_save)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _create_engine_tab(self) -> QWidget:
        """Create engine settings tab."""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # Engine path
        path_group = QGroupBox("Stockfish Engine")
        path_layout = QVBoxLayout()
        path_layout.setSpacing(10)
        path_layout.setContentsMargins(15, 15, 15, 15)
        
        path_info = QLabel("Specify a custom Stockfish engine path (leave empty for auto-detect)")
        path_info.setStyleSheet("color: #6b7280; font-size: 12px;")
        path_layout.addWidget(path_info)
        
        path_row = QHBoxLayout()
        self.engine_path_edit = QLineEdit()
        self.engine_path_edit.setPlaceholderText("Auto-detect")
        self.engine_path_edit.setMinimumWidth(400)
        path_row.addWidget(self.engine_path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_engine)
        browse_btn.setMinimumWidth(100)
        path_row.addWidget(browse_btn)
        
        path_layout.addLayout(path_row)
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # Engine performance
        perf_group = QGroupBox("Performance Settings")
        perf_form = QFormLayout()
        perf_form.setSpacing(15)
        perf_form.setContentsMargins(15, 15, 15, 15)
        
        self.engine_threads = QSpinBox()
        self.engine_threads.setRange(1, 16)
        self.engine_threads.setSuffix(" threads")
        self.engine_threads.setMinimumWidth(150)
        perf_form.addRow("CPU Threads:", self.engine_threads)
        
        self.engine_hash = QSpinBox()
        self.engine_hash.setRange(16, 4096)
        self.engine_hash.setSingleStep(16)
        self.engine_hash.setSuffix(" MB")
        self.engine_hash.setMinimumWidth(150)
        perf_form.addRow("Hash Table Size:", self.engine_hash)
        
        perf_group.setLayout(perf_form)
        layout.addWidget(perf_group)
        
        # Analysis configuration
        analysis_group = QGroupBox("Analysis Configuration")
        analysis_form = QFormLayout()
        analysis_form.setSpacing(15)
        analysis_form.setContentsMargins(15, 15, 15, 15)
        
        self.engine_depth = QSpinBox()
        self.engine_depth.setRange(10, 40)
        self.engine_depth.setSuffix(" plies")
        self.engine_depth.setMinimumWidth(150)
        analysis_form.addRow("Search Depth:", self.engine_depth)
        
        self.engine_time = QDoubleSpinBox()
        self.engine_time.setRange(0.1, 10.0)
        self.engine_time.setSingleStep(0.1)
        self.engine_time.setSuffix(" sec")
        self.engine_time.setDecimals(1)
        self.engine_time.setMinimumWidth(150)
        analysis_form.addRow("Time per Move:", self.engine_time)
        
        analysis_group.setLayout(analysis_form)
        layout.addWidget(analysis_group)
        
        layout.addStretch()
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(scroll)
        return container
    
    def _create_analysis_tab(self) -> QWidget:
        """Create analysis settings tab."""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # General analysis options
        general_group = QGroupBox("General Options")
        general_layout = QVBoxLayout()
        general_layout.setSpacing(10)
        general_layout.setContentsMargins(15, 15, 15, 15)
        
        self.auto_analyze = QCheckBox("Automatically analyze imported games")
        general_layout.addWidget(self.auto_analyze)
        
        self.add_to_practice = QCheckBox("Automatically add mistakes to practice database")
        general_layout.addWidget(self.add_to_practice)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Classification thresholds
        threshold_group = QGroupBox("Move Classification Thresholds")
        threshold_info = QLabel(
            "Centipawn loss thresholds for move classification.\n"
            "Moves are classified based on how much worse they are than the best move."
        )
        threshold_info.setStyleSheet("color: #6b7280; font-size: 12px; margin-bottom: 10px;")
        
        threshold_form = QFormLayout()
        threshold_form.setSpacing(15)
        threshold_form.setContentsMargins(15, 15, 15, 15)
        
        self.threshold_excellent = QSpinBox()
        self.threshold_excellent.setRange(5, 50)
        self.threshold_excellent.setSuffix(" cp loss")
        self.threshold_excellent.setMinimumWidth(150)
        threshold_form.addRow("Excellent (≤ X cp):", self.threshold_excellent)
        
        self.threshold_good = QSpinBox()
        self.threshold_good.setRange(20, 100)
        self.threshold_good.setSuffix(" cp loss")
        self.threshold_good.setMinimumWidth(150)
        threshold_form.addRow("Good (≤ X cp):", self.threshold_good)
        
        self.threshold_inaccuracy = QSpinBox()
        self.threshold_inaccuracy.setRange(50, 200)
        self.threshold_inaccuracy.setSuffix(" cp loss")
        self.threshold_inaccuracy.setMinimumWidth(150)
        threshold_form.addRow("Inaccuracy (≤ X cp):", self.threshold_inaccuracy)
        
        self.threshold_mistake = QSpinBox()
        self.threshold_mistake.setRange(100, 400)
        self.threshold_mistake.setSuffix(" cp loss")
        self.threshold_mistake.setMinimumWidth(150)
        threshold_form.addRow("Mistake (≤ X cp):", self.threshold_mistake)
        
        threshold_layout = QVBoxLayout()
        threshold_layout.addWidget(threshold_info)
        threshold_layout.addLayout(threshold_form)
        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)
        
        layout.addStretch()
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(scroll)
        return container
    
    def _create_practice_tab(self) -> QWidget:
        """Create practice settings tab."""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # Practice mode
        mode_group = QGroupBox("Practice Mode")
        mode_form = QFormLayout()
        mode_form.setSpacing(15)
        mode_form.setContentsMargins(15, 15, 15, 15)
        
        self.practice_difficulty = QComboBox()
        self.practice_difficulty.addItems(["lenient", "strict"])
        self.practice_difficulty.setMinimumWidth(150)
        mode_form.addRow("Difficulty:", self.practice_difficulty)
        
        self.practice_spaced_repetition = QCheckBox("Enable spaced repetition")
        mode_form.addRow("", self.practice_spaced_repetition)
        
        mode_group.setLayout(mode_form)
        layout.addWidget(mode_group)
        
        # Position configuration
        position_group = QGroupBox("Position Configuration")
        position_form = QFormLayout()
        position_form.setSpacing(15)
        position_form.setContentsMargins(15, 15, 15, 15)
        
        self.practice_offset = QSpinBox()
        self.practice_offset.setRange(1, 6)
        self.practice_offset.setSuffix(" plies before mistake")
        self.practice_offset.setMinimumWidth(200)
        position_form.addRow("Training Start Position:", self.practice_offset)
        
        self.practice_session_length = QSpinBox()
        self.practice_session_length.setRange(5, 50)
        self.practice_session_length.setSuffix(" positions")
        self.practice_session_length.setMinimumWidth(200)
        position_form.addRow("Default Session Length:", self.practice_session_length)
        
        position_group.setLayout(position_form)
        layout.addWidget(position_group)
        
        # Info panel
        info_label = QLabel(
            "<b>Difficulty Modes:</b><br/>"
            "<b>Lenient:</b> Accepts moves within ~30 cp of best move<br/>"
            "<b>Strict:</b> Only accepts the engine's best move<br/><br/>"
            "<b>Spaced Repetition:</b><br/>"
            "Automatically schedules practice positions based on your performance. "
            "Positions you struggle with appear more frequently."
        )
        info_label.setStyleSheet("""
            background: #f3f4f6;
            padding: 15px;
            border-radius: 6px;
            color: #374151;
            font-size: 12px;
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(scroll)
        return container
    
    def _create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab."""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # Theme
        theme_group = QGroupBox("Theme")
        theme_form = QFormLayout()
        theme_form.setSpacing(15)
        theme_form.setContentsMargins(15, 15, 15, 15)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setMinimumWidth(150)
        theme_form.addRow("UI Theme:", self.theme_combo)
        
        theme_note = QLabel("Note: Theme changes require restart")
        theme_note.setStyleSheet("color: #6b7280; font-size: 11px; font-style: italic;")
        theme_form.addRow("", theme_note)
        
        theme_group.setLayout(theme_form)
        layout.addWidget(theme_group)
        
        # Board appearance
        board_group = QGroupBox("Chess Board")
        board_layout = QVBoxLayout()
        board_layout.setSpacing(10)
        board_layout.setContentsMargins(15, 15, 15, 15)
        
        color_form = QFormLayout()
        color_form.setSpacing(15)
        
        # Light square color picker
        light_color_layout = QHBoxLayout()
        self.board_light_color = QPushButton()
        self.board_light_color.setMinimumWidth(150)
        self.board_light_color.setMinimumHeight(35)
        self.board_light_color.setCursor(Qt.PointingHandCursor)
        self.board_light_color.clicked.connect(lambda: self._pick_color('light'))
        light_color_layout.addWidget(self.board_light_color)
        light_color_layout.addStretch()
        color_form.addRow("Light Squares:", light_color_layout)
        
        # Dark square color picker
        dark_color_layout = QHBoxLayout()
        self.board_dark_color = QPushButton()
        self.board_dark_color.setMinimumWidth(150)
        self.board_dark_color.setMinimumHeight(35)
        self.board_dark_color.setCursor(Qt.PointingHandCursor)
        self.board_dark_color.clicked.connect(lambda: self._pick_color('dark'))
        dark_color_layout.addWidget(self.board_dark_color)
        dark_color_layout.addStretch()
        color_form.addRow("Dark Squares:", dark_color_layout)
        
        board_layout.addLayout(color_form)
        
        self.show_coordinates = QCheckBox("Show board coordinates (a-h, 1-8)")
        board_layout.addWidget(self.show_coordinates)
        
        board_group.setLayout(board_layout)
        layout.addWidget(board_group)
        
        layout.addStretch()
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(scroll)
        return container
    
    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        
        # User profile
        profile_group = QGroupBox("User Profile")
        profile_form = QFormLayout()
        profile_form.setSpacing(15)
        profile_form.setContentsMargins(15, 15, 15, 15)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Your Name")
        self.username_edit.setMinimumWidth(250)
        profile_form.addRow("Username:", self.username_edit)
        
        profile_group.setLayout(profile_form)
        layout.addWidget(profile_group)
        
        # Import preferences
        import_group = QGroupBox("Import Preferences")
        import_layout = QVBoxLayout()
        import_layout.setSpacing(10)
        import_layout.setContentsMargins(15, 15, 15, 15)
        
        self.auto_dedupe = QCheckBox("Automatically skip duplicate games when importing")
        import_layout.addWidget(self.auto_dedupe)
        
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # Default preferences
        defaults_group = QGroupBox("Defaults")
        defaults_form = QFormLayout()
        defaults_form.setSpacing(15)
        defaults_form.setContentsMargins(15, 15, 15, 15)
        
        self.default_time_control = QComboBox()
        self.default_time_control.addItems(["bullet", "blitz", "rapid"])
        self.default_time_control.setMinimumWidth(150)
        defaults_form.addRow("Default Time Control:", self.default_time_control)
        
        defaults_group.setLayout(defaults_form)
        layout.addWidget(defaults_group)
        
        layout.addStretch()
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(scroll)
        return container
    
    def _browse_engine(self):
        """Browse for Stockfish engine executable."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Stockfish Engine",
            "",
            "Executables (*.exe);;All Files (*.*)" if self.settings.settings.value("platform", "").startswith("win") else "All Files (*.*)"
        )
        if file_path:
            self.engine_path_edit.setText(file_path)
    
    def _pick_color(self, square_type: str):
        """Open color picker dialog for board squares."""
        if square_type == 'light':
            current_color = QColor(self.current_light_color)
            title = "Pick Light Square Color"
        else:
            current_color = QColor(self.current_dark_color)
            title = "Pick Dark Square Color"
        
        color = QColorDialog.getColor(current_color, self, title)
        
        if color.isValid():
            color_hex = color.name()
            if square_type == 'light':
                self.current_light_color = color_hex
                self._update_color_button(self.board_light_color, color_hex)
            else:
                self.current_dark_color = color_hex
                self._update_color_button(self.board_dark_color, color_hex)
    
    def _update_color_button(self, button: QPushButton, color_hex: str):
        """Update color button appearance."""
        # Calculate text color (black or white) based on background brightness
        color = QColor(color_hex)
        brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
        text_color = "#000000" if brightness > 128 else "#ffffff"
        
        button.setText(color_hex.upper())
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                color: {text_color};
                border: 2px solid #d1d5db;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border: 2px solid #9ca3af;
            }}
        """)
    
    def load_settings(self):
        """Load settings from storage into UI."""
        # Engine
        engine_path = self.settings.get_engine_path()
        self.engine_path_edit.setText(engine_path if engine_path else "")
        self.engine_threads.setValue(self.settings.get_engine_threads())
        self.engine_hash.setValue(self.settings.get_engine_hash())
        self.engine_depth.setValue(self.settings.get_engine_depth())
        self.engine_time.setValue(self.settings.get_engine_time())
        
        # Analysis
        self.auto_analyze.setChecked(self.settings.get_analysis_auto_analyze())
        self.add_to_practice.setChecked(self.settings.get_analysis_add_to_practice())
        self.threshold_excellent.setValue(self.settings.get_analysis_excellent_threshold())
        self.threshold_good.setValue(self.settings.get_analysis_good_threshold())
        self.threshold_inaccuracy.setValue(self.settings.get_analysis_inaccuracy_threshold())
        self.threshold_mistake.setValue(self.settings.get_analysis_mistake_threshold())
        
        # Practice
        self.practice_difficulty.setCurrentText(self.settings.get_practice_difficulty())
        self.practice_spaced_repetition.setChecked(self.settings.get_practice_spaced_repetition())
        self.practice_offset.setValue(self.settings.get_practice_offset_plies())
        self.practice_session_length.setValue(self.settings.get_practice_session_length())
        
        # Appearance
        self.theme_combo.setCurrentText(self.settings.get_theme())
        self.current_light_color = self.settings.get_board_light_color()
        self.current_dark_color = self.settings.get_board_dark_color()
        self._update_color_button(self.board_light_color, self.current_light_color)
        self._update_color_button(self.board_dark_color, self.current_dark_color)
        self.show_coordinates.setChecked(self.settings.get_show_coordinates())
        
        # General
        self.username_edit.setText(self.settings.get_username())
        self.auto_dedupe.setChecked(self.settings.get_import_auto_dedupe())
        self.default_time_control.setCurrentText(self.settings.get_default_time_control())
    
    def _on_save(self):
        """Save UI settings to storage."""
        # Engine
        path = self.engine_path_edit.text().strip()
        self.settings.set_engine_path(path if path else None)
        self.settings.set_engine_threads(self.engine_threads.value())
        self.settings.set_engine_hash(self.engine_hash.value())
        self.settings.set_engine_depth(self.engine_depth.value())
        self.settings.set_engine_time(self.engine_time.value())
        
        # Analysis
        self.settings.set_analysis_auto_analyze(self.auto_analyze.isChecked())
        self.settings.set_analysis_add_to_practice(self.add_to_practice.isChecked())
        self.settings.set_analysis_excellent_threshold(self.threshold_excellent.value())
        self.settings.set_analysis_good_threshold(self.threshold_good.value())
        self.settings.set_analysis_inaccuracy_threshold(self.threshold_inaccuracy.value())
        self.settings.set_analysis_mistake_threshold(self.threshold_mistake.value())
        
        # Practice
        self.settings.set_practice_difficulty(self.practice_difficulty.currentText())
        self.settings.set_practice_spaced_repetition(self.practice_spaced_repetition.isChecked())
        self.settings.set_practice_offset_plies(self.practice_offset.value())
        self.settings.set_practice_session_length(self.practice_session_length.value())
        
        # Appearance
        self.settings.set_theme(self.theme_combo.currentText())
        self.settings.set_board_light_color(self.current_light_color)
        self.settings.set_board_dark_color(self.current_dark_color)
        self.settings.set_show_coordinates(self.show_coordinates.isChecked())
        
        # General
        self.settings.set_username(self.username_edit.text().strip() or "You")
        self.settings.set_import_auto_dedupe(self.auto_dedupe.isChecked())
        self.settings.set_default_time_control(self.default_time_control.currentText())
        
        # Sync to disk
        self.settings.sync()
        
        # Show confirmation
        message = "Your settings have been saved successfully."
        message += "\\n\\nTheme and board color changes will take effect when you restart the application or open a new board."
        
        QMessageBox.information(
            self,
            "Settings Saved",
            message
        )
        
        self.settings_changed.emit()
    
    def _on_reset(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings.reset_all()
            self.load_settings()
            QMessageBox.information(
                self,
                "Settings Reset",
                "All settings have been reset to default values."
            )
    
    def _on_restart(self):
        """Restart the application to apply settings changes."""
        reply = QMessageBox.question(
            self,
            "Restart Application",
            "Do you want to restart DCO now to apply all settings?\n\n"
            "Make sure to save any unsaved changes before restarting.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QCoreApplication.quit()
            python = sys.executable
            os.execl(python, python, *sys.argv)
