"""
Simple tests to verify DCO installation and basic functionality.
Run with: pytest tests/test_basic.py
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dco.data.models import Base, Game, GameSource


def test_database_creation():
    """Test that database tables can be created."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)
    
    # Check that tables were created
    assert 'games' in Base.metadata.tables
    assert 'analyses' in Base.metadata.tables
    assert 'moves' in Base.metadata.tables
    assert 'practice_items' in Base.metadata.tables


def test_game_model():
    """Test creating a game model instance."""
    game = Game(
        source=GameSource.PGN_IMPORT,
        white="Player1",
        black="Player2",
        result="1-0",
        pgn_text="[White \"Player1\"] [Black \"Player2\"] 1. e4 e5"
    )
    
    assert game.white == "Player1"
    assert game.black == "Player2"
    assert game.result == "1-0"
    assert game.source == GameSource.PGN_IMPORT


def test_database_insert():
    """Test inserting a game into database."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    game = Game(
        source=GameSource.PGN_IMPORT,
        white="TestWhite",
        black="TestBlack",
        result="1/2-1/2",
        pgn_text="[White \"TestWhite\"] [Black \"TestBlack\"] 1. e4 e5 2. Nf3"
    )
    
    session.add(game)
    session.commit()
    
    # Query back
    retrieved = session.query(Game).filter_by(white="TestWhite").first()
    assert retrieved is not None
    assert retrieved.black == "TestBlack"
    
    session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
