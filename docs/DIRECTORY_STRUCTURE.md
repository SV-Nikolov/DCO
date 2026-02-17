# Repository Directory Structure

This document explains the organization of the DCO repository following GitHub best practices.

## Root Level

```
├── app.py                      # Application entry point
├── requirements.txt            # Production dependencies
├── requirements-minimal.txt    # Minimal required packages
├── README.md                   # Main readme (you are here)
├── LICENSE                     # MIT License
├── Assignment.txt              # Course assignment details
├── .gitignore                  # Git ignore rules
└── .git/                       # Git repository metadata
```

## Source Code: `dco/`

The main application source code organized by feature:

```
dco/
├── __init__.py                 # Package initialization
│
├── core/                       # Core chess logic and engine integration
│   ├── engine.py              # Stockfish wrapper and EngineConfig
│   ├── settings.py            # Application settings persistence
│   ├── analysis.py            # Game analysis engine
│   ├── classification.py       # Move classification logic
│   └── __pycache__/           # Python cache (git ignored)
│
├── ui/                        # User interface layer
│   ├── main_window.py         # Main application window
│   ├── modern_stylesheet.py   # Theme and styling system
│   │
│   ├── screens/               # Individual application screens
│   │   ├── home.py           # Home/Dashboard screen
│   │   ├── library.py        # Game library screen
│   │   ├── analysis.py       # Game analysis screen
│   │   ├── play.py           # Play vs Computer screen
│   │   ├── puzzles.py        # Puzzle practice screen
│   │   ├── settings.py       # Application settings screen
│   │   └── __pycache__/      # Python cache
│   │
│   ├── widgets/               # Reusable UI components
│   │   ├── chess_board.py    # Chess board display widget
│   │   ├── move_list.py      # Move list display
│   │   ├── piece_selector.py # Piece selection widget
│   │   └── __pycache__/      # Python cache
│   │
│   └── __pycache__/           # Python cache
│
├── data/                      # Database and data persistence
│   ├── db.py                 # Database initialization
│   ├── models.py             # SQLAlchemy ORM models
│   ├── game_import.py        # PGN import functionality
│   └── __pycache__/          # Python cache
│
├── engine/                    # Engine and gameplay logic
│   ├── engine_controller.py  # Engine control and strength adjustment
│   ├── dual_game_clock.py    # Chess clock implementation
│   ├── __init__.py           # Package exports
│   └── __pycache__/          # Python cache
│
├── practice/                  # Practice mode
│   ├── __init__.py
│   └── __pycache__/          # Python cache
│
├── puzzles/                   # Puzzle generation and management
│   ├── puzzle_generator.py   # Generate puzzles from positions
│   ├── puzzle_validator.py   # Validate puzzle sequences
│   ├── __init__.py
│   └── __pycache__/          # Python cache
│
└── __pycache__/              # Python cache (git ignored)
```

## Documentation: `docs/`

Complete documentation organized by topic:

```
docs/
├── README.md                          # Documentation index
├── QUICKSTART.md                      # 5-minute getting started guide
├── SETUP.md                           # Development environment setup
├── TROUBLESHOOTING.md                 # Common issues and solutions
├── INSTALL_STOCKFISH.md               # Stockfish engine installation
├── UI_DESIGN_SYSTEM.md                # UI/UX design specifications
├── DIRECTORY_STRUCTURE.md             # This file
│
├── guides/                            # Detailed guides
│   ├── DEVELOPERS.md                  # Developer guide and architecture
│   ├── INTEGRATION_GUIDE.md           # Feature integration details
│   └── INTEGRATION_COMPLETE.md        # Integration completion status
│
└── planning/                          # Project planning and tracking
    ├── 375939b-ignore-stockfish-binary.md   # Planning note
    ├── 4b3c694-fix-analysis-classification-and-add-eco.md
    ├── milestone-6-puzzles.md         # Puzzle feature milestone
    └── milestone-7-play-vs-computer.md # Play feature milestone
```

### Documentation Quick Reference

| File | Purpose | Audience |
|------|---------|----------|
| QUICKSTART.md | Install and run in 5 minutes | Users, First-time setup |
| SETUP.md | Development environment | Developers |
| TROUBLESHOOTING.md | Common issues | Users, Developers |
| INSTALL_STOCKFISH.md | Engine installation | Users |
| UI_DESIGN_SYSTEM.md | Design standards | UI Developers |
| guides/DEVELOPERS.md | Architecture & design | Developers |
| guides/INTEGRATION_GUIDE.md | Feature integration | Developers |
| planning/ | Project tracking | Project managers |

## Scripts: `scripts/`

Utility and build scripts:

