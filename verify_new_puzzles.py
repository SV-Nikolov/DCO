"""Verify new puzzle solutions are legal."""
import chess

# Test the new puzzles
puzzles = [
    {
        "id": 1,
        "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
        "solution": ["h5f7"],
    },
    {
        "id": 2,
        "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5",
        "solution": ["c4f7", "e8f7", "f3g5", "f7e8", "d1h5"],
    },
    {
        "id": 3,
        "fen": "r1bqkb1r/pppppppp/2n2n2/8/3PP3/2N5/PPP2PPP/R1BQKBNR b KQkq - 1 3",
        "solution": ["f6e4"],
    },
    {
        "id": 4,
        "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4",
        "solution": ["f3g5", "d7d5", "g5f7"],
    },
    {
        "id": 5,
        "fen": "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2BPP3/5N2/PPP2PPP/RNBQK2R b KQkq - 0 5",
        "solution": ["c6d4", "f3d4", "c5d4"],
    },
    {
        "id": 6,
        "fen": "r2qk2r/ppp2ppp/2np1n2/2b1p1B1/2B1P1b1/3P1N2/PPP2PPP/RN1QK2R w KQkq - 0 7",
        "solution": ["c4f7", "e8f7", "f3e5"],
    },
    {
        "id": 7,
        "fen": "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 0 3",
        "solution": ["d1f3", "d7d6", "c4f7"],
    },
    {
        "id": 8,
        "fen": "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
        "solution": ["c6d4"],
    },
]

print("Verifying puzzle solutions...\n")

all_valid = True
for puzzle in puzzles:
    print(f"Puzzle {puzzle['id']}:")
    board = chess.Board(puzzle["fen"])
    
    valid = True
    for i, move_uci in enumerate(puzzle["solution"]):
        legal_moves = [m.uci() for m in board.legal_moves]
        if move_uci not in legal_moves:
            print(f"  ✗ Move {i} '{move_uci}' is ILLEGAL!")
            print(f"    Legal moves: {legal_moves[:10]}")
            valid = False
            all_valid = False
            break
        else:
            move = chess.Move.from_uci(move_uci)
            san = board.san(move)
            print(f"  ✓ Move {i}: {san} ({move_uci})")
            board.push(move)
    
    if valid:
        print(f"  ALL MOVES VALID ✓\n")
    else:
        print()

if all_valid:
    print("\n✓ All puzzles are valid!")
else:
    print("\n✗ Some puzzles have errors!")
