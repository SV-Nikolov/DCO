"""
Database migration script to add puzzle system columns.
Adds missing columns to existing puzzles table.
"""

import sqlite3
from pathlib import Path

def migrate_puzzle_columns():
    """Add missing columns to puzzles table."""
    # First ensure database exists with all current tables
    print("Creating/updating database schema...")
    from dco.data.db import get_db
    from dco.data.models import Base
    db = get_db()
    Base.metadata.create_all(db.engine)
    print("✓ Base schema created")
    
    db_path = Path(__file__).parent / "dco_data.db"
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if puzzles table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='puzzles'")
    if not cursor.fetchone():
        print("⚠ Puzzles table doesn't exist - it should have been created above")
        conn.close()
        return
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(puzzles)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    print(f"Existing puzzle columns: {existing_columns}")
    
    # Add missing columns
    migrations = []
    
    if 'theme' not in existing_columns:
        migrations.append(("ADD COLUMN theme VARCHAR(20)", "theme"))
    
    if 'source_game_id' not in existing_columns:
        migrations.append(("ADD COLUMN source_game_id INTEGER", "source_game_id"))
    
    # Execute migrations
    for sql_fragment, col_name in migrations:
        try:
            cursor.execute(f"ALTER TABLE puzzles {sql_fragment}")
            print(f"✓ Added column: {col_name}")
        except sqlite3.OperationalError as e:
            print(f"⚠ Column {col_name} migration skipped: {e}")
    
    # Add index for theme if it doesn't exist
    if 'theme' not in existing_columns:
        try:
            cursor.execute("CREATE INDEX idx_puzzle_theme ON puzzles(theme)")
            print("✓ Created index on puzzles.theme")
        except sqlite3.OperationalError:
            print("⚠ Index idx_puzzle_theme already exists")
    
    conn.commit()
    conn.close()
    print("\n✓ Migration complete!")

if __name__ == "__main__":
    migrate_puzzle_columns()
