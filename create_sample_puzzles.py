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
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 2 5",
            "solution": ["c4f7", "e8f7", "d1d5"],  # Bxf7+ Kxf7 Qd5+ forking king and rook
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
            "fen": "r2qkb1r/ppp2ppp/2n5/3pP3/2Bn4/5N2/PPP2PPP/RNBQK2R w KQkq - 0 7",
            "solution": ["d1d5"],  # Qd5 - Forking knight on e4 and bishop on c5
            "theme": PuzzleTheme.TACTIC,
            "rating": 1400,
            "source": "sample"
        },
        {
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2BPP3/5N2/PPP2PPP/RNBQK2R b KQkq - 0 5",
            "solution": ["c6d4", "f3d4", "c5f2"],  # Nd4! Nxd4 Bxf2+ winning the exchange
            "theme": PuzzleTheme.TACTIC,
            "rating": 1500,
            "source": "sample"
        },
        {
            "fen": "r2qkb1r/ppp2ppp/2np1n2/4p3/2B1P1b1/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 1 6",
            "solution": ["c4f7", "e8f7", "f3e5", "f7e8", "e5g4"],  # Bxf7+ Kxf7 Ne5+ Ke8 Nxg4 winning bishop
            "theme": PuzzleTheme.MATERIAL,
            "rating": 1600,
            "source": "sample"
        },
        {
            "fen": "r1bqk2r/pppp1ppp/2n2n2/2b5/2BpP3/5N2/PPP2PPP/RNBQ1RK1 w kq - 0 6",
            "solution": ["c4f7", "e8f7", "f3g5", "f7e8", "d1h5"],  # Bxf7+ Kxf7 Ng5+ Ke8 Qh5+ winning
            "theme": PuzzleTheme.MATE,
            "rating": 1700,
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
