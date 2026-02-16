# AI State Document - Daily Chess Offline (DCO)
**Last Updated**: Project State Snapshot  
**Purpose**: Enable seamless AI session handoff and development continuity

---

## 🎯 QUICK START FOR NEW AI SESSION

### Immediate Context
You are continuing development on **Daily Chess Offline (DCO)**, a Python desktop chess improvement application. The project is at **Milestone 4 Complete** (Practice Mode fully functional). The user has just requested comprehensive documentation for AI continuity.

### What Works Right Now
✅ **PGN Import** → **Game Analysis** → **Practice Item Generation** → **Interactive Practice Sessions**  
✅ Advanced move classification (Brilliant, Critical, Blunder detection with strict thresholds)  
✅ ACPL-based performance Elo estimation  
✅ ECO opening detection (minimal dataset)  
✅ Spaced repetition with mastery tracking (3 consecutive first-try solves)  
✅ Auto-migration for database schema evolution

### What to Do Next
**Priority 1**: Test practice mode with real game analysis  
**Priority 2**: Begin Milestone 5 (Statistics Dashboard)  
**Priority 3**: Expand ECO dataset from sample to full reference

### Critical Commands
```powershell
# Run application
python app.py

# Install dependencies
pip install -r requirements.txt

# Reset database (if schema issues)
Remove-Item dco_data.db
```

---

## 📋 PROJECT OVERVIEW

### Core Identity
**Daily Chess Offline (DCO)** is a desktop application for chess improvement through personalized training based on user's own mistakes. Think "Chess.com Game Review + Personal Weakness Trainer" but completely offline.

### Key Features
1. **PGN Import**: Batch import games from Chess.com/Lichess
2. **Local Analysis**: Stockfish-powered move-by-move evaluation
3. **Advanced Classification**: 9 move types (book/best/excellent/good/inaccuracy/mistake/blunder/brilliant/critical)
4. **Practice Mode**: Drill mistakes with spaced repetition and mastery tracking
5. **Game Library**: Searchable database with filters
6. **Planned**: Statistics dashboard, puzzle mode, play vs computer

### Technology Stack
- **Language**: Python 3.13
- **UI Framework**: PySide6 (Qt 6)
- **Database**: SQLite + SQLAlchemy 2.x ORM
- **Chess Engine**: Stockfish (UCI protocol via python-chess)
- **Board Rendering**: SVG via python-chess library

---

## 🏗️ ARCHITECTURE

### Directory Structure
```
DCO/
├── app.py                          # Application entry point
├── dco/
│   ├── core/                       # Business logic
│   │   ├── analysis.py            # Game analysis orchestration
│   │   ├── classification.py      # Move classification engine
│   │   ├── accuracy.py            # Accuracy calculation
│   │   ├── engine.py              # Stockfish integration (UCI)
│   │   ├── eco.py                 # Opening detection
│   │   ├── pgn_import.py          # PGN parsing and import
│   │   └── practice.py            # Practice item generation & spaced repetition
│   ├── data/                       # Database layer
│   │   ├── db.py                  # Database initialization & auto-migration
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   └── eco_data.json          # ECO opening reference (minimal)
│   ├── ui/                         # User interface
│   │   ├── main_window.py         # Main window with navigation rail
│   │   ├── screens/               # Individual screens
│   │   │   ├── home.py           # Dashboard
│   │   │   ├── import_pgn.py     # PGN import interface
│   │   │   ├── library.py        # Game library browser
│   │   │   ├── analysis.py       # Game review interface
│   │   │   └── practice.py       # Interactive practice UI
│   │   └── widgets/               # Reusable components
│   │       ├── chessboard.py     # Interactive chessboard widget
│   │       └── move_list.py      # Move list with classifications
│   ├── stockfish/                  # Stockfish binary directory (gitignored)
│   │   └── *.exe                  # 108MB binary, manually provided
│   ├── practice/                   # Future: practice-specific utilities
│   └── puzzles/                    # Future: puzzle generation/loading
├── dco_data.db                     # SQLite database (gitignored)
├── requirements.txt                # Python dependencies
├── Assignment.txt                  # Original project specification
├── PROGRESS.md                     # Development progress tracker
└── AI_STATE.md                     # This document
```

### Data Flow
```
[PGN Import] → [Database: Game]
     ↓
[User clicks Analyze] → [Background Thread: GameAnalyzer]
     ↓
[Stockfish Evaluation] → [Move Classification] → [ACPL/Elo Calculation]
     ↓
[save_analysis_to_db] → [Database: Analysis + Move records]
     ↓
[generate_practice_items] → [Database: PracticeItem + PracticeProgress]
     ↓
[User opens Practice screen] → [select_practice_items (exclude mastered)]
     ↓
[Interactive Board] → [User makes move]
     ↓
[Correct?] → Yes: advance to next | No: red/green arrows, 1s pause, requeue
     ↓
[update_practice_progress] → [SM-2 algorithm, mastery tracking]
```

