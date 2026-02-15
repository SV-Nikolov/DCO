# Installing Stockfish for DCO

DCO requires Stockfish chess engine to analyze games. Here's how to install it:

## Windows

### Option 1: Download and Extract (Recommended)

1. **Download Stockfish**:
   - Go to https://stockfishchess.org/download/
   - Download the latest Windows version (e.g., "stockfish-windows-x86-64.zip")

2. **Extract to DCO Directory**:
   - Extract the ZIP file
   - Copy `stockfish.exe` (or `stockfish_x64.exe`) to your DCO folder: `C:\Source\DCO\`
   - Rename it to `stockfish.exe` if needed

3. **Verify Installation**:
   - Open PowerShell in the DCO folder
   - Run: `.\stockfish.exe`
   - You should see "Stockfish ... by ..." message
   - Type `quit` to exit

### Option 2: Install to System PATH

1. **Download Stockfish**: Same as above

2. **Create Stockfish Directory**:
   ```powershell
   mkdir "C:\Program Files\Stockfish"
   ```

3. **Copy Executable**:
   - Copy `stockfish.exe` to `C:\Program Files\Stockfish\`

4. **Add to PATH**:
   - Right-click "This PC" → Properties → Advanced System Settings
   - Click "Environment Variables"
   - Under "System variables", select "Path" → Edit
   - Click "New" and add: `C:\Program Files\Stockfish`
   - Click OK on all dialogs
   - Restart PowerShell/Command Prompt

5. **Verify**:
   ```powershell
   stockfish
   ```

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
1. Current directory: `C:\Source\DCO\stockfish.exe`
2. Subdirectory: `C:\Source\DCO\engines\stockfish.exe`
3. System PATH
4. Common install locations:
   - `C:\Program Files\Stockfish\stockfish.exe`
   - `C:\Program Files (x86)\Stockfish\stockfish.exe`
   - `%LOCALAPPDATA%\Stockfish\stockfish.exe`

**Recommended Solution**: Place `stockfish.exe` directly in `C:\Source\DCO\`

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

## Advanced: Custom Engine Path (Future Feature)

Settings screen will allow you to configure:
- Custom engine path
- Analysis depth
- Time per move
- Number of threads
- Hash table size

For now, DCO auto-detects Stockfish from standard locations.
