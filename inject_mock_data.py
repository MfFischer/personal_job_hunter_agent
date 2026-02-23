import sqlite3
import json

DB_PATH = "g:/automation projects/personal job hunter/data/jobs.db"

def inject_mock_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Get 3 random job IDs
    cursor.execute("SELECT id, title FROM jobs LIMIT 3")
    jobs = cursor.fetchall()
    
    if not jobs:
        print("No jobs found in DB to update!")
        return

    print(f"Updating {len(jobs)} jobs with mock scores...")

    # Job 1: High Match (Assertive)
    job1_id = jobs[0][0]
    analysis1 = {
        "match_score": 92,
        "pros": ["Perfect Tech Stack", "Industry Match", "Senior Role"],
        "cons": ["Timezone gap"],
        "missing_skills": [],
        "language": "EN",
        "job_domain": "SaaS"
    }
    # Insert Mock Application/Cover Letter for Job 1
    cursor.execute("DELETE FROM applications WHERE job_id = ?", (job1_id,))
    cursor.execute('''
        INSERT INTO applications (job_id, status, cover_letter_text, is_reported)
        VALUES (?, 'generated', ?, 0)
    ''', (job1_id, "Dear Hiring Manager,\n\nI am writing to express my interest in the Senior Role at your company. With my background in SaaS and Engineering Management, I am confident I can deliver immediate value.\n\nSincerely,\nAndreas Fischer"))

    if len(jobs) > 1:
        # Job 2: Low Match (Exploratory + Pivot)
        job2_id = jobs[1][0]
        # ... existing score update ...
        
        # Insert Mock Application for Job 2
        cursor.execute("DELETE FROM applications WHERE job_id = ?", (job2_id,))
        cursor.execute('''
            INSERT INTO applications (job_id, status, cover_letter_text, is_reported)
            VALUES (?, 'generated', ?, 0)
        ''', (job2_id, "Dear Hiring Team,\n\nI was excited to see the opening for the Remote position. While my core experience is in SaaS, I have always been fascinated by Crypto and have been upskilling in Rust.\n\nBest,\nAndreas Fischer"))
        analysis2 = {
            "match_score": 65,
            "pros": ["Good Culture", "Remote"],
            "cons": ["Domain Mismatch", "Missing Rust knowledge"],
            "missing_skills": ["Rust", "Crypto"],
            "language": "EN",
            "job_domain": "Crypto"
        }
        cursor.execute('''
            UPDATE job_scores 
            SET ai_match_score = 65, 
                ai_analysis_json = ?, 
                keyword_score = 60,
                is_excluded = 0
            WHERE job_id = ?
        ''', (json.dumps(analysis2), job2_id))

    # Reset any reporting flags
    cursor.execute("UPDATE applications SET is_reported = 0")
    
    conn.commit()
    conn.close()
    print("Mock data injected successfully.")

if __name__ == "__main__":
    inject_mock_data()
