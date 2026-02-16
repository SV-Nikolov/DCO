"""
Modern Chess Analyst Qt Stylesheet

This stylesheet provides a modern, professional appearance for the DCO application
using a chess-inspired color scheme with smooth gradients and professional typography.

Usage:
    app.setStyleSheet(load_stylesheet())
    
Color Palette:
- Primary: #2563eb (Blue)
- Dark Background: #0f172a (Dark Navy)
- Card Background: #1e293b (Darker Navy)
- Text Primary: #f1f5f9 (Light Gray)
- Text Muted: #94a3b8 (Medium Gray)
"""

STYLESHEET = """
/* =================================================================
   GLOBAL STYLESHEET - DCO Chess Analyst
   ================================================================= */
   
* {
    margin: 0;
    padding: 0;
}

QWidget {
    background-color: #0f172a;
    color: #f1f5f9;
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}

/* =================================================================
   MAIN WINDOW & FRAMES
   ================================================================= */

QMainWindow {
    background-color: #0f172a;
}

QFrame {
    background-color: #0f172a;
    border: none;
}

QFrame#navWidget {
    background-color: #020617;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}

QFrame#headerFrame {
    background-color: #1a2332;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

QFrame#contentFrame {
    background-color: #0f172a;
}

/* =================================================================
   BUTTONS & NAVIGATION
   ================================================================= */

QPushButton {
    background-color: transparent;
    color: #cbd5e1;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 500;
    text-align: left;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #f1f5f9;
}

QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.08);
}

QPushButton:checked {
    background-color: #2563eb;
    color: white;
    border-left: 4px solid white;
    padding-left: 16px;
}

QPushButton#primaryButton {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #2563eb,
        stop:1 #1e40af
    );
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #3b82f6,
        stop:1 #2563eb
    );
}

QPushButton#primaryButton:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #1e40af,
        stop:1 #1e3a8a
    );
}

QPushButton#successButton {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #10b981,
        stop:1 #059669
    );
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 600;
}

/* =================================================================
   LABELS & TEXT
   ================================================================= */

QLabel {
    color: #f1f5f9;
    background-color: transparent;
}

QLabel#screenTitle {
    font-size: 24px;
    font-weight: 700;
    color: #f1f5f9;
}

QLabel#statValue {
    font-size: 28px;
    font-weight: 700;
    color: #2563eb;
}

QLabel#statLabel {
    font-size: 12px;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#mutedText {
    color: #94a3b8;
}

QLabel#versionLabel {
    color: #6b7280;
    padding: 10px 20px;
    font-size: 11px;
}

QLabel#placeholderText {
    font-size: 18px;
    color: #6b7280;
}

/* =================================================================
   INPUT FIELDS & COMBO BOXES
   ================================================================= */

QLineEdit,
QTextEdit,
QPlainTextEdit {
    background-color: rgba(255, 255, 255, 0.05);
    color: #f1f5f9;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #2563eb;
}

QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus {
    border: 1px solid #2563eb;
    background-color: rgba(255, 255, 255, 0.08);
}

QLineEdit::placeholder {
    color: #64748b;
}

QComboBox {
    background-color: rgba(255, 255, 255, 0.05);
    color: #f1f5f9;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #2563eb;
}

QComboBox:hover {
    border: 1px solid rgba(37, 99, 235, 0.3);
}

QComboBox:focus {
    border: 1px solid #2563eb;
    background-color: rgba(255, 255, 255, 0.08);
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: url(none);
}

/* =================================================================
   SCROLL BARS
   ================================================================= */

QScrollBar:vertical {
    background: transparent;
    width: 8px;
}

QScrollBar::handle:vertical {
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(255, 255, 255, 0.3);
}

QScrollBar::sub-line:vertical,
QScrollBar::add-line:vertical {
    border: none;
    background: none;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: rgba(255, 255, 255, 0.3);
}

QScrollBar::sub-line:horizontal,
QScrollBar::add-line:horizontal {
    border: none;
    background: none;
}

/* =================================================================
   MENUS & CONTEXT
   ================================================================= */

QMenuBar {
    background-color: #1a2332;
    color: #f1f5f9;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

QMenuBar::item:selected {
    background-color: rgba(37, 99, 235, 0.2);
}

QMenu {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
}

QMenu::item:selected {
    background-color: #2563eb;
}

/* =================================================================
   TABS
   ================================================================= */

QTabBar::tab {
    background-color: transparent;
    color: #cbd5e1;
    border: none;
    padding: 8px 16px;
    margin: 4px 2px;
    border-radius: 6px;
}

QTabBar::tab:hover {
    background-color: rgba(255, 255, 255, 0.05);
}

QTabBar::tab:selected {
    background-color: #2563eb;
    color: white;
}

QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* =================================================================
   TREE & TABLE WIDGETS
   ================================================================= */

QTreeWidget,
QTableWidget,
QListWidget {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    gridline-color: rgba(255, 255, 255, 0.05);
}

QTreeWidget::item:hover,
QTableWidget::item:hover,
QListWidget::item:hover {
    background-color: rgba(37, 99, 235, 0.1);
}

QTreeWidget::item:selected,
QTableWidget::item:selected,
QListWidget::item:selected {
    background-color: #2563eb;
    color: white;
}

QHeaderView::section {
    background-color: #0f172a;
    color: #f1f5f9;
    padding: 6px;
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    font-weight: 600;
}

/* =================================================================
   PROGRESS BAR
   ================================================================= */

QProgressBar {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: #f1f5f9;
}

QProgressBar::chunk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #2563eb,
        stop:1 #10b981
    );
    border-radius: 4px;
}

/* =================================================================
   SLIDERS
   ================================================================= */

QSlider::groove:horizontal {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 5px;
    height: 6px;
}

QSlider::handle:horizontal {
    background-color: #2563eb;
    border-radius: 6px;
    width: 14px;
    margin: -4px 0;
}

QSlider::handle:horizontal:hover {
    background-color: #3b82f6;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #2563eb,
        stop:1 #10b981
    );
    border-radius: 5px;
}

/* =================================================================
   DIALOGS & MESSAGE BOXES
   ================================================================= */

QDialog {
    background-color: #0f172a;
}

QMessageBox {
    background-color: #0f172a;
}

QMessageBox QLabel {
    color: #f1f5f9;
}

QMessageBox QPushButton {
    min-width: 60px;
    min-height: 30px;
}

QFileDialog {
    background-color: #0f172a;
}

/* =================================================================
   SPINBOX
   ================================================================= */

QSpinBox,
QDoubleSpinBox {
    background-color: rgba(255, 255, 255, 0.05);
    color: #f1f5f9;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 4px 8px;
}

QSpinBox:focus,
QDoubleSpinBox:focus {
    border: 1px solid #2563eb;
}

QSpinBox::up-button,
QSpinBox::down-button,
QDoubleSpinBox::up-button,
QDoubleSpinBox::down-button {
    background-color: transparent;
    border: none;
    width: 20px;
}

QSpinBox::up-arrow,
QSpinBox::down-arrow,
QDoubleSpinBox::up-arrow,
QDoubleSpinBox::down-arrow {
    width: 10px;
    height: 10px;
}

/* =================================================================
   TOOLTIPS
   ================================================================= */

QToolTip {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #2563eb;
    border-radius: 6px;
    padding: 6px 12px;
}

/* =================================================================
   STATUS BAR
   ================================================================= */

QStatusBar {
    background-color: #1a2332;
    color: #cbd5e1;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

QStatusBar::item {
    border: none;
}

/* =================================================================
   CUSTOM CARDS/FRAMES
   ================================================================= */

QFrame#cardFrame {
    background-color: #1e293b;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

QFrame#statCard {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #1e293b,
        stop:1 rgba(37, 99, 235, 0.1)
    );
    border: 1px solid rgba(37, 99, 235, 0.2);
    border-radius: 10px;
}

/* =================================================================
   DOCK WIDGETS
   ================================================================= */

QDockWidget {
    background-color: #0f172a;
    color: #f1f5f9;
}

QDockWidget::title {
    background-color: #1a2332;
    padding: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* =================================================================
   FOCUS OUTLINE (REMOVE DEFAULT)
   ================================================================= */

*:focus {
    outline: none;
}
"""

def load_stylesheet() -> str:
    """Load and return the DCO stylesheet."""
    return STYLESHEET


# Example usage in main application:
if __name__ == "__main__":
    # from PySide6.QtWidgets import QApplication
    # app = QApplication([])
    # app.setStyleSheet(load_stylesheet())
    print("DCO Modern Stylesheet Loaded")
    print(f"Total lines: {len(STYLESHEET.splitlines())}")
