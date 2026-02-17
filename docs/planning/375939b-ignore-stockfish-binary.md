# Commit: 375939b - Ignore Stockfish binary

Date: 2026-02-16

## Summary
- Ignore local Stockfish Windows binaries to prevent accidental commits of large files.

## Files Changed
- .gitignore

## Critical Notes
- Stockfish binaries should be kept locally under dco/stockfish and never committed.
- GitHub rejects files over 100 MB; the ignore rule prevents future push failures.
