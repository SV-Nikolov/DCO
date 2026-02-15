"""
PGN import functionality for DCO.
Handles importing chess games from PGN format.
"""

from datetime import datetime
from typing import List, Optional, Tuple
import chess.pgn
import io
from sqlalchemy.orm import Session

from ..data.models import Game, GameSource


class PGNImporter:
    """Handles importing games from PGN format."""
    
    def __init__(self, db_session: Session):
        """
        Initialize PGN importer.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.session = db_session
    
    def import_pgn_text(
        self, 
        pgn_text: str, 
        skip_duplicates: bool = True
    ) -> Tuple[List[Game], List[str]]:
        """
        Import games from PGN text.
        
        Args:
            pgn_text: PGN format text containing one or more games
            skip_duplicates: If True, skip games that appear to be duplicates
            
        Returns:
            Tuple of (imported_games, error_messages)
        """
        imported = []
        errors = []
        
        # Parse PGN text
        pgn_io = io.StringIO(pgn_text)
        
        while True:
            try:
                game = chess.pgn.read_game(pgn_io)
                if game is None:
                    break
                
                # Extract game data
                headers = game.headers
                
                # Check for duplicate
                if skip_duplicates:
                    if self._is_duplicate(headers, game):
                        errors.append(
                            f"Skipped duplicate: {headers.get('White', '?')} vs "
                            f"{headers.get('Black', '?')} on {headers.get('Date', '?')}"
                        )
                        continue
                
                # Create Game object
                db_game = self._create_game_from_pgn(game, headers, pgn_text)
                
                # Add to session
                self.session.add(db_game)
                imported.append(db_game)
                
            except Exception as e:
                errors.append(f"Error parsing game: {str(e)}")
                continue
        
        # Commit all imported games
        if imported:
            try:
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                errors.append(f"Error saving games to database: {str(e)}")
                return [], errors
        
        return imported, errors
    
    def import_pgn_file(
        self, 
        file_path: str, 
        skip_duplicates: bool = True
    ) -> Tuple[List[Game], List[str]]:
        """
        Import games from a PGN file.
        
        Args:
            file_path: Path to PGN file
            skip_duplicates: If True, skip games that appear to be duplicates
            
        Returns:
            Tuple of (imported_games, error_messages)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                pgn_text = f.read()
            return self.import_pgn_text(pgn_text, skip_duplicates)
        except Exception as e:
            return [], [f"Error reading file: {str(e)}"]
    
    def _create_game_from_pgn(
        self, 
        game: chess.pgn.Game, 
        headers: chess.pgn.Headers,
        original_pgn: str
    ) -> Game:
        """
        Create a Game model instance from a chess.pgn.Game object.
        
        Args:
            game: chess.pgn.Game object
            headers: Game headers
            original_pgn: Original PGN text
            
        Returns:
            Game model instance
        """
        # Extract moves in SAN notation
        board = game.board()
        moves_san = []
        for move in game.mainline_moves():
            moves_san.append(board.san(move))
            board.push(move)
        
        # Parse Elo ratings (handle '?' and invalid values)
        def parse_elo(elo_str: Optional[str]) -> Optional[int]:
            if not elo_str or elo_str == '?':
                return None
            try:
                return int(elo_str)
            except ValueError:
                return None
        
        white_elo = parse_elo(headers.get('WhiteElo'))
        black_elo = parse_elo(headers.get('BlackElo'))
        
        # Create Game instance
        db_game = Game(
            source=GameSource.PGN_IMPORT,
            event=headers.get('Event', ''),
            site=headers.get('Site', ''),
            date=headers.get('Date', ''),
            round=headers.get('Round', ''),
            white=headers.get('White', ''),
            black=headers.get('Black', ''),
            result=headers.get('Result', '*'),
            white_elo=white_elo,
            black_elo=black_elo,
            time_control=headers.get('TimeControl', ''),
            termination=headers.get('Termination', ''),
            pgn_text=str(game),  # Store the parsed PGN
            moves_san=' '.join(moves_san),
            created_at=datetime.utcnow()
        )
        
        return db_game
    
    def _is_duplicate(
        self, 
        headers: chess.pgn.Headers, 
        game: chess.pgn.Game
    ) -> bool:
        """
        Check if a game is a duplicate of an existing game in the database.
        
        Args:
            headers: Game headers
            game: chess.pgn.Game object
            
        Returns:
            True if duplicate found, False otherwise
        """
        # Extract key identifying information
        white = headers.get('White', '')
        black = headers.get('Black', '')
        date = headers.get('Date', '')
        
        # Get first 10 moves for comparison
        board = game.board()
        moves = []
        for i, move in enumerate(game.mainline_moves()):
            if i >= 10:
                break
            moves.append(board.san(move))
            board.push(move)
        moves_start = ' '.join(moves)
        
        # Query for similar games
        if white and black and date:
            existing = self.session.query(Game).filter(
                Game.white == white,
                Game.black == black,
                Game.date == date
            ).first()
            
            if existing and existing.moves_san:
                # Check if first 10 moves match
                existing_moves_start = ' '.join(existing.moves_san.split()[:10])
                if existing_moves_start == moves_start:
                    return True
        
        return False


def import_pgn(
    db_session: Session, 
    pgn_text: str, 
    skip_duplicates: bool = True
) -> Tuple[List[Game], List[str]]:
    """
    Convenience function to import PGN text.
    
    Args:
        db_session: SQLAlchemy database session
        pgn_text: PGN format text
        skip_duplicates: If True, skip duplicate games
        
    Returns:
        Tuple of (imported_games, error_messages)
    """
    importer = PGNImporter(db_session)
    return importer.import_pgn_text(pgn_text, skip_duplicates)
