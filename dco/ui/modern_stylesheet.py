"""
Modern Chess Analyst Qt Stylesheet - Clean Light Theme

A professional, clean light theme inspired by modern applications like Notion and Linear.
Optimized for readability and visual hierarchy.

Usage:
    app.setStyleSheet(load_stylesheet())
    
Color Palette:
- Primary: #2563eb (Blue)
- Background: #ffffff (White)
- Surface: #f8fafc (Light Gray)
- Border: #e2e8f0 (Soft Gray)
- Text Primary: #1e293b (Dark Slate)
- Text Secondary: #64748b (Muted Slate)
"""

STYLESHEET = """
/* =================================================================
   CLEAN LIGHT THEME - DCO Chess Analyst
   ================================================================= */
   
* {
    margin: 0;
    padding: 0;
}

QWidget {
    background-color: #ffffff;
    color: #1e293b;
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 14px;
}

/* =================================================================
   MAIN WINDOW & FRAMES
   ================================================================= */

QMainWindow {
    background-color: #f8fafc;
}

QFrame {
    background-color: transparent;
    border: none;
}

QFrame#navWidget {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
}

QFrame#headerFrame {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
}

QFrame#contentFrame {
    background-color: #f8fafc;
}

/* =================================================================
   BUTTONS & NAVIGATION
   ================================================================= */

QPushButton {
    background-color: transparent;
    color: #64748b;
    border: none;
    padding: 10px 16px;
    border-radius: 6px;
    font-weight: 500;
    text-align: left;
}

QPushButton:hover {
    background-color: #f1f5f9;
    color: #1e293b;
}

QPushButton:pressed {
    background-color: #e2e8f0;
}

QPushButton:checked {
    background-color: #eff6ff;
    color: #2563eb;
    border-left: 3px solid #2563eb;
    padding-left: 13px;
}

QPushButton#primaryButton {
    background-color: #2563eb;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background-color: #1d4ed8;
}

QPushButton#primaryButton:pressed {
    background-color: #1e40af;
}

QPushButton#secondaryButton {
    background-color: #f1f5f9;
    color: #475569;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 500;
}

QPushButton#secondaryButton:hover {
    background-color: #e2e8f0;
    border-color: #cbd5e1;
}

QPushButton#successButton {
    background-color: #10b981;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
}

QPushButton#successButton:hover {
    background-color: #059669;
}

/* =================================================================
   LABELS & TEXT
   ================================================================= */

QLabel {
    color: #1e293b;
    background-color: transparent;
}

QLabel#screenTitle {
    font-size: 24px;
    font-weight: 700;
    color: #0f172a;
}

QLabel#cardTitle {
    font-size: 16px;
    font-weight: 600;
    color: #1e293b;
}

QLabel#sectionTitle {
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
}

QLabel#statValue {
    font-size: 32px;
    font-weight: 700;
    color: #2563eb;
}

QLabel#statLabel {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
    letter-spacing: 0.5px;
}

QLabel#mutedText {
    color: #94a3b8;
}

QLabel#versionLabel {
    color: #94a3b8;
    padding: 10px 20px;
    font-size: 11px;
}

QLabel#placeholderText {
    font-size: 16px;
    color: #94a3b8;
}

/* =================================================================
   INPUT FIELDS & COMBO BOXES
   ================================================================= */

QLineEdit,
QTextEdit,
QPlainTextEdit {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 12px;
    selection-background-color: #dbeafe;
    selection-color: #1e293b;
}

QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus {
    border: 2px solid #2563eb;
    background-color: #ffffff;
    padding: 9px 11px;
}

QLineEdit::placeholder {
    color: #94a3b8;
}

QComboBox {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: #dbeafe;
}

QComboBox:hover {
    border: 1px solid #cbd5e1;
}

QComboBox:focus {
    border: 2px solid #2563eb;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

/* =================================================================
   SCROLL BARS
   ================================================================= */

QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #cbd5e1;
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94a3b8;
}

QScrollBar::sub-line:vertical,
QScrollBar::add-line:vertical {
    border: none;
    background: none;
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #cbd5e1;
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #94a3b8;
}

QScrollBar::sub-line:horizontal,
QScrollBar::add-line:horizontal {
    border: none;
    background: none;
    width: 0;
}

/* =================================================================
   MENUS & CONTEXT
   ================================================================= */

QMenuBar {
    background-color: #ffffff;
    color: #1e293b;
    border-bottom: 1px solid #e2e8f0;
    padding: 4px;
}

QMenuBar::item:selected {
    background-color: #f1f5f9;
    border-radius: 4px;
}

QMenu {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 32px 8px 16px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #f1f5f9;
}

/* =================================================================
   TABS
   ================================================================= */

QTabBar::tab {
    background-color: transparent;
    color: #64748b;
    border: none;
    padding: 10px 20px;
    margin-right: 4px;
    border-radius: 6px;
}

QTabBar::tab:hover {
    background-color: #f1f5f9;
}

QTabBar::tab:selected {
    background-color: #eff6ff;
    color: #2563eb;
    font-weight: 600;
}

QTabWidget::pane {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background-color: #ffffff;
}

/* =================================================================
   TREE & TABLE WIDGETS
   ================================================================= */

QTreeWidget,
QTableWidget,
QListWidget {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    gridline-color: #f1f5f9;
    alternate-background-color: #f8fafc;
}

QTreeWidget::item,
QTableWidget::item,
QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QTreeWidget::item:hover,
QTableWidget::item:hover,
QListWidget::item:hover {
    background-color: #f8fafc;
}

QTreeWidget::item:selected,
QTableWidget::item:selected,
QListWidget::item:selected {
    background-color: #eff6ff;
    color: #1e293b;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #64748b;
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid #e2e8f0;
    font-weight: 600;
    font-size: 12px;
}

QHeaderView::section:hover {
    background-color: #f1f5f9;
}

/* =================================================================
   PROGRESS BAR
   ================================================================= */

QProgressBar {
    background-color: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    height: 8px;
    text-align: center;
    color: #64748b;
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 6px;
}

/* =================================================================
   SLIDERS
   ================================================================= */

QSlider::groove:horizontal {
    background-color: #e2e8f0;
    border-radius: 4px;
    height: 6px;
}

QSlider::handle:horizontal {
    background-color: #2563eb;
    border: 2px solid #ffffff;
    border-radius: 8px;
    width: 16px;
    margin: -6px 0;
}

QSlider::handle:horizontal:hover {
    background-color: #1d4ed8;
}

QSlider::sub-page:horizontal {
    background-color: #2563eb;
    border-radius: 4px;
}

/* =================================================================
   DIALOGS & MESSAGE BOXES
   ================================================================= */

QDialog {
    background-color: #ffffff;
}

QMessageBox {
    background-color: #ffffff;
}

QMessageBox QLabel {
    color: #1e293b;
}

QMessageBox QPushButton {
    min-width: 80px;
    min-height: 36px;
}

QFileDialog {
    background-color: #ffffff;
}

/* =================================================================
   SPINBOX & CHECKBOXES
   ================================================================= */

QSpinBox,
QDoubleSpinBox {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 12px;
}

QSpinBox:focus,
QDoubleSpinBox:focus {
    border: 2px solid #2563eb;
}

QSpinBox::up-button,
QSpinBox::down-button,
QDoubleSpinBox::up-button,
QDoubleSpinBox::down-button {
    background-color: transparent;
    border: none;
    width: 20px;
}

QCheckBox {
    color: #1e293b;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #cbd5e1;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #2563eb;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
    image: url(none);
}

/* =================================================================
   TOOLTIPS
   ================================================================= */

QToolTip {
    background-color: #1e293b;
    color: #ffffff;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
}

/* =================================================================
   STATUS BAR
   ================================================================= */

QStatusBar {
    background-color: #f8fafc;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
}

QStatusBar::item {
    border: none;
}

/* =================================================================
   CUSTOM CARDS/FRAMES
   ================================================================= */

QFrame#cardFrame {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}

QFrame#statCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
}

/* =================================================================
   DOCK WIDGETS
   ================================================================= */

QDockWidget {
    background-color: #ffffff;
    color: #1e293b;
}

QDockWidget::title {
    background-color: #f8fafc;
    padding: 10px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
}

/* =================================================================
   FOCUS OUTLINE (REMOVE DEFAULT)
   ================================================================= */

*:focus {
    outline: none;
}
"""

def load_stylesheet() -> str:
    """Load and return the DCO clean light stylesheet."""
    return STYLESHEET


# Example usage in main application:
if __name__ == "__main__":
    # from PySide6.QtWidgets import QApplication
    # app = QApplication([])
    # app.setStyleSheet(load_stylesheet())
    print("DCO Clean Light Stylesheet Loaded")
    print(f"Total lines: {len(STYLESHEET.splitlines())}")
