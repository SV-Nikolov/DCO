"""Test full puzzle sequences."""
from dco.data.db import get_db
from dco.data.models import Puzzle
import chess

db = get_db()
session = db.get_session()

# Test puzzle 2 which has multiple moves
puzzle = session.query(Puzzle).filter(Puzzle.id == 2).first()

print(f"Testing Puzzle {puzzle.id}: {puzzle.theme.value} (Rating {puzzle.rating})")
print(f"FEN: {puzzle.fen}")
print(f"Solution: {puzzle.solution_line}\n")

board = chess.Board(puzzle.fen)
print(f"Initial position - Turn: {'White' if board.turn else 'Black'}")

for i, move_uci in enumerate(puzzle.solution_line):
    print(f"\nMove {i}: {move_uci}")
    print(f"  Current turn: {'White' if board.turn else 'Black'}")
    
    # Check if move is legal
    legal_moves = [m.uci() for m in board.legal_moves]
    is_legal = move_uci in legal_moves
    
    print(f"  Legal? {is_legal}")
    
    if not is_legal:
        print(f"  ERROR: Move is illegal!")
        print(f"  Legal moves: {legal_moves[:10]}")
        break
    else:
        move = chess.Move.from_uci(move_uci)
        san = board.san(move)
        print(f"  SAN: {san}")
        board.push(move)
        print(f"  Board after move:\n{board}")

session.close()