---

## 🔧 CRITICAL IMPLEMENTATION DETAILS

### 1. Move Classification System

#### Classification Types (Enum: VARCHAR in SQLite)
```python
class MoveClassification(Enum):
    BOOK = "BOOK"                   # Opening book moves (depth ≤ 15)
    BEST = "BEST"                   # Best move (CP loss ≤ 10)
    EXCELLENT = "EXCELLENT"         # CP loss 11-25
    GOOD = "GOOD"                   # CP loss 26-50
    INACCURACY = "INACCURACY"       # CP loss 51-100
    MISTAKE = "MISTAKE"             # CP loss 101-200
    BLUNDER = "BLUNDER"             # CP loss > 200
    BRILLIANT = "BRILLIANT"         # Best/Excellent with sacrifice (special criteria)
    CRITICAL = "CRITICAL"           # Unique best move position (MultiPV=5)
```

#### Brilliant Move Detection (Trade-Proof)
**Requirements** (ALL must be met):
1. Move is Best or Excellent (CP loss ≤ 25)
2. Not a recapture (no immediate material regain)
3. Not the only legal move
4. Not a simple check
5. Immediate material sacrifice detected (≥ 1 pawn equivalent)
6. **Material deficit persists through PV horizon** (8 plies ahead)
7. Deeper verification (depth 25) confirms continued advantage
8. Not an obvious/forced move

**Key Constants** (classification.py):
```python
PV_HORIZON = 8              # Plies to verify sacrifice persistence
DEEPER_DEPTH = 25           # Verification depth
BRILLIANT_MARGIN = 30       # CP tolerance for "best/excellent"
BRILLIANT_MIN_SACRIFICE = 2 # Minimum material loss (pawns)
```

**Implementation**: `_is_brilliant_move()` in classification.py (lines ~200-300)

#### Critical Position Detection (MultiPV)
**Requirements**:
1. Position evaluated with **MultiPV=5** (top 5 moves)
2. **Uniqueness**: E1 - E2 gap ≥ 180 cp, OR
3. **Breadth + Collapse**: (median(E2-E5) - E1 ≥ 150) AND (E5 - E1 ≥ 300)
4. **Not decided**: |E1| < 500 cp (unless mate nearby)
5. Mate exceptions: Critical if mate-in-N detected

**Key Constants** (classification.py):
```python
E1_E2_UNIQUENESS = 180      # Gap for unique best move
MIN_BREADTH = 150           # Median gap requirement
WORST_COLLAPSE = 300        # Worst alternative drop
DECIDED_EVAL = 500          # Overwhelming advantage threshold
```

**Implementation**: `_is_critical_position()` in classification.py (lines ~350-450)

### 2. Performance Elo Estimation (ACPL-Based)

#### Formula
```python
# Base ACPL (Average Centipawn Loss per move, excluding book moves)
acpl = sum(cp_losses) / num_non_book_moves

# ACPL → Elo mapping (tiered thresholds)
if acpl <= 10:   elo = 2600 - (acpl × 30)           # 2600-2300
elif acpl <= 30: elo = 2300 - ((acpl-10) × 15)      # 2300-2000
elif acpl <= 50: elo = 2000 - ((acpl-30) × 15)      # 2000-1700
elif acpl <= 100: elo = 1700 - ((acpl-50) × 10)     # 1700-1200
else:            elo = 1200 - ((acpl-100) × 4)       # 1200-500

# Error penalties (normalized per 40 moves)
blunders_per_40 = (blunder_count / non_book_moves) × 40
mistakes_per_40 = (mistake_count / non_book_moves) × 40
penalty = (blunders_per_40 × 150) + (mistakes_per_40 × 50)

# Final rating
performance_elo = clamp(elo - penalty, 500, 3000)

# Opponent-relative capping
if opponent_elo:
    performance_elo = clamp(performance_elo, opponent_elo - 400, opponent_elo + 400)
```

#### Minimum Requirements
- Game length: ≥ 20 plies (half-moves)
- At least 1 non-book move for ACPL calculation

**Implementation**: `_estimate_performance_elo()` in analysis.py (lines ~400-500)

### 3. ECO Opening Detection

#### Algorithm
Longest-prefix matching from opening position:
1. Start from initial board state
2. Play moves from game in sequence
3. After each move, check eco_data.json for matching move sequence
4. Keep longest matching sequence
5. Return (eco_code, opening_name, opening_variation)

**Data Source**: `dco/data/eco_data.json` (currently minimal sample)

**Example Entry**:
```json
{
  "moves": "e2e4 e7e5 g1f3",
  "eco": "C40",
  "name": "King's Pawn Game",
  "variation": ""
}
```

**Implementation**: `ECODetector.detect_opening()` in eco.py (lines ~30-80)

