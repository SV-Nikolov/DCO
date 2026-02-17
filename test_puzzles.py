"""Test puzzle validity."""
from dco.data.db import get_db
from dco.data.models import Puzzle
import chess

db = get_db()
session = db.get_session()

puzzles = session.query(Puzzle).all()
print(f"Found {len(puzzles)} puzzles\n")

for puzzle in puzzles:
    print(f"\nPuzzle {puzzle.id}: {puzzle.theme.value if puzzle.theme else 'None'} (Rating {puzzle.rating})")
    print(f"  FEN: {puzzle.fen}")
    
    board = chess.Board(puzzle.fen)
    print(f"  Turn: {'White' if board.turn else 'Black'}")
    print(f"  Solution: {puzzle.solution_line}")
    
    # Check if first move is legal
    if puzzle.solution_line:
        first_move_uci = puzzle.solution_line[0]
        legal_moves = [m.uci() for m in board.legal_moves]
        is_legal = first_move_uci in legal_moves
        
        print(f"  First move '{first_move_uci}' legal? {is_legal}")
        if not is_legal:
            print(f"  ERROR: Illegal first move!")
            print(f"  Legal moves: {legal_moves[:10]}...")

session.close()
