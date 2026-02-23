import sqlite3
import json
import logging
import time
import google.generativeai as genai
from src.main import CANDIDATE_PROFILE
from src.documents import generator

# Monkey patch generator to use Lite model
def generate_cover_letter_lite(job_data, analysis_results, candidate_profile):
    from src.documents.generator import get_cv_path
    
    language = analysis_results.get("language", "EN")
    
    prompt = f"""
    You are an expert Career Coach and Professional Writer.
    Write a tailored COVER LETTER for the following job application.

    ## INPUTS
    1. ROLE: {job_data['title']} at {job_data['company']}
    2. JOB DOMAIN: {analysis_results.get('job_domain', 'General')}
    3. JOB DESCRIPTION: 
    {job_data['description'][:5000]}
    
    4. CANDIDATE MATCH INSIGHTS:
    - Pros: {', '.join(analysis_results.get('pros', []))}
    - Gaps: {', '.join(analysis_results.get('cons', []))}
    - Missing Skills: {', '.join(analysis_results.get('missing_skills', []))}
    
    5. CANDIDATE PROFILE:
     Core Industries: {', '.join(candidate_profile.get('industries', []))}
     Experience: {candidate_profile.get('experience_summary')}

    ## CRITICAL INSTRUCTION: DOMAIN HONESTY
    Check if the 'JOB DOMAIN' (e.g. Trading, Crypto, Health) overlaps with the Candidate's 'Core Industries'.
    - IF MISMATCH (e.g. Job is Trading, Candidate is SaaS):
      - DO NOT claim experience in the Job's domain.
      - DO NOT use phrases like "My experience in Trading..."
      - INSTEAD, use a "PIVOT" framing: "While my background is in [Candidate Industry], my experience in [Skill] is highly transferable to [Job Domain]..." 
      - Phrase it like: "I am eager to apply my [Skill] expertise to the challenges of [Job Domain]."
    - IF MATCH: Acknowledge the deep domain fit.

    ## TONE RULES
    - NO generic fluff.
    - Professional, confident, yet humble about specific domain gaps.
    - STRICTLY under 300 words.

    ## STRUCTURE
    - Opening: Enthusiastic.
    - Body: Highlight "Pros".
    - Bridging: Address "Gaps" using PIVOT strategy.
    - Closing: Call to action.
    """

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-lite-001')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"

# Find BHFT job
conn = sqlite3.connect('g:/automation projects/personal job hunter/data/jobs.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
job = cur.execute("SELECT * FROM jobs WHERE title LIKE '%Market Data%' OR company LIKE '%BHFT%'").fetchone()

if not job:
    print("BHFT Job not found in DB!")
    exit()

analysis_results = {
    "match_score": 52,
    "pros": ["SaaS Experience", "Python proficiency", "Engineering Management"],
    "cons": ["No trading experience", "No C++"],
    "missing_skills": ["Market Data Feeds", "Low Latency C++"],
    "language": "EN",
    "job_domain": "Trading" 
}

print("Generating Pivot Letter with Lite Model...")
letter = generate_cover_letter_lite(dict(job), analysis_results, CANDIDATE_PROFILE)
print("\n=== GENERATED LETTER ===\n")
print(letter)

with open("test_bhft_letter.txt", "w", encoding="utf-8") as f:
    f.write(letter)
