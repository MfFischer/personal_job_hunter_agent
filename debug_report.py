import sqlite3
import logging

DB_PATH = "g:/automation projects/personal job hunter/data/jobs.db"

def debug_query():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check total jobs
    cursor.execute("SELECT count(*) as count FROM jobs")
    print(f"Total Jobs: {cursor.fetchone()['count']}")

    # Check scores
    cursor.execute("SELECT count(*) as count FROM job_scores WHERE ai_match_score > 0")
    print(f"Jobs with AI Score > 0: {cursor.fetchone()['count']}")
    
    # Check exclusion
    cursor.execute("SELECT count(*) as count FROM job_scores WHERE is_excluded = 0")
    print(f"Non-excluded Jobs: {cursor.fetchone()['count']}")

    # Run the exact query from email_sender
    cursor.execute('''
        SELECT j.title, s.ai_match_score, a.is_reported
        FROM jobs j
        JOIN job_scores s ON j.id = s.job_id
        LEFT JOIN applications a ON j.id = a.job_id
        WHERE s.ai_match_score > 0
          AND (a.is_reported IS NULL OR a.is_reported = 0)
        LIMIT 5
    ''')
    rows = cursor.fetchall()
    print(f"\nQuery returned {len(rows)} rows:")
    for row in rows:
        print(dict(row))
    
    conn.close()

if __name__ == "__main__":
    debug_query()
