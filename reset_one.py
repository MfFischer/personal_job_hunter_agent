import sqlite3
import logging

DB_PATH = "g:/automation projects/personal job hunter/data/jobs.db"

def reset_promising_job():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find a Python job to reset
    cursor.execute("SELECT id, title FROM jobs WHERE title LIKE '%Python%' AND id IN (SELECT job_id FROM job_scores WHERE is_excluded=0) LIMIT 1")
    job = cursor.fetchone()
    
    if job:
        print(f"Resetting analysis for: {job[1]} ({job[0]})")
        cursor.execute('''
            UPDATE job_scores 
            SET ai_match_score = NULL, 
                ai_analysis_json = NULL
            WHERE job_id = ?
        ''', (job[0],))
        conn.commit()
    else:
        print("No Python job found.")
    
    conn.close()

if __name__ == "__main__":
    reset_promising_job()
