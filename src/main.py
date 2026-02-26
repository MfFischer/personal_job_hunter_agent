import os
import logging
import json
import time
from src.database import db_manager
from src.scrapers.scraper import RSSScraper, JSONScraper, RemotiveScraper
from src.filters.filter import score_job
from src.analysis.gemini_analyzer import analyze_job_relevance
from src.documents.generator import generate_cover_letter

# ... (logging setup)

# Configuration (PoC)
# Split feeds by type
# Use broad feeds - Layer 1 Profile Keywords will filter them
RSS_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss",
    "https://weworkremotely.com/categories/remote-product-jobs.rss"
]
JSON_FEEDS = [
    "https://remoteok.com/api"
]
REMOTIVE_FEEDS = [
    "https://remotive.com/api/remote-jobs?category=software-dev",
    "https://remotive.com/api/remote-jobs?category=product"
]

from src.analysis.resume_parser import parse_resumes_to_profile

def load_profile():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    profile_path = os.path.join(base_dir, "data", "profile.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except Exception:
            logging.warning("Corrupt profile.json, regenerating...")
    
    # If not exists or corrupt, try to generate
    logging.info("No profile found. Generating from Resume...")
    return parse_resumes_to_profile()

# Load Profile dynamically
CANDIDATE_PROFILE = load_profile()
if not CANDIDATE_PROFILE:
    logging.warning("Could not load candidate profile. Using Fallback.")
    CANDIDATE_PROFILE = {
        "skills": ["Python", "Generalist"], 
        "target_roles": ["Software Engineer"],
        "experience_summary": "Experienced Developer.",
        "preferences": "Remote"
    }

def main():
    logging.info("Starting Job Hunter Bot...")
    if CANDIDATE_PROFILE:
        logging.info(f"Loaded Profile for: {CANDIDATE_PROFILE.get('core_roles', ['Unknown'])[0]}")
    
    # 0. Init DB
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    db_manager.init_db()

    # 1. Layer 1: Discovery
    logging.info(">>> Layer 1: Discovery")
    
    scrapers = []
    for url in RSS_FEEDS:
        scrapers.append(RSSScraper(url))
    for url in JSON_FEEDS:
        scrapers.append(JSONScraper(url))
    for url in REMOTIVE_FEEDS:
        scrapers.append(RemotiveScraper(url))

    new_jobs_count = 0
    
    for scraper in scrapers:
        try:
            jobs = scraper.fetch_jobs()
            for job in jobs:
                job_id = db_manager.save_job(job)
                if job_id:
                    new_jobs_count += 1
                    
                    # 2. Layer 2: Rule-Filtering (Immediate processing for PoC)
                    score, excluded, reason = score_job(job, CANDIDATE_PROFILE)
                    db_manager.save_score(job_id, score, excluded, reason)
        except Exception as e:
            logging.error(f"Scraper error: {e}")
            
    logging.info(f"Layer 1 & 2 Complete. New Jobs: {new_jobs_count}")

    # 3. Layer 3: AI Analysis
    # Phase 3: AI Budget Protection
    if not db_manager.check_daily_quota(limit=50):
        logging.warning("Daily AI Quota Exceeded! Skipping Layer 3 analysis.")
    else:
        logging.info(">>> Layer 3: AI Analysis (Limit: 30/run)")
        candidates = db_manager.get_top_candidates(limit=30) 
        
        # Strategic Domain Filter
        BLOCKED_DOMAINS = ["Gambling", "Betting", "Crypto", "Adult", "Trading High Frequency"]

        for job in candidates:
            logging.info(f"Analyzing: {job['title']}...")
            result = analyze_job_relevance(job['description'], CANDIDATE_PROFILE)
            
            if result is None:
                logging.error(f"AI Analysis failed for {job['title']}. Skipping this job for today.")
                continue
                
            db_manager.increment_ai_usage() # Log the API call
            
            # --- LAYER 2: AI FILTER ---
            # 1. Location Gate
            remote_status = result.get('remote_status', 'GLOBAL_REMOTE')
            if remote_status in ["HYBRID", "ONSITE", "NON_EU_REMOTE"]:
                logging.info(f"Layer 2 Filter: Rejecting {job['title']} (Location: {remote_status})")
                db_manager.save_score(job['id'], 0, True, f"AI-Detected Location Mismatch: {remote_status}")
                continue
            
            # 2. Strategic Domain Gate
            job_domain = result.get('job_domain', 'General')
            if any(blocked in job_domain for blocked in BLOCKED_DOMAINS):
                logging.info(f"Layer 2 Filter: Rejecting {job['title']} (Blocked Domain: {job_domain})")
                db_manager.save_score(job['id'], 0, True, f"Strategic Domain Filter: {job_domain}")
                continue

            db_manager.update_ai_analysis(
                job['id'], 
                result.get('match_score', 0), 
                result,
                result.get('language', 'EN')
            )
            # Rate Limit handling: Free tier has strict per-minute limits (15 RPM / 1M TPM)
            # Sleep 30 seconds to guarantee we don't burst the minute limit with 3 large job descriptions
            time.sleep(30)

    # 4. Layer 4: Document Gen (Top 30)
    logging.info(">>> Layer 4: Document Generation")
    top_picks = db_manager.get_top_ai_matches(limit=30)
    
    for pick in top_picks:
        logging.info(f"Generating Cover Letter for: {pick['title']} (Score: {pick['ai_match_score']})...")
        
        # Load analysis json properly
        analysis = json.loads(pick['ai_analysis_json'])
        
        cover_letter = generate_cover_letter(
            pick,
            analysis,
            CANDIDATE_PROFILE
        )
        
        if not cover_letter:
            logging.info(f"Skipped generation for {pick['title']} (Score < 65 or Error).")
            continue
        
        # Save output to DB for Emailer
        db_manager.save_application(pick['id'], cover_letter)
        
        # Save output (In real app, save to DB application table or file)
        filename = f"application_{pick['id'][:8]}.txt"
        with open(filename, "w", encoding='utf-8') as f:
            f.write(cover_letter)
        logging.info(f"Saved to DB & File: {filename}")

    logging.info("Job Hunter Run Complete.")

if __name__ == "__main__":
    main()
