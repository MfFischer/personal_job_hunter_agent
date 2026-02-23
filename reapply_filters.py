import logging
import json
from src.database import db_manager
from src.filters.filter import score_job

# Configure Logging
logging.basicConfig(level=logging.INFO)

# Load Profile
def load_profile():
    profile_path = "g:/automation projects/personal job hunter/data/profile.json"
    try:
        with open(profile_path, 'r') as f:
            return json.load(f)
    except:
        return None

def reapply_filters():
    logging.info("Starting Re-scoring of ALL jobs...")
    
    CANDIDATE_PROFILE = load_profile()
    if not CANDIDATE_PROFILE:
        logging.error("Profile not found!")
        return

    conn = db_manager.get_connection()
    conn.row_factory = db_manager.sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch all jobs
    cursor.execute("SELECT * FROM jobs")
    jobs = [dict(row) for row in cursor.fetchall()]
    
    resocred_count = 0
    excluded_count = 0
    
    for job in jobs:
        score, is_excluded, reason = score_job(job, CANDIDATE_PROFILE)
        
        # Update DB
        # Note: We need to update existing score rows
        # db_manager.save_score typically does INSERT OR IGNORE or INSERT OR REPLACE?
        # Let's check db_manager or just write raw SQL here to be safe
        
        cursor.execute('''
            UPDATE job_scores 
            SET keyword_score = ?, 
                is_excluded = ?, 
                exclusion_reason = ?
            WHERE job_id = ?
        ''', (score, 1 if is_excluded else 0, reason, job['id']))
        
        # If explicitly excluded now, also nuke any AI score to prevent reporting
        if is_excluded:
            cursor.execute("UPDATE job_scores SET ai_match_score = 0 WHERE job_id = ?", (job['id'],))
            excluded_count += 1
            logging.info(f"Excluded: {job['title']} ({reason})")
        
        resocred_count += 1

    conn.commit()
    conn.close()
    
    logging.info(f"Re-scored {resocred_count} jobs.")
    logging.info(f"Newly Excluded: {excluded_count} jobs.")

if __name__ == "__main__":
    reapply_filters()
