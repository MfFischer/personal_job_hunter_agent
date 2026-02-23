import sqlite3
import logging

DB_PATH = "g:/automation projects/personal job hunter/data/jobs.db"

def migrate_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("SELECT is_reported FROM applications LIMIT 1")
    except sqlite3.OperationalError:
        print("Column 'is_reported' not found. Migrating...")
        try:
            cursor.execute("ALTER TABLE applications ADD COLUMN is_reported BOOLEAN DEFAULT 0")
            cursor.execute("ALTER TABLE applications ADD COLUMN reported_at DATETIME")
            conn.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")
    else:
        print("Schema already up to date.")
    
    conn.close()

if __name__ == "__main__":
    migrate_db()
