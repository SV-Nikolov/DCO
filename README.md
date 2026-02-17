# Daily Chess Offline (DCO)

A powerful desktop application for chess training and improvement based on your own past mistakes. Learn from your games, practice with personalized puzzles, and play against Stockfish.

##  Quick Start

For complete setup instructions, see [docs/QUICKSTART.md](docs/QUICKSTART.md).

\\\ash
# Clone the repository
git clone https://github.com/SV-Nikolov/DCO.git
cd DCO

# Install dependencies
pip install -r requirements.txt

# Download Stockfish (required for play and analysis features)
# See: docs/INSTALL_STOCKFISH.md

# Run the application
python app.py
\\\

##  Repository Structure

All files are organized following GitHub best practices:

- **dco/** - Source code
- **docs/** - Complete documentation (QUICKSTART, SETUP, TROUBLESHOOTING, etc.)
- **scripts/** - Utility scripts (build, database, etc.)
- **tests/** - Test suite
- **data/db/** - Application databases (generated at runtime)
- **logs/** - Log files and progress tracking
- **.github/** - GitHub configuration and templates

See [DIRECTORY_STRUCTURE.md](docs/DIRECTORY_STRUCTURE.md) for detailed file organization.

##  Documentation

Start here:
-  **[QUICKSTART.md](docs/QUICKSTART.md)** - Install and run in 5 minutes
-  **[SETUP.md](docs/SETUP.md)** - Development environment setup
-  **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues
-  **[INSTALL_STOCKFISH.md](docs/INSTALL_STOCKFISH.md)** - Engine installation
-  **[UI_DESIGN_SYSTEM.md](docs/UI_DESIGN_SYSTEM.md)** - Design specs
-  **[guides/DEVELOPERS.md](docs/guides/DEVELOPERS.md)** - Developer guide

##  Features

- **Learn from Mistakes** - Import your games and get instant analysis
- **Personalized Practice** - Auto-generated puzzles from your actual positions
- **Play vs Stockfish** - Adjustable difficulty (1000-2800 Elo)
- **Game Analysis** - Deep analysis with principal variations
- **Puzzle Library** - Unlimited practice material
- **Dark Mode** - Modern, eye-friendly UI
- **Game Database** - Searchable library with statistics

##  Requirements

- Python 3.8+
- PySide6
- python-chess
- Stockfish engine (download separately)

##  Project Status

- [logs/PROGRESS.md](logs/PROGRESS.md) - Development progress
- [logs/AI_STATE.md](logs/AI_STATE.md) - AI integration status
- [docs/planning/](docs/planning/) - Planning documents

##  License

MIT License - See [LICENSE](LICENSE)

##  Contributing

See [docs/guides/DEVELOPERS.md](docs/guides/DEVELOPERS.md)

---

**Repository**: https://github.com/SV-Nikolov/DCO
