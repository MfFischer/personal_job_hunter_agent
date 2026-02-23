import sqlite3

DB_PATH = "g:/automation projects/personal job hunter/data/jobs.db"

def reset_reported_status():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Resetting is_reported for all applications so they can be picked up by the email sender again
    cursor.execute("UPDATE applications SET is_reported = 0")
    print(f"Reset {cursor.rowcount} applications to reported=0")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    reset_reported_status()