**⚠️ Known Issue**: eco_data.json contains only ~20 sample openings. Needs full ECO reference with ~500 entries.

### 4. Practice Mode (Spaced Repetition)

#### Item Generation
**Offset**: Default 2 plies before mistake (configurable via `DEFAULT_OFFSET_PLIES`)  
**Target Line**: Single move only (`DEFAULT_TARGET_LINE_PLIES = 1` per user requirement)

**Inclusion Criteria**:
- Move classification: BLUNDER, MISTAKE, CRITICAL (default)
- Optional: INACCURACY (via settings)
- Not book moves
- Not Brilliant moves (already correct)
- No duplicate positions (same FEN + target line)

**Database Records**:
- `PracticeItem`: Core data (FEN, target line UCI/SAN, category, source game)
- `PracticeProgress`: SM-2 state (due_date, interval_days, ease_factor, consecutive_first_try, lapses)

**Implementation**: `generate_practice_items()` in practice.py (lines ~50-150)

#### SM-2 Spaced Repetition
**Quality Scores**:
- **5**: Pass on first try (correct move immediately)
- **3**: Pass after retry (correct after hints/multiple attempts)
- **1**: Fail (wrong move, ran out of attempts)

**Interval Progression**:
```python
# First review
if repetitions == 0:
    interval = 1 day (quality 5) or 1 day (quality 3/1)

# Second review
elif repetitions == 1:
    interval = 6 days (quality ≥ 3)

# Subsequent reviews
else:
    interval = previous_interval × ease_factor
```

**Ease Factor Adjustment**:
```python
# Quality 5: ease_factor += 0.1 (max 2.5)
# Quality 3: ease_factor unchanged
# Quality 1: ease_factor -= 0.2 (min 1.3)
```

**Mastery Tracking**:
- `consecutive_first_try` counter: increments on quality 5, resets on quality 3/1
- **Mastery threshold**: `consecutive_first_try ≥ 3`
- Mastered items excluded from future sessions: `WHERE consecutive_first_try < 3`

**Implementation**: `update_practice_progress()` in practice.py (lines ~200-300)

#### Practice UI Behavior (User-Specified)
1. **Single-move targets**: No continuation lines after correct move
2. **Wrong move feedback**:
   - Red arrow: user's wrong move (from → to)
   - Green arrow: correct move
   - 1-second pause (`QTimer.singleShot(1000)`)
   - Switch to **different random position** (not next in sequence)
3. **Re-queuing**: Wrong items appended to session queue (once per item via `requeued_ids` set)
4. **Mastery filter**: Items with `consecutive_first_try ≥ 3` excluded from selection

**Implementation**: PracticeScreen class in ui/screens/practice.py (lines ~100-500)

### 5. Database Schema & Auto-Migration

#### Key Models (SQLAlchemy)
```python
# Game: Imported PGN data
class Game(Base):
    id: int
    pgn_text: str
    moves_san: str              # Space-separated SAN moves
    eco_code: str               # ECO code (e.g., "C40")
    opening_name: str
    opening_variation: str
    # ... metadata (players, date, result, etc.)

# Analysis: Game-level analysis results
class Analysis(Base):
    id: int
    game_id: int (FK → Game)
    accuracy_white: float       # 0-100
    accuracy_black: float
    perf_elo_white: int         # ACPL-based estimated Elo
    perf_elo_black: int
    # ... aggregate stats

# Move: Move-by-move evaluations
class Move(Base):
    id: int
    analysis_id: int (FK → Analysis)
    move_number: int
    move_san: str
    classification: Enum(MoveClassification)  # stored as VARCHAR
    eval_before_cp: int
    eval_best_cp: int
    eval_after_cp: int
    is_critical: bool
    is_brilliant: bool
    best_line_san: str
    # ...

# PracticeItem: Extracted training positions
class PracticeItem(Base):
    id: int
    game_id: int (FK → Game)
    fen_start: str              # Position to practice from
    target_line_uci: str        # JSON array ["e2e4"]
    target_line_san: str        # JSON array ["e4"]
    category: Enum(PracticeCategory)  # BLUNDER/MISTAKE/CRITICAL/INACCURACY
    motif_tags: str             # JSON array (future: ["fork", "pin"])
    # ...

# PracticeProgress: SM-2 spaced repetition state
class PracticeProgress(Base):
    id: int
    item_id: int (FK → PracticeItem, one-to-one)
    due_date: datetime
    interval_days: int
    ease_factor: float          # 1.3-2.5
    repetitions: int
    consecutive_first_try: int  # Mastery tracking
    lapses: int
    last_reviewed: datetime

# TrainingSession: Session tracking
class TrainingSession(Base):
    id: int
    type: Enum(SessionType)     # PRACTICE/PUZZLE/PLAY
    started_at: datetime
    ended_at: datetime
    accuracy: float             # % correct on first try
```

