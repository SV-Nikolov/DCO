"""
Daily Chess Offline (DCO) - Main Application Entry Point

A desktop application for chess training and improvement based on your own past mistakes.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QSharedMemory

from dco.ui.main_window import MainWindow
from dco.ui.modern_stylesheet import load_stylesheet
from dco.data.db import init_database
from dco.core.settings import get_settings


def main():
    """Main application entry point."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Daily Chess Offline")
    app.setOrganizationName("DCO")
    
    # Check for existing instance
    shared_memory = QSharedMemory("DCO_SingleInstance")
    if not shared_memory.create(1):
        QMessageBox.warning(
            None,
            "Application Already Running",
            "Daily Chess Offline is already running. Only one instance can run at a time."
        )
        return 1
    
    # Load theme from settings and apply stylesheet
    settings = get_settings()
    theme = settings.get_theme()
    app.setStyleSheet(load_stylesheet(theme))
    
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
    
    # Ensure cleanup on quit
    app.aboutToQuit.connect(window._cleanup_all_resources)
    
    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
