import sqlite3
import os

def check_exclusions():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data", "jobs.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query the most recent jobs from Remotive that were excluded
    cursor.execute('''
        SELECT s.exclusion_reason, COUNT(*)
        FROM jobs j 
        JOIN job_scores s ON j.id = s.job_id 
        WHERE s.is_excluded = 1
        GROUP BY s.exclusion_reason
        ORDER BY COUNT(*) DESC
        LIMIT 20
    ''')
    
    results = cursor.fetchall()
    print("Top Exclusion Reasons (All Time):")
    for reason, count in results:
        print(f" - [{count}] {reason}")
        
    conn.close()

if __name__ == "__main__":
    check_exclusions()