#### Auto-Migration System
**Purpose**: Add new columns without losing user data (alternative to Alembic)

**Implementation** (`_auto_migrate()` in db.py):
1. Check existing columns via `PRAGMA table_info(table_name)`
2. Add missing columns with `ALTER TABLE table_name ADD COLUMN ...`
3. Normalize enum values: `UPDATE moves SET classification = UPPER(classification)`

**Current Migrations**:
- ECO columns: `eco_code`, `opening_name`, `opening_variation` on `games` table
- Mastery tracking: `consecutive_first_try` on `practice_progress` table
- Enum normalization: Uppercase all classification values (BOOK not book)

**⚠️ Limitation**: Cannot modify existing columns (SQLite limitation). For breaking changes, delete `dco_data.db` and recreate.

**Execution**: Called automatically in `Database.init_db()` (db.py line ~150)

---

## 🎓 CRITICAL ALGORITHM DETAILS (Non-Obvious)

### Why "Trade-Proof" Brilliant Detection?
**Problem**: Early implementation marked any sacrifice as Brilliant, including unsound tactics.  
**Solution**: Verify material deficit persists through engine's primary variation (PV) for 8 plies. If engine expects material recovery (recapture, compensation), not Brilliant.

**Example**:
```
Position: User sacrifices queen for checkmate in 5
- Immediate material: -9 points (queen)
- PV at ply +2: Still -9 (opponent can't prevent mate)
- PV at ply +8: Game over (mate delivered)
→ Brilliant ✓ (sacrifice never recovered)

Position: User sacrifices rook for bishop pair
- Immediate material: -2 points (rook vs bishop)
- PV at ply +4: -0.5 points (second bishop captured)
- PV at ply +8: +0.5 points (pawn compensation)
→ Not Brilliant ✗ (material recovered through PV)
```

### Why MultiPV=5 for Critical Positions?
**Problem**: Single-line engine analysis can't detect "obvious vs nuanced" positions.  
**Solution**: Evaluate top 5 moves. If 2nd-best is close to best (< 180cp gap), position has multiple viable options → not critical. If 2nd-best is terrible (≥180cp worse), position has unique best move → critical.

**Example**:
```
Non-Critical Position (MultiPV=5 results):
1. Nf3: +0.5
2. Nc3: +0.4  (gap: 10cp)
3. d4:  +0.3
4. e3:  +0.2
5. Nge2: +0.1
→ Multiple good moves, not critical

Critical Position (MultiPV=5 results):
1. Rxf7!: +2.8      (only winning move)
2. Kh1:  -4.5      (gap: 730cp)
3. Re1:  -5.0
4. Qd2:  -5.5
5. c3:   -6.0
→ Unique best move, CRITICAL ✓
```

### Why Detach Practice Items from SQLAlchemy Session?
**Problem**: `PracticeItem` objects loaded in one method, accessed in UI after session closes → `DetachedInstanceError` on lazy attribute access.  
**Solution**: Force-load all needed attributes, then `session.expunge(item)` to detach from session. Store `session_record_id: int` instead of `TrainingSession` ORM object to avoid relationship navigation.

**Code Pattern**:
```python
# Load items with explicit attribute access
items = session.query(PracticeItem).filter(...).all()
for item in items:
    # Force-load lazy attributes
    _ = item.fen_start
    _ = item.target_line_uci
    _ = item.target_line_san
    _ = item.category
    # Detach from session
    session.expunge(item)

# Safe to use items after session closes
self.items = items
```

### Why Normalize Error Rates Per 40 Moves?
**Problem**: Short games (20 moves) vs long games (60 moves) have incomparable error counts.  
**Solution**: Scale error rates to standard 40-move game length for Elo penalty calculation.

**Example**:
```
Game A: 20 moves, 2 blunders
- Blunders per 40 = (2/20) × 40 = 4
- Penalty = 4 × 150cp = 600cp

Game B: 60 moves, 3 blunders  
- Blunders per 40 = (3/60) × 40 = 2
- Penalty = 2 × 150cp = 300cp

Without normalization, Game A (shorter, more errors per move) would be unfairly penalized less than Game B (longer, more total errors).
```

---

## 🐛 KNOWN ISSUES & FIXES

### 1. GitHub Push Rejection (108MB Stockfish Binary)
**Problem**: Stockfish binary exceeded GitHub's 100MB file size limit.  
**Solution**: History rewrite with `git filter-branch` to purge binary from all commits.

**Commands Used**:
```powershell
# Create bare clone
git clone --bare . C:\temp\dco_bare

# Enter bare repo
cd C:\temp\dco_bare

# Remove binary from history
git filter-branch --force --index-filter `
  "git rm --cached --ignore-unmatch dco/stockfish/stockfish-windows-x86-64-avx2.exe" `
  --prune-empty --tag-name-filter cat -- --all

# Force-push cleaned history
git push --force origin main

# Reset local repo
cd C:\Source\DCO
git fetch
git reset --hard origin/main
```

