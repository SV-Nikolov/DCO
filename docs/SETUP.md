# Setup Guide for Daily Chess Offline (DCO)

## Prerequisites

1. **Python 3.11 or 3.12** installed on your system
   - Download from: https://www.python.org/downloads/
   - Verify: `python --version`

2. **Stockfish Chess Engine** (required for game analysis)
   - Download from: https://stockfishchess.org/download/
   - Windows: Download the Windows executable
   - Extract and note the path (e.g., `C:\Stockfish\stockfish.exe`)

## Installation Steps

### 1. Install Python Dependencies

Open a terminal/command prompt in the DCO directory and run:

```bash
pip install -r requirements.txt
```

This will install:
- PySide6 (Qt framework for GUI)
- python-chess (chess logic and engine communication)
- SQLAlchemy (database ORM)
- pandas, numpy (data analysis)
- matplotlib (charts)
- and other dependencies

### 2. Install Stockfish

**Option A: Automatic Detection**
- Place `stockfish.exe` in the DCO directory
- Or install Stockfish system-wide and ensure it's in your PATH

**Option B: Manual Configuration**
- The application will prompt you to configure the path on first run
- Or you can set it later in Settings

### 3. Run the Application

```bash
python app.py
```

The application should launch with the main window.

## First Steps

### Import Your First Game

1. Click **"Import"** in the navigation rail
2. Paste PGN text or click **"Import from File..."**
3. Click **"Import Games"**

Example PGN format:
```
[Event "Casual Game"]
[Site "Chess.com"]
[Date "2026.02.15"]
[White "YourUsername"]
[Black "Opponent"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 ...
```

### View Your Games

1. Click **"Library"** to see all imported games
2. Use the search box to filter by player name, event, or date
3. Double-click a game to analyze (coming in Milestone 2)

## Troubleshooting

### "Stockfish not found" Error

If you see this error:
1. Download Stockfish from https://stockfishchess.org/download/
2. Place the executable in one of these locations:
   - DCO directory (same folder as `app.py`)
   - `C:\Program Files\Stockfish\`
   - Or configure the path in Settings

### Import Errors

If games fail to import:
- Check that the PGN format is valid
- Ensure each game has proper headers (White, Black, Result)
- Look at the error messages for specific issues

### Database Issues

If you encounter database errors:
- Delete `dco_data.db` to start fresh
- The database will be recreated on next run

## Development Setup

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
DCO/
├── app.py              # Main entry point
├── dco/                # Main package
│   ├── core/          # Core chess logic
│   │   ├── engine.py          # Stockfish integration
│   │   ├── analysis.py        # Game analysis
│   │   ├── classification.py  # Move classification
│   │   ├── accuracy.py        # Accuracy computation
│   │   └── pgn_import.py      # PGN import logic
│   ├── data/          # Database layer
│   │   ├── db.py      # Database management
│   │   └── models.py  # SQLAlchemy models
│   ├── ui/            # User interface
│   │   ├── main_window.py     # Main application window
│   │   ├── screens/           # Individual screens
│   │   └── widgets/           # Reusable UI components
│   ├── practice/      # Practice mode (coming soon)
│   └── puzzles/       # Puzzle system (coming soon)
├── tests/             # Test suite
├── requirements.txt   # Python dependencies
└── README.md         # Project documentation
```

## Next Steps

Once you have games imported:

1. **Milestone 2** (in progress): Analyze games with engine to see move classifications
2. **Milestone 3**: View detailed analysis with accuracy percentages
3. **Milestone 4**: Generate practice sessions from your mistakes
4. **Milestone 5**: View statistics and track your progress

## Getting Help

- Check [Assignment.txt](Assignment.txt) for complete feature specifications
- Review code documentation in each module
- Create an issue for bugs or feature requests
