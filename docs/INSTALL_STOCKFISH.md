# Installing Stockfish for DCO

**IMPORTANT**: Stockfish is **NOT** included with DCO. You must download and install it separately.

Stockfish is a free, open-source chess engine. DCO uses it for game analysis and as an opponent when playing against the computer.

## Quick Start

1. **Download Stockfish** from https://stockfishchess.org/download/
2. **Extract/Install** it to any location on your computer
3. **Launch DCO** - it will auto-detect Stockfish from standard locations
4. **If auto-detection fails**: Settings → Engine → "Browse..." → Select stockfish executable → Restart DCO

---

## Windows

### Option 1: Download and Extract (Auto-Detection)

1. **Download Stockfish**:
   - Go to https://stockfishchess.org/download/
   - Download the latest Windows version (e.g., "stockfish-windows-x86-64.zip")

2. **Extract to Program Files**:
   - Right-click the ZIP → Extract All
   - Choose location: `C:\Program Files\Stockfish`
   - Extract all files there

3. **Launch DCO**: `python app.py`
   - Stockfish will be auto-detected from Program Files

### Option 2: Manual Configuration

If Stockfish is in a non-standard location or auto-detection fails:

1. **Install Stockfish** anywhere you prefer
2. **Launch DCO** and open Settings
3. Go to Engine tab
4. Click **"Browse..."** button
5. Navigate to your `stockfish.exe` (or `stockfish` on macOS/Linux)
6. Click **"Save Settings"**
7. Restart DCO for changes to take effect

## Quick Test in DCO

After installing Stockfish:

1. Start DCO: `python app.py`
2. Import a PGN game (Import screen)
3. Go to Library and double-click the game
4. Click "Analyze Game"
5. If successful, you'll see analysis progress

## Troubleshooting

### "Stockfish not found" Error

**Check if Stockfish is accessible**:
```powershell
# From DCO directory
.\stockfish.exe

# Or if in PATH
stockfish
```

**DCO looks for Stockfish in these locations (in order)**:
1. System PATH - `stockfish` or `stockfish.exe` command
2. Windows Standard Paths:
   - `C:\Program Files\Stockfish\stockfish.exe`
   - `C:\Program Files (x86)\Stockfish\stockfish.exe`
   - `%APPDATA%\Local\Stockfish\stockfish.exe`
3. Downloads folder - `~/Downloads/stockfish*`
4. macOS Homebrew: `/usr/local/bin/stockfish` or `/opt/homebrew/bin/stockfish`
5. Linux standard: `/usr/bin/stockfish` or `/usr/local/bin/stockfish`

**If auto-detection doesn't work**:
1. Go to Settings → Engine tab
2. Click "Browse..." to manually select your stockfish executable
3. Restart DCO

### Version Compatibility

- DCO works with **Stockfish 14+** (latest version recommended)
- Older versions may work but are not tested

### Performance Tips

- Default settings: 20 depth, 0.5 seconds per move
- For faster analysis: Lower depth in Analysis screen
- For more accurate analysis: Increase time per move (future setting)

## macOS / Linux

### macOS
```bash
# Using Homebrew
brew install stockfish

# Verify
which stockfish
```

### Linux
```bash
# Ubuntu/Debian
sudo apt install stockfish

# Fedora
sudo dnf install stockfish

# Arch
sudo pacman -S stockfish

# Verify
which stockfish
```

## Advanced: Engine Configuration

In DCO Settings, you can configure:

- **Engine Path**: Click "Browse..." to select a custom stockfish location
- **CPU Threads**: Number of threads for analysis (1-16, more = faster but more CPU intensive)
- **Hash Table Size**: Memory for analysis (16-4096 MB, more = better but uses more RAM)
- **Analysis Depth**: Default search depth for analysis (higher = more accurate but slower)
- **Time per Move**: How long the engine analyzes each position (seconds)

For most users, the defaults work well. Adjust if needed for your system.