**Prevention**: Added `dco/stockfish/*.exe` to .gitignore

### 2. Enum Serialization Error (book vs BOOK)
**Problem**: Initial implementation stored lowercase enum values (`book`), later changed to uppercase enum names (`BOOK`).  
**Symptom**: `ValueError: 'book' is not a valid MoveClassification`

**Solution**: Auto-migration normalizes on startup:
```python
cursor.execute("UPDATE moves SET classification = UPPER(classification)")
```

**Current State**: All new records use uppercase, old records migrated automatically.

### 3. DetachedInstanceError in Practice Screen
**Problem**: PracticeItem objects accessed after SQLAlchemy session closed.  
**Symptom**: `DetachedInstanceError: Instance <PracticeItem> is not bound to a Session`

**Solution**:
1. Force-load all needed attributes before expunging
2. Store `session_record_id: int` instead of `TrainingSession` ORM object

**Implementation**: lines ~150-180 in practice.py

### 4. Missing ECO Columns in Existing Database
**Problem**: Schema changes without migration caused `OperationalError: no such column: eco_code`.  
**Solution**: Auto-migration adds columns:
```python
if 'eco_code' not in columns:
    cursor.execute("ALTER TABLE games ADD COLUMN eco_code VARCHAR(10)")
```

**Current State**: Auto-migration handles this on startup.

---

## 🚀 COMPLETED MILESTONES

### ✅ Milestone 1: Foundations
- Project structure with modular organization
- PySide6 application shell with navigation rail
- SQLite database with SQLAlchemy ORM
- PGN import (text + file, batch support)
- Game library with search and filtering
- Home screen with quick stats

### ✅ Milestone 2: Engine Integration
- Stockfish integration via python-chess UCI
- Auto-detection of Stockfish installation
- Position evaluation with principal variations (PV)
- MultiPV support (evaluate top N moves)
- Configurable depth, time, threads, hash

### ✅ Milestone 3: Classifications + Accuracy
- 9-category move classification system
- Centipawn loss calculation
- Accuracy computation (logarithmic decay)
- ACPL-based performance Elo estimation
- Brilliant move detection (trade-proof, PV-horizon verification)
- Critical position detection (MultiPV=5, uniqueness/breadth/collapse)
- Analysis screen with interactive board and move list
- Background analysis with progress indicator

### ✅ Milestone 4: Practice Mode
- Practice item generator from analyzed games
- SM-2 spaced repetition algorithm
- Mastery tracking (3 consecutive first-try threshold)
- Interactive practice UI with chessboard
- Category selection (Blunders/Mistakes/Critical/Inaccuracies)
- Strict/Lenient mode (best move only vs top-3 acceptable)
- Single-move targets (per user requirement)
- Visual feedback: red arrow (wrong) + green arrow (correct)
- 1-second pause before switching to random different position
- Re-queuing failed positions (once per session)
- Session tracking (accuracy, time, items completed)

### ✅ Additional Features
- ECO opening detection with longest-prefix matching
- Auto-migration system for database schema evolution
- Git history cleanup (removed large binary)
- Comprehensive error handling and session management

---

## 📝 PENDING WORK

### ⏳ Milestone 5: Statistics Dashboard
**Requirements** (from Assignment.txt):
- Date range selector (last 7/30/90 days, custom range)
- **Charts**:
  - Accuracy over time (line chart)
  - Performance Elo over time (line chart)
  - Blunders per game (bar chart)
  - Mistakes by motif/type (pie or bar chart)
- **Summary Cards**:
  - Most common error categories
  - Performance by time control
  - Performance by color (White vs Black)
  - Opening performance (best/worst openings by accuracy/Elo)

**Implementation Plan**:
1. Create `dco/ui/screens/statistics.py`
2. Add date range filter UI (QDateRangeEdit or custom widget)
3. Query `Analysis` table with date filtering:
   - `SELECT accuracy_white, accuracy_black, perf_elo_white, perf_elo_black FROM analyses JOIN games ON ...`
4. Query `Move` table for classification counts:
   - `SELECT classification, COUNT(*) FROM moves GROUP BY classification`
5. Integrate charting library:
   - Option A: matplotlib with Qt backend (`from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg`)
   - Option B: PySide6 native charts (QtCharts module)
6. Implement chart widgets:
   - `AccuracyLineChart`: Plot accuracy over game dates
   - `EloLineChart`: Plot performance Elo over game dates
   - `BlundersBarChart`: Bar chart of blunder counts per game
   - `MotifPieChart`: Pie chart of mistake distribution (requires motif tagging)
7. Navigation: Add statistics button signal in main_window.py

**Estimated Effort**: 4-6 hours

