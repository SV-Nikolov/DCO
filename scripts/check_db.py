import sqlite3

conn = sqlite3.connect('dco_data.db')
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:")
for t in tables:
    print(f"  - {t[0]}")

# Check puzzles table structure
if ('puzzles',) in tables:
    print("\nPuzzles table structure:")
    cursor.execute("PRAGMA table_info(puzzles)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]}: {col[2]}")
else:
    print("\nNo puzzles table found")

conn.close()
