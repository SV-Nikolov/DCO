"""
Daily Chess Offline (DCO) - Main Application Entry Point

A desktop application for chess training and improvement based on your own past mistakes.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from dco.ui.main_window import MainWindow
from dco.ui.modern_stylesheet import load_stylesheet
from dco.data.db import init_database


def main():
    """Main application entry point."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Daily Chess Offline")
    app.setOrganizationName("DCO")
    
    # Apply modern stylesheet
    app.setStyleSheet(load_stylesheet())
    
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
