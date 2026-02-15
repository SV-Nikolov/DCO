"""
Daily Chess Offline (DCO) - Main Application Entry Point

A desktop application for chess training and improvement based on your own past mistakes.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from dco.ui.main_window import MainWindow
from dco.data.db import init_database


def main():
    """Main application entry point."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Daily Chess Offline")
    app.setOrganizationName("DCO")
    
    # Set application-wide style
    app.setStyle("Fusion")
    
    # Set global stylesheet for text visibility
    app.setStyleSheet("""
        QWidget {
            color: #1f2937;
        }
        QLabel {
            color: #1f2937;
        }
        QPushButton {
            color: #1f2937;
        }
        QLineEdit {
            color: #1f2937;
        }
        QTextEdit {
            color: #1f2937;
        }
        QCheckBox {
            color: #1f2937;
        }
        QComboBox {
            color: #1f2937;
        }
    """)
    
    # Initialize database
    try:
        db = init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return 1
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