```
scripts/
├── build_exe.py                       # Build Windows executable (PyInstaller)
├── create_sample_puzzles.py           # Generate sample puzzle data
├── create_test_games.py               # Create test game data
├── verify_new_puzzles.py              # Validate puzzle sequences
├── migrate_puzzles.py                 # Database migration utilities
├── check_db.py                        # Database inspection utility
├── run_dco.bat                        # Windows batch runner
└── DailyChessOffline.spec             # PyInstaller specification
```

**When to use each script:**

- `build_exe.py` - Create Windows standalone executable
- `create_sample_puzzles.py` - Populate database with sample data
- `create_test_games.py` - Generate test games for development
- `verify_new_puzzles.py` - Validate puzzle integrity
- `migrate_puzzles.py` - Update database schema
- `check_db.py` - Inspect current database state

## Tests: `tests/`

Test suite:

```
tests/
├── __init__.py                        # Test package initialization
├── test_basic.py                      # Basic functionality tests
├── test_puzzles.py                    # Puzzle system tests
└── test_puzzle_sequence.py            # Puzzle sequence tests
```

Run tests with:
```bash
python -m pytest tests/
python -m pytest tests/ -v              # Verbose output
```

## Data: `data/` (Generated at Runtime)

Application data directory - **NOT in Git**:

```
data/
├── db/                                # Database files
│   ├── dco.db                        # Main application database
│   └── .gitkeep                      # Directory marker for git
└── .gitkeep                          # Directory marker for git
```

Files here are generated when the application runs. They are in `.gitignore` to keep the repository clean.

## Logs: `logs/` (Generated at Runtime)

Log files and progress tracking - **NOT in Git**:

```
logs/
├── debug_err.txt                      # Error logs (generated)
├── debug_out.txt                      # Debug output (generated)
├── PROGRESS.md                        # Development progress tracker
├── AI_STATE.md                        # AI integration status
└── .gitkeep                           # Directory marker for git
```

The PROGRESS.md and AI_STATE.md files are committed to track project status. Generated debug files are in `.gitignore`.

## Build Artifacts (Generated, Not in Git)

```
build/                                 # PyInstaller build directory (created)
dist/                                  # Standalone executables (created)
```

These are created by `scripts/build_exe.py` and are in `.gitignore`.

## GitHub Configuration: `.github/`

GitHub-specific configuration:

```
.github/
├── ISSUE_TEMPLATE/                    # Issue templates for GitHub
└── pull_request_template              # PR template (if needed)
```

## Git Configuration

```
.gitignore                             # Files to exclude from git
.git/                                  # Git repository metadata
```

## Key Principles

### 1. **Source Code Organization**
- `dco/` contains all source code
- Organized by feature (core, ui, data, engine, etc.)
- Each module has a clear responsibility

### 2. **Documentation Centralization**
- All user and developer docs in `docs/`
- Quick reference guides in root for frequently viewed files
- Planning documents in `docs/planning/`

### 3. **Scripts Separation**
- All utility scripts in `scripts/`
- Not cluttering the root directory
- Easy to find and skip in code reviews

### 4. **Clean Repository**
- Generated data in `data/`, excluded from git
- Logs in `logs/`, excluded from git
- Build artifacts in `build/` and `dist/`, excluded from git
- Cache directories in `.gitignore`

### 5. **Test Organization**
- All tests in dedicated `tests/` directory
- Easy to run with pytest
- Can exclude from production builds

## Adding New Files

When adding new files, follow these guidelines:

### For Source Code
→ Create in appropriate subdirectory under `dco/`

#### Examples:
- New screen: `dco/ui/screens/new_feature.py`
- New core logic: `dco/core/new_module.py`
- New widget: `dco/ui/widgets/new_widget.py`

### For Documentation
→ Create in `docs/` (or subdirectory)

#### Examples:
- User guide: `docs/FEATURE_GUIDE.md`
- Developer doc: `docs/guides/ARCHITECTURE.md`
- Planning: `docs/planning/feature-xyz.md`

### For Scripts
→ Create in `scripts/`

#### Examples:
- Utility script: `scripts/data_import.py`
- Build tool: `scripts/build_something.py`

### For Tests
→ Create in `tests/`

#### Examples:
- Feature tests: `tests/test_feature.py`
- Integration tests: `tests/test_integration.py`

## Maintenance

### Keeping It Clean

1. **Remove unused scripts** - Delete from `scripts/` if no longer needed
2. **Archive old docs** - Move outdated documentation to `docs/archive/`
3. **Update README.md** - Keep it current with project status
4. **Review structure** - Quarterly assessment of organization

### Common Reorganizations

If you need to reorganize, ensure:

```bash
git mv old_location new_location
git commit -m "refactor: move files to improve organization"
git push origin branch-name
```

## Questions?

- **Getting started?** → See [docs/QUICKSTART.md](QUICKSTART.md)
- **Development?** → See [docs/guides/DEVELOPERS.md](guides/DEVELOPERS.md)  
- **Issues?** → See [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Last Updated**: February 17, 2026
