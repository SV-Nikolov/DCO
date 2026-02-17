# Quick Start Guide

## Get Started in 5 Minutes

### Step 1: Install Dependencies (2 min)

```bash
pip install -r requirements.txt
```

### Step 2: Get Stockfish (1 min)

Download from: https://stockfishchess.org/download/

**Windows**: Extract `stockfish.exe` to the DCO folder (same directory as `app.py`)

### Step 3: Run the App (30 sec)

```bash
python app.py
```

### Step 4: Import a Game (1 min)

1. Click **Import** in the left navigation
2. Paste this example PGN:

```
[Event "Test Game"]
[Site "Chess.com"]
[Date "2026.02.15"]
[White "Magnus Carlsen"]
[Black "Hikaru Nakamura"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 O-O 
8. c3 d6 9. h3 Nb8 10. d4 Nbd7 11. Nbd2 Bb7 12. Bc2 Re8 13. Nf1 Bf8 
14. Ng3 g6 15. a4 c5 16. d5 c4 17. Bg5 Qc7 18. Qd2 Nc5 19. Bh6 Bxh6 
20. Qxh6 Nfxe4 21. Nxe4 Nxe4 22. Rxe4 Qd7 23. Rae1 Kf8 24. Qh4 1-0
```

3. Click **Import Games**

### Step 5: View Your Library (30 sec)

Click **Library** to see your imported game with search and filter options.

## What's Working Now

✅ **Import Games**: Paste PGN or import from files  
✅ **Game Library**: Search, filter, and browse games  
✅ **Home Dashboard**: Quick stats and recent activity  

## Coming Next

The following features are implemented but not yet connected to the UI:

🔧 **Game Analysis**: Analyze with Stockfish engine (code ready, UI pending)  
🔧 **Practice Mode**: Train on your mistakes (in development)  
🔧 **Statistics**: Track your progress over time (in development)  
🔧 **Puzzles**: Solve tactical puzzles (in development)  

## Sample Chess.com PGN

To test with your own games from Chess.com:

1. Go to Chess.com
2. Click on a game you played
3. Click the **Share** button
4. Copy the PGN
5. Paste into DCO's Import screen

## Need Help?

- See [SETUP.md](SETUP.md) for detailed installation
- See [PROGRESS.md](PROGRESS.md) for feature status
- See [Assignment.txt](Assignment.txt) for complete specifications

---

**Tip**: The database (`dco_data.db`) is created automatically in the application directory. You can delete it to start fresh if needed.
