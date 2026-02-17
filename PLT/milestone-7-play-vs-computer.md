# Milestone 7: Play vs Computer (Engine Play)

**Date**: February 17, 2026  
**Status**: Planning - Not Started  

## Summary
Implement the "Play vs Computer" feature allowing users to play against Stockfish with:
- Configurable opponent strength (1000-3200 Elo)
- Time controls (Bullet/Blitz/Rapid/Custom)
- Color selection (White/Black/Random)
- Optional features: Increments, Takebacks, Hints, Coach Mode
- Auto-save finished games to database with automatic analysis

## Requirements

### Core Features
1. **Pre-game Setup**
   - Opponent strength selector: 1000-3200 Elo (slider or dropdown)
   - Time control presets:
     - Bullet: 1-2 min
     - Blitz: 3-5 min
     - Rapid: 8-10 min
     - Custom: 1-10 minutes
   - Color selection: White / Black / Random
   - Increment: 0-5 seconds
   - Optional toggles:
     - Takebacks: On/Off
     - Hints: On/Off (show top N engine moves on request)
     - Coach mode: Highlight threats after each move
     - Auto-save: On/Off (default: On)

2. **In-Game Interface**
   - Interactive chessboard with drag-and-drop or click-to-move
   - Move list with standard notation
   - Clocks for both players (countdown timers)
   - Game controls:
     - Resign button
     - Offer Draw (optional - engine can accept/decline)
     - Takeback (if enabled in settings)
     - Request Hint (if enabled)
     - Save & Exit (save game state and exit)
     - New Game / Restart
   - Status display: Turn indicator, game result, check/checkmate alerts

3. **Engine Controller**
   - Stockfish integration with skill level mapping
   - Elo → Skill level + depth/time limits
   - Move calculation with proper UCI protocol
   - Support for giving hints (top N moves with evaluations)
   - Coach mode analysis (tactical threats detection)

4. **Game Clock Logic**
   - Countdown timers with increment support
   - Flag detection (time runs out)
   - Pause/resume functionality
   - Time display in MM:SS format

5. **Game Saving & Analysis**
   - Auto-save completed games to database
   - Store metadata: opponent Elo, time control, result, termination reason
   - Automatic post-game analysis (optional, can be deferred)
   - PGN generation with headers

## Implementation Plan

### Phase 1: Engine Controller (engine_controller.py)
Create a manager for Stockfish:
- `EngineController` class
- `set_elo_strength(elo: int)` - Map Elo to skill/depth/time
- `get_best_move(board, time_limit)` - Calculate engine move
- `get_top_moves(board, n=3)` - Get hints
- `analyze_threats(board)` - For coach mode
- `start()` / `quit()` - Lifecycle management

### Phase 2: Game Clock (game_clock.py)
Timer logic:
- `GameClock` class
- `start()` / `pause()` / `resume()`
- `add_increment(seconds)`
- `get_time_remaining()` - Returns seconds remaining
- `is_flagged()` - Check if time expired
- Qt timer integration for UI updates

### Phase 3: Play Screen UI (play.py)
Full interactive screen:
- Setup panel (pre-game configuration)
- Game board area
- Move list widget
- Clock displays
- Control buttons
- Status/feedback labels
- Modal dialogs for game end

### Phase 4: Game State Manager (play_game_manager.py)
Orchestrate game flow:
- `PlayGameManager` class
- Track game state (board, moves, clocks, result)
- Handle user moves (validation, clock updates)
- Trigger engine moves
- Process special actions (resign, draw, takeback)
- Save game to database
- Generate PGN

### Phase 5: Integration & Testing
- Wire engine controller to play screen
- Test all time controls
- Test Elo strength levels
- Verify game saving
- Test edge cases (stalemate, insufficient material, threefold repetition)
- Performance testing (engine responsiveness)

## Technical Details

### Elo to Skill Mapping
Stockfish skill level (0-20) + time/depth limits:
```
1000 Elo → Skill 0, Depth 1, Time 10ms
1200 Elo → Skill 2, Depth 2, Time 20ms
1400 Elo → Skill 4, Depth 3, Time 50ms
1600 Elo → Skill 6, Depth 5, Time 100ms
1800 Elo → Skill 8, Depth 8, Time 200ms
2000 Elo → Skill 10, Depth 10, Time 500ms
2200 Elo → Skill 13, Depth 12, Time 1000ms
2400 Elo → Skill 16, Depth 15, Time 2000ms
2600 Elo → Skill 18, Depth 18, Time 5000ms
2800+ Elo → Skill 20, No limits
```

### Database Schema
Reuse existing `Game` model:
- `source = "engine_game"`
- `white/black = "User" / "Stockfish (2000)"`
- Store engine Elo in black/white_elo fields
- `time_control = "5+3"` format
- `termination = "Normal" / "Time forfeit" / "Resignation"`

### Time Control Format
Store as: `minutes+increment` (e.g., "5+3", "10+0", "1+1")

## Architecture Notes

### Threading Considerations
- Engine calculations should run in separate thread to avoid UI freezing
- Use Qt signals/slots for thread-safe communication
- Clock updates should be smooth (100ms QPaintTimer)

### UCI Protocol
- Use `python-chess` engine integration
- Configure Stockfish UCI options: Skill Level, Threads, Hash
- Proper engine lifecycle (start on game begin, quit on game end)

## Success Criteria
- [ ] User can start a game vs Stockfish
- [ ] Configurable opponent strength works correctly
- [ ] Time controls function properly with increments
- [ ] Engine plays reasonable moves for selected Elo
- [ ] Game saves to database on completion
- [ ] All game controls work (resign, takeback, hints)
- [ ] Clock displays update smoothly
- [ ] Game results are detected correctly (checkmate, stalemate, timeout, resignation)
- [ ] PGN export works

## Future Enhancements (Post-MVP)
- Opening book integration
- Personality settings (aggressive/defensive engine style)
- Blindfold mode
- Move animations
- Sound effects
- Tournament mode (play multiple games)
- Engine analysis during game (spectator mode)
