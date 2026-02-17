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
            "solution": ["h5f7"],  # Qxf7# - Checkmate in one
            "theme": PuzzleTheme.MATE,
            "rating": 800,
            "source": "sample"
        },
        {
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5",
            "solution": ["c4f7", "e8f7", "f3g5", "f7e8", "d1h5"],  # Bxf7+ Kxf7 Ng5+ Ke8 Qh5+ winning
            "theme": PuzzleTheme.TACTIC,
            "rating": 1200,
            "source": "sample"
        },
        {
            "fen": "r1bqkb1r/pppppppp/2n2n2/8/3PP3/2N5/PPP2PPP/R1BQKBNR b KQkq - 1 3",
            "solution": ["f6e4"],  # Nxe4 - Win center pawn
            "theme": PuzzleTheme.MATERIAL,
            "rating": 1000,
            "source": "sample"
        },
        {
            "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4",
            "solution": ["f3g5", "d7d5", "g5f7"],  # Ng5 d5 Nxf7 winning rook (Fried Liver prep)
            "theme": PuzzleTheme.TACTIC,
            "rating": 1400,
            "source": "sample"
        },
        {
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2BPP3/5N2/PPP2PPP/RNBQK2R b KQkq - 0 5",
            "solution": ["c6d4", "f3d4", "c5d4"],  # Nd4! Nxd4 Bxd4 winning a pawn
            "theme": PuzzleTheme.TACTIC,
            "rating": 1500,
            "source": "sample"
        },
        {
            "fen": "r2qk2r/ppp2ppp/2np1n2/2b1p1B1/2B1P1b1/3P1N2/PPP2PPP/RN1QK2R w KQkq - 0 7",
            "solution": ["c4f7", "e8f7", "f3e5"],  # Bxf7+ Kxf7 Ne5+ forking king and queen
            "theme": PuzzleTheme.MATERIAL,
            "rating": 1600,
            "source": "sample"
        },
        {
            "fen": "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 0 3",
            "solution": ["d1f3", "d7d6", "c4f7"],  # Qf3 d6 Bxf7# - Scholar's mate
            "theme": PuzzleTheme.MATE,
            "rating": 700,
            "source": "sample"
        },
        {
            "fen": "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
            "solution": ["c6d4"],  # Nd4 - Center fork trick attacking queen and bishop
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
