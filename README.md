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

1. Ensure Python 3.11+ is installed
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

## Requirements

- Python >= 3.11, < 3.13
- Stockfish chess engine (will be auto-detected or can be configured in settings)

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