### ⏳ Milestone 6: Puzzles
**Requirements** (from Assignment.txt):
- Offline puzzle database (import from PGN/EPD/FEN formats)
- Puzzle categories: Mate, Win Material, Tactic, Defense
- Puzzle rating progression (easier → harder as user improves)
- "From My Games" puzzles: Convert critical positions and missed tactics into puzzles
- Puzzle UI: Similar to practice screen but with hint system

**Implementation Plan**:
1. Create `Puzzle` model:
   ```python
   class Puzzle(Base):
       id: int
       fen: str
       solution_uci: str          # JSON array of moves
       theme: Enum(PuzzleTheme)   # MATE/MATERIAL/TACTIC/DEFENSE
       rating: int                # Difficulty (1000-3000)
       source: str                # "lichess", "user_game", etc.
       source_game_id: int        # FK to Game (if from user game)
   ```
2. Puzzle import: Parse standard puzzle formats (Lichess CSV, Chess Tempo JSON)
3. Puzzle generation from user games:
   - Extract critical positions (already flagged in analysis)
   - Extract missed wins (eval drop ≥ 300cp after mistake)
   - Store as puzzles with solution = best line from engine
4. Create `dco/ui/screens/puzzles.py`:
   - Reuse PracticeScreen architecture (interactive board)
   - Add hint system (show first move, show threat, show full line)
   - Rating-based selection (user performance → puzzle difficulty)
5. Puzzle progress tracking (similar to spaced repetition)

**Estimated Effort**: 6-8 hours

### ⏳ Play vs Computer Mode
**Requirements** (from Assignment.txt):
- Opponent strength: 1000-3200 Elo (map to Stockfish skill level 0-20)
- Time controls: Bullet (1-2 min), Blitz (3-5 min), Rapid (8-10 min), Custom (1-10 min)
- Increment support (0-5 seconds)
- Color selection: White / Black / Random
- Optional features: Takebacks, Hints, Coach Mode (show threats/best line after move)
- Auto-save finished game to database

**Implementation Plan**:
1. Elo → Skill Level mapping:
   ```python
   def elo_to_skill_level(elo: int) -> int:
       # 1000 Elo → Skill 0, 3200 Elo → Skill 20
       return round((elo - 1000) / 110)
   ```
2. Create `dco/ui/screens/play.py`:
   - Game setup panel (strength, time, color, options)
   - Real-time game loop with clock management
   - Interactive board (reuse chessboard widget)
   - Move validation (legal move check)
   - Engine move generation (async to avoid UI freeze)
3. Clock implementation:
   - Use `QTimer` for countdown (update every 100ms)
   - Time increment after each move
   - Flag falls → auto-resign
4. Optional features:
   - Takeback: `board.pop()` to undo last move
   - Hints: Show engine's top move (arrow overlay)
   - Coach mode: After user move, display threats and best continuation
5. Game save: Generate PGN from move list, save to database
6. Post-game: Offer to analyze the game immediately

**Estimated Effort**: 8-10 hours

### ⏳ Settings Screen
**Requirements** (from Assignment.txt):
- Engine configuration: Path, threads, hash size, default depth/time
- Analysis parameters: Adjust classification thresholds, book depth
- UI preferences: Theme (dark/light), board style, piece set
- Data management: Export/import database, clear history

**Implementation Plan**:
1. Create `dco/ui/screens/settings.py`
2. Settings storage: JSON file or new `Settings` table in database
3. UI sections:
   - **Engine**: Path picker, hash/threads spinners, depth/time sliders
   - **Analysis**: Threshold sliders (excellent/good/mistake/blunder), book depth spinbox
   - **UI**: Theme dropdown, board style preview, piece set selector
   - **Data**: Export button (dump to .sql), import button, reset button (with confirmation)
4. Apply settings: Pass to engine initialization, update classification thresholds dynamically
5. Validation: Ensure Stockfish path exists, hash/threads within reasonable limits

**Estimated Effort**: 4-5 hours

### ⏳ ECO Dataset Expansion
**Current State**: `dco/data/eco_data.json` contains ~20 sample openings  
**Goal**: Full ECO reference with ~500 openings

**Data Sources**:
- PGN of ECO openings (e.g., from Lichess opening database)
- SCID ECO classification file
- Online ECO databases (e.g., 365chess.com, chessgames.com)

**Format** (each entry):
```json
{
  "moves": "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3",
  "eco": "B70",
  "name": "Sicilian Defense",
  "variation": "Dragon Variation"
}
```

**Implementation**:
1. Download ECO data (PGN or JSON)
2. Parse into format above (move sequence in UCI notation)
3. Sort by move sequence length (longest first for prefix matching)
4. Replace current eco_data.json

**Estimated Effort**: 2-3 hours (data acquisition + parsing)

---

## 🎯 NEXT STEPS FOR NEW AI SESSION

