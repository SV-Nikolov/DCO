#!/usr/bin/env python
"""Create test games for batch analysis testing."""
import sys
from dco.data.db import Database
from dco.data.models import Game
from dco.core.pgn_import import PGNImporter

test_pgn = """
[Event "Test 1"]
[Site "?"]
[Date "2024.01.01"]
[Round "?"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 
8. c3 Na5 9. Ba4 c5 10. d4 Qc7 11. Nbd2 O-O 12. dxe5 dxe5 13. Qe2 Nxe4 
14. Nxe4 Qb6 1-0
"""

# Initialize DB
db = Database("dco/data/chess.db")
db.init_db()

session = db.get_session()
games = session.query(Game).all()
print(f"Current games in DB: {len(games)}")

if len(games) == 0:
    print("Importing test game...")
    try:
        importer = PGNImporter(session)
        imported, errors = importer.import_pgn_text(test_pgn, skip_duplicates=False)
        if imported:
            print(f"Imported {len(imported)} game(s)")
            for g in imported:
                print(f"  - Game {g.id}: {g.white} vs {g.black}")
        if errors:
            print(f"Errors: {errors}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Already have {len(games)} games")
    for g in games[:3]:
        print(f"  - Game {g.id}: {g.white} vs {g.black}")

session.close()
