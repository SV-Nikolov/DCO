"""
Create sample puzzles for testing the puzzle system.
"""

from dco.data.db import get_db
from dco.puzzles import PuzzleManager
from dco.data.models import PuzzleTheme

def create_sample_puzzles():
    """Create sample puzzles for testing."""
    db = get_db()
    puzzle_manager = PuzzleManager(db)
    
    sample_puzzles = [
        {
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
            "solution": ["h5f7"],  # Scholar's mate pattern
            "theme": PuzzleTheme.MATE,
            "rating": 800,
            "source": "sample"
        },
        {
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 2 5",
            "solution": ["c4f7", "e8f7", "d1d5"],  # Fork king and rook
            "theme": PuzzleTheme.TACTIC,
            "rating": 1200,
            "source": "sample"
        },
        {
            "fen": "r1bqkb1r/pppppppp/2n2n2/8/3PP3/2N5/PPP2PPP/R1BQKBNR b KQkq - 1 3",
            "solution": ["f6e4"],  # Win pawn
            "theme": PuzzleTheme.MATERIAL,
            "rating": 1000,
            "source": "sample"
        },
        {
            "fen": "6k1/5ppp/8/8/8/6PP/5PK1/8 w - - 0 1",
            "solution": ["g2f3", "g8f7", "f3e4"],  # King endgame technique
            "theme": PuzzleTheme.ENDGAME,
            "rating": 1400,
            "source": "sample"
        },
        {
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2BPP3/5N2/PPP2PPP/RNBQK2R b KQkq - 0 5",
            "solution": ["c6d4", "f3d4", "c5f2"],  # Italian Game trap
            "theme": PuzzleTheme.TACTIC,
            "rating": 1500,
            "source": "sample"
        },
        {
            "fen": "r2qkb1r/ppp2ppp/2np1n2/4p3/2B1P1b1/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 1 6",
            "solution": ["c4f7", "e8f7", "f3e5", "f7e7", "e5g4"],  # Win material
            "theme": PuzzleTheme.MATERIAL,
            "rating": 1600,
            "source": "sample"
        },
        {
            "fen": "6k1/5p1p/4p1p1/3pP3/1ppP4/1P3P2/2P3PP/6K1 w - - 0 1",
            "solution": ["f3f4", "c4c3", "g2g4"],  # Pawn endgame
            "theme": PuzzleTheme.ENDGAME,
            "rating": 1700,
            "source": "sample"
        },
        {
            "fen": "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
            "solution": ["c6d4"],  # Center fork trick
            "theme": PuzzleTheme.TACTIC,
            "rating": 1300,
            "source": "sample"
        },
    ]
    
    created_count = 0
    for puzzle_data in sample_puzzles:
        try:
            puzzle = puzzle_manager.create_puzzle(
                fen=puzzle_data["fen"],
                solution_moves=puzzle_data["solution"],
                theme=puzzle_data["theme"],
                rating=puzzle_data["rating"],
                source=puzzle_data["source"],
            )
            created_count += 1
            theme_name = puzzle_data["theme"].value if puzzle_data["theme"] else "Unknown"
            print(f"✓ Created puzzle: {theme_name} (Rating: {puzzle_data['rating']})")
        except Exception as e:
            print(f"✗ Failed to create puzzle: {e}")
    
    print(f"\n✓ Created {created_count} sample puzzles!")
    print("You can now navigate to the Puzzles screen in the app.")

if __name__ == "__main__":
    create_sample_puzzles()
