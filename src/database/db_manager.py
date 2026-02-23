import sqlite3
import json
import hashlib
from datetime import datetime

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "jobs.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

def save_job(job_data: dict) -> str:
    """Saves a job to the DB. Returns the Job ID if new, or None if exists."""
    
    # Create deterministic ID based on URL (Legacy)
    job_id = hashlib.md5(job_data['url'].encode()).hexdigest()
    
    # Phase 3: SHA256 Deduplication (Title + Company)
    raw_sig = (job_data.get('title', '') + job_data.get('company', '') + str(job_data.get('is_remote', False))).lower()
    job_hash = hashlib.sha256(raw_sig.encode()).hexdigest()

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check duplicate hash
        cursor.execute("SELECT id FROM jobs WHERE job_hash = ?", (job_hash,))
        if cursor.fetchone():
            return None # Duplicate Job Content

        cursor.execute('''
            INSERT INTO jobs (id, title, company, url, description, source, posted_date, is_remote, raw_data, job_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_id,
            job_data.get('title'),
            job_data.get('company'),
            job_data.get('url'),
            job_data.get('description'),
            job_data.get('source'),
            job_data.get('posted_date', datetime.now().isoformat()),
            job_data.get('is_remote', False),
            job_data.get('raw_data', '{}'), 
            job_hash
        ))
        conn.commit()
        return job_id
    except sqlite3.IntegrityError:
        return None  # Job ID (url hash) already exists
    finally:
        conn.close()

def save_score(job_id: str, score: int, is_excluded: bool, reason: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO job_scores (job_id, keyword_score, is_excluded, exclusion_reason)
        VALUES (?, ?, ?, ?)
    ''', (job_id, score, is_excluded, reason))
    conn.commit()
    conn.close()

def update_ai_analysis(job_id: str, ai_match_score: int, analysis_json: dict, language: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE job_scores 
        SET ai_match_score = ?, ai_analysis_json = ?, language = ?
        WHERE job_id = ?
    ''', (ai_match_score, json.dumps(analysis_json), language, job_id))
    conn.commit()
    conn.close()

def get_top_candidates(limit=20):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT j.*, s.keyword_score 
        FROM jobs j
        JOIN job_scores s ON j.id = s.job_id
        WHERE s.is_excluded = 0
        AND s.ai_analysis_json IS NULL -- Fetch unranked jobs
        ORDER BY s.keyword_score DESC
        LIMIT ?
    ''', (limit,))
    return [dict(row) for row in cursor.fetchall()]

def get_top_ai_matches(limit=30):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT j.*, s.ai_match_score, s.ai_analysis_json
        FROM jobs j
        JOIN job_scores s ON j.id = s.job_id
        WHERE s.ai_match_score > 0
        ORDER BY s.ai_match_score DESC
        LIMIT ?
    ''', (limit,))
    return [dict(row) for row in cursor.fetchall()]

def save_application(job_id: str, cover_letter_text: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM applications WHERE job_id = ?
        ''', (job_id,))
        
        cursor.execute('''
            INSERT INTO applications (job_id, cover_letter_text, status, created_at)
            VALUES (?, ?, 'generated', CURRENT_TIMESTAMP)
        ''', (job_id, cover_letter_text))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error saving app: {e}")

# --- PHASE 3: AI BUDGET & OUTCOME TRACKING ---

def check_daily_quota(limit=50) -> bool:
    """Returns True if under quota, False if exceeded."""
    today = datetime.now().date().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT request_count FROM ai_usage_log WHERE date = ?", (today,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0] < limit
    return True # No entry means 0 usage

def increment_ai_usage():
    today = datetime.now().date().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ai_usage_log (date, request_count) VALUES (?, 1)
        ON CONFLICT(date) DO UPDATE SET request_count = request_count + 1
    ''', (today,))
    conn.commit()
    conn.close()