### Immediate Actions (Priority Order)
1. **Test Practice Mode End-to-End**:
   ```powershell
   python app.py
   # 1. Import PGN (use sample game with mistakes)
   # 2. Analyze game
   # 3. Verify practice items generated
   # 4. Start practice session
   # 5. Test behavior: wrong move → red/green arrows, 1s pause, random switch, requeue
   # 6. Pass item 3 times → verify mastery (excluded from next session)
   ```

2. **Begin Milestone 5 (Statistics)**:
   - Create `statistics.py` screen with date range selector
   - Implement accuracy/Elo line charts using matplotlib
   - Query and aggregate analysis data
   - Add navigation button to main window

3. **Expand ECO Dataset**:
   - Download full ECO reference (suggest Lichess opening DB)
   - Convert to eco_data.json format
   - Test opening detection on imported games

4. **Code Quality Improvements**:
   - Add type hints where missing (especially ui/ modules)
   - Write unit tests for classification.py (Brilliant/Critical detection)
   - Add docstrings to public methods

### Questions to Ask User (If Needed)
- **Statistics**: Which charting library to use (matplotlib vs PySide6 native)?
- **Puzzles**: Which puzzle source to integrate first (Lichess puzzle DB)?
- **Play Mode**: Should engine "think" be shown (pondering animation)?
- **Settings**: Store settings in JSON file or database table?

### Common Commands Reference
```powershell
# Run application
python app.py

# Install dependencies
pip install -r requirements.txt

# Run tests (when added)
pytest tests/

# Check for errors
python -m py_compile dco/**/*.py

# Reset database (nuclear option)
Remove-Item dco_data.db; python app.py

# Git operations
git status
git add .
git commit -m "feat: add statistics dashboard"
git push origin main

# Build executable (future)
pyinstaller DailyChessOffline.spec
```

---

## 📚 KEY FILES REFERENCE

### Core Logic Files
| File | Line Count | Purpose | Key Functions |
|------|-----------|---------|---------------|
| `classification.py` | 515 | Move classification engine | `classify_move()`, `_is_brilliant_move()`, `_is_critical_position()` |
| `analysis.py` | 600 | Game analysis orchestration | `GameAnalyzer.analyze_game()`, `_estimate_performance_elo()`, `save_analysis_to_db()` |
| `practice.py` | 350 | Practice generation & SM-2 | `generate_practice_items()`, `select_practice_items()`, `update_practice_progress()` |
| `engine.py` | 400 | Stockfish UCI interface | `ChessEngine.analyze_position()`, `evaluate_multi_pv()` |
| `eco.py` | 120 | Opening detection | `ECODetector.detect_opening()` |
| `accuracy.py` | 200 | Accuracy calculation | `calculate_accuracy()` |

### Database Files
| File | Line Count | Purpose | Key Classes |
|------|-----------|---------|-------------|
| `models.py` | 450 | SQLAlchemy ORM schema | `Game`, `Analysis`, `Move`, `PracticeItem`, `PracticeProgress`, `TrainingSession` |
| `db.py` | 250 | DB initialization & migration | `Database`, `get_db()`, `_auto_migrate()` |

### UI Files
| File | Line Count | Purpose | Key Classes |
|------|-----------|---------|-------------|
| `main_window.py` | 300 | Main window + navigation | `MainWindow` |
| `screens/home.py` | 250 | Dashboard | `HomeScreen` |
| `screens/import_pgn.py` | 350 | PGN import interface | `ImportScreen` |
| `screens/library.py` | 400 | Game browser | `LibraryScreen` |
| `screens/analysis.py` | 600 | Game review | `AnalysisScreen`, `AnalysisWorker` (QThread) |
| `screens/practice.py` | 550 | Practice UI | `PracticeScreen` |
| `widgets/chessboard.py` | 400 | Interactive board | `ChessBoardWidget` |
| `widgets/move_list.py` | 300 | Move list display | `MoveListWidget` |

### Configuration Files
| File | Purpose | Notes |
|------|---------|-------|
| `requirements.txt` | Python dependencies | Python 3.11-3.13 compatible |
| `Assignment.txt` | Original specification | 610 lines, complete feature list |
| `.gitignore` | Git exclusions | Includes `dco/stockfish/*.exe` (108MB binary) |
| `dco_data.db` | SQLite database | Auto-created on first run, gitignored |

---

## 🧠 DEBUGGING TIPS

### Common Errors & Solutions

#### 1. `ImportError: No module named 'PySide6'`
**Solution**: Install dependencies
```powershell
pip install -r requirements.txt
```

#### 2. `FileNotFoundError: Stockfish binary not found`
**Solution**: Download Stockfish and place in `dco/stockfish/`
```powershell
# Download from https://stockfishchess.org/download/
# Place stockfish-windows-x86-64-avx2.exe in dco/stockfish/
# Or set custom path in Settings (future feature)
```

