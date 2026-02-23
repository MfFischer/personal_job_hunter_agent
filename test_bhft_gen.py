import sqlite3
import json
import logging
from src.documents.generator import generate_cover_letter
from src.main import CANDIDATE_PROFILE

# Setup Logging
logging.basicConfig(level=logging.INFO)

# Connect to DB
conn = sqlite3.connect('g:/automation projects/personal job hunter/data/jobs.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Find BHFT job
job = cur.execute("SELECT * FROM jobs WHERE title LIKE '%Market Data%' OR company LIKE '%BHFT%'").fetchone()

if not job:
    print("BHFT Job not found in DB!")
    exit()

print(f"Found Job: {job['title']} at {job['company']}")

# Simulate/Hardcode Analysis Results (since we might have failed to save them)
# We explicitly set job_domain to 'Trading' to test the Pivot Logic.
analysis_results = {
    "match_score": 52,
    "pros": ["SaaS Experience", "Python proficiency", "Engineering Management"],
    "cons": ["No trading experience", "No C++"],
    "missing_skills": ["Market Data Feeds", "Low Latency C++"],
    "language": "EN",
    "job_domain": "Trading" 
}

# Generate Letter
print("\nGenerating Cover Letter...")
letter = generate_cover_letter(dict(job), analysis_results, CANDIDATE_PROFILE)

print("\n=== GENERATED LETTER ===\n")
print(letter)

# Save it to verify
with open("test_bhft_letter.txt", "w", encoding="utf-8") as f:
    f.write(letter)
