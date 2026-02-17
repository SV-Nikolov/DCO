"""
Database migration script to add puzzle system columns.
Adds missing columns to existing puzzles table.
"""

import sqlite3
from pathlib import Path

def migrate_puzzle_columns():
    """Add missing columns to puzzles table."""
    db_path = Path(__file__).parent / "chess_data.db"
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if puzzles table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='puzzles'")
    if not cursor.fetchone():
        print("Puzzles table doesn't exist yet - creating fresh schema")
        conn.close()
        from dco.data.db import get_db
        from dco.data.models import Base
        db = get_db()
        Base.metadata.create_all(db.engine)
        print("✓ Fresh database schema created")
        return
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(puzzles)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    print(f"Existing columns: {existing_columns}")
    
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
    
    # Check if puzzle_progress table exists, create if not
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='puzzle_progress'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE puzzle_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                puzzle_id INTEGER NOT NULL UNIQUE,
                due_date DATETIME NOT NULL,
                interval_days FLOAT DEFAULT 1.0,
                ease_factor FLOAT DEFAULT 2.5,
                repetitions INTEGER DEFAULT 0,
                lapses INTEGER DEFAULT 0,
                consecutive_first_try INTEGER DEFAULT 0,
                last_result VARCHAR(20),
                attempts_total INTEGER DEFAULT 0,
                attempts_correct INTEGER DEFAULT 0,
                updated_at DATETIME,
                FOREIGN KEY(puzzle_id) REFERENCES puzzles(id)
            )
        """)
        cursor.execute("CREATE INDEX idx_puzzle_progress_due ON puzzle_progress(due_date)")
        print("✓ Created puzzle_progress table")
    
    # Add index for theme if it doesn't exist
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
