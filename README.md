# Daily Chess Offline (DCO)

A desktop Python application for chess training and improvement based on your own past mistakes.

## Features

- **Play vs Computer**: Offline chess engine with adjustable strength (1000-3200 Elo)
- **Import & Analyze**: Import Chess.com games (PGN) and analyze them locally
- **Game Database**: Searchable game library with statistics
- **Practice Mode**: Auto-generated training from your blunders and mistakes
- **Puzzles**: Offline puzzle sets and puzzles generated from your games
- **Statistics Dashboard**: Track your progress with accuracy and performance metrics

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Stockfish Chess Engine

**DCO requires Stockfish to analyze games.**

**Quick Install (Windows)**:
1. Download Stockfish: https://stockfishchess.org/download/
2. Extract the ZIP file
3. Copy `stockfish.exe` to the DCO directory (`C:\Source\DCO\`)
4. Done!

For detailed instructions, see [INSTALL_STOCKFISH.md](INSTALL_STOCKFISH.md)

### 3. Run the Application

```bash
python app.py
```

## Requirements

- Python >= 3.11 (Python 3.13+ recommended)
- Stockfish chess engine (see installation instructions above)

## Project Structure

```
dco/
├── app.py                 # Main entry point
├── ui/                    # UI layer
│   ├── main_window.py
│   ├── screens/          # Individual screens
│   └── widgets/          # Reusable UI components
├── core/                 # Core chess logic
│   ├── engine.py
│   ├── analysis.py
│   └── classification.py
├── practice/             # Practice mode logic
├── puzzles/              # Puzzle system
└── data/                 # Database layer
    ├── db.py
    └── models.py
```

## License

See LICENSE file.