#### 3. `OperationalError: no such column: consecutive_first_try`
**Solution**: Delete database to trigger auto-migration
```powershell
Remove-Item dco_data.db
python app.py  # Auto-migration will create schema
```

#### 4. `DetachedInstanceError` in Practice Screen
**Solution**: Verify items are expunged in `select_practice_items()`
```python
# In practice.py, lines ~150-180
for item in items:
    _ = item.fen_start  # Force-load
    session.expunge(item)
```

#### 5. Classification Enum Errors
**Solution**: Ensure enum values are uppercase strings
```python
# Correct
classification = MoveClassification.BLUNDER  # "BLUNDER"

# Incorrect
classification = "blunder"  # Will cause ValueError
```

#### 6. Practice Items Not Appearing
**Checklist**:
1. Did analysis complete? (Check `Analysis` table has record)
2. Did `generate_practice_items()` execute? (Check `PracticeItem` table)
3. Are items mastered? (Check `consecutive_first_try < 3` in query)
4. Check category filters: Blunders/Mistakes enabled?

**Debug Query**:
```python
from dco.data.db import get_db
db = get_db()
session = db.Session()

# Count practice items by category
from dco.data.models import PracticeItem, PracticeProgress
items = session.query(PracticeItem).join(PracticeProgress).filter(
    PracticeProgress.consecutive_first_try < 3
).all()
print(f"Available items: {len(items)}")
for item in items:
    print(f"  {item.category}: FEN {item.fen_start[:20]}...")
```

### Logging & Debugging
**Current State**: Basic print statements in analysis/practice logic  
**Recommendation**: Add logging module for production

**Quick Debug Pattern**:
```python
# Add at top of file
import sys

# Debug output
print(f"[DEBUG] Variable value: {variable}", file=sys.stderr)

# Trace execution
print(f"[TRACE] Entering function: {function_name}", file=sys.stderr)
```

---

## 🔐 SENSITIVE INFORMATION
**None**: This is an offline desktop application with no API keys, credentials, or sensitive data.

**User Data**: All data stored locally in `dco_data.db` (SQLite). Users responsible for their own backups.

---

## 📄 LICENSE
See [LICENSE](LICENSE) file in repository root.

---

## 🤝 CONTRIBUTION GUIDELINES (for AI)

### Code Style
- **Python**: PEP 8 compliant, 4-space indentation
- **Type Hints**: Use where beneficial (especially public APIs)
- **Docstrings**: Google style for classes and complex functions
- **Comments**: Explain "why" not "what" (code should be self-explanatory)

### Commit Messages
- **Format**: `type(scope): description`
- **Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
- **Examples**:
  - `feat(statistics): add accuracy over time chart`
  - `fix(practice): resolve DetachedInstanceError on item selection`
  - `refactor(classification): extract PV verification logic`

### Testing
- **Priority**: Add tests for classification.py (Brilliant/Critical detection)
- **Framework**: pytest
- **Location**: `tests/` directory
- **Run**: `pytest tests/`

### Before Committing
1. Run application to verify no runtime errors
2. Test affected features manually
3. Check for print statements/debug code
4. Update PROGRESS.md if milestone completed
5. Update AI_STATE.md if architecture changes

---

## 🎉 SUCCESS CRITERIA

### Milestone 5 Complete When:
- [ ] Statistics screen accessible from navigation
- [ ] Date range filter functional
- [ ] Accuracy over time chart displays correctly
- [ ] Performance Elo over time chart displays correctly
- [ ] Blunders per game bar chart displays correctly
- [ ] Summary cards show correct aggregated data
- [ ] Charts update when date range changes

### Milestone 6 Complete When:
- [ ] Puzzle database schema implemented
- [ ] Puzzle import from standard format works
- [ ] Puzzles generated from user games (critical positions)
- [ ] Puzzle UI functional with hint system
- [ ] Puzzle difficulty progression implemented
- [ ] Puzzle progress tracked (rating changes based on performance)

### Full Project Complete When:
- [ ] All 6 milestones finished (Foundations, Engine, Classifications, Practice, Statistics, Puzzles)
- [ ] Play vs Computer mode functional
- [ ] Settings screen with engine/analysis configuration
- [ ] ECO dataset complete (~500 openings)
- [ ] Comprehensive test coverage (≥70%)
- [ ] User documentation complete (QUICKSTART.md, TROUBLESHOOTING.md)
- [ ] Application packaged as executable (PyInstaller)

---

## 📞 CONTACT & SUPPORT

**User**: GitHub user `dco-dev` (assume this is you)  
**Repository**: `https://github.com/dco-dev/DCO` (if public, adjust as needed)  
**Issues**: Use GitHub Issues for bug reports and feature requests

---

**END OF AI STATE DOCUMENT**  
*This document is your complete project context. Start by testing practice mode, then proceed to Milestone 5 (Statistics). Good luck!* 🚀
