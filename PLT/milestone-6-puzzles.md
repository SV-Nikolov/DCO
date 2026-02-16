# Milestone 6: Puzzles System

**Date**: February 17, 2026  
**Status**: Starting Implementation  

## Summary
Implement a comprehensive puzzle system including:
- Puzzle database model and storage
- Puzzle import from standard formats (Lichess CSV, PGN)
- Puzzle generation from user game critical positions
- Interactive puzzle solving UI
- Hint system and difficulty progression
- Puzzle statistics and tracking

## Key Features
1. **Puzzle Model** with theme, rating, solution moves
2. **Puzzle Import** from Lichess and other sources
3. **Puzzle Generation** from critical positions in analyzed games
4. **Interactive UI** similar to practice mode with hints
5. **Difficulty Progression** based on user performance
6. **Progress Tracking** (solved/learning/unsolved)

## Files to Create/Modify
- `dco/data/models.py` - Add Puzzle and PuzzleProgress models
- `dco/puzzles/puzzle_manager.py` - Core puzzle logic
- `dco/puzzles/importer.py` - Puzzle import from various formats
- `dco/puzzles/generator.py` - Generate puzzles from user games
- `dco/ui/screens/puzzles.py` - Interactive puzzle UI
- `dco/ui/main_window.py` - Add puzzles navigation button

## Implementation Order
1. Database models (Puzzle, PuzzleProgress, PuzzleTheme)
2. Puzzle manager and storage logic
3. Import functionality
4. Generation from games
5. UI screen implementation
6. Navigation integration
7. Testing and refinement

## Critical Notes
- Reuse Practice Mode architecture for interactive board
- Use enum for puzzle themes (MATE, MATERIAL, TACTIC, DEFENSE, ENDGAME)
- Rating system: 800-2800 Elo-like scale
- Solution is JSON array of moves (allows multi-move sequences unlike practice)
- Hint system: first move, threat explanation, full line

---

**Next**: Start with database model implementation in `dco/data/models.py`
