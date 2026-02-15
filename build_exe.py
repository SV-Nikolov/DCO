"""
Build script for creating DCO executable.
This script configures PyInstaller to create a standalone executable.
"""

import PyInstaller.__main__
import sys
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# PyInstaller arguments
args = [
    'app.py',                    # Main script
    '--name=DailyChessOffline',  # Executable name
    '--onefile',                 # Single executable file
    '--windowed',                # No console window (GUI app)
    '--icon=NONE',              # No icon for now
    '--add-data=dco;dco',       # Include dco package
    '--hidden-import=PySide6.QtCore',
    '--hidden-import=PySide6.QtGui',
    '--hidden-import=PySide6.QtWidgets',
    '--hidden-import=chess',
    '--hidden-import=chess.engine',
    '--hidden-import=chess.pgn',
    '--hidden-import=sqlalchemy',
    '--hidden-import=sqlalchemy.ext.declarative',
    '--collect-all=PySide6',
    '--noconsole',
    '--clean',
]

# Run PyInstaller
PyInstaller.__main__.run(args)

print("\nBuild complete! Executable should be in the 'dist' folder.")
print("Note: You'll still need to provide Stockfish engine separately.")
