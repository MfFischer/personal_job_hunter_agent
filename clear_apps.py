import sqlite3
import logging

DB_PATH = "g:/automation projects/personal job hunter/data/jobs.db"

def clear_applications():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Delete all rows in applications so we can re-generate fresh ones
    cursor.execute("DELETE FROM applications")
    print(f"Deleted {cursor.rowcount} stale applications.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    clear_applications()
