import google.generativeai as genai
import json
import typing
import os

# Define the response schema using standard python typing
class JobAnalysis(typing.TypedDict):
    match_score: int
    pros: list[str]
    cons: list[str]
    missing_skills: list[str]
    language: typing.Literal["DE", "EN", "OTHER"]
    job_domain: str  # e.g. "FinTech", "HealthTech", "Trading", "Ecommerce"

def analyze_job_relevance(job_description: str, resume_profile: dict) -> JobAnalysis:
    """
    Analyzes a job description against a user's compressed profile using Gemini.
    
    Args:
        job_description: The full text of the job description.
        resume_profile: A dictionary representing the 'Compressed Profile' (Skills, Experience, Preferences).
        
    Returns:
        A dictionary containing the analysis results.
    """
    
    # 1. Token Optimization
    skills = resume_profile.get('primary_stack', []) + resume_profile.get('secondary_stack', [])
    # Fallback to 'skills' if strictly using valid schema from parser, but handle both
    if not skills:
        skills = resume_profile.get('skills', [])

    profile_str = f"""
    SKILLS: {", ".join(skills)}
    ROLES: {", ".join(resume_profile.get('core_roles', []))}
    EXPERIENCE: {resume_profile.get('experience_summary', '')}
    INDUSTRIES: {", ".join(resume_profile.get('industries', []))}
    PREFERENCES: {resume_profile.get('preferred_environment', 'Remote')}
    """

    # 2. Prompt Engineering
    prompt = f"""
    You are an expert Career Coach and Recruiter AI. 
    Analyze the following JOB DESCRIPTION against the CANDIDATE PROFILE.
    
    CRITICAL FILTERING RULES:
    1. LOCATION: If job is strict "US Only" or "North America Only" and Candidate is NOT in US -> Score = 0.
    2. ROLE: If job is "Sales", "Business Development", or "Account Executive" (Non-Technical) -> Score = 0 (Mismatch).
    3. STACK: If job requires a specific stack (e.g. Ruby, Java) that is NOT in Candidate SKILLS -> Penalize heavily.

    Task:
    1. Determine the language of the job posting (DE or EN).
    2. Classify the JOB DOMAIN (e.g. "Trading", "SaaS", "Consulting").
    3. Classify REMOTE STATUS: 
       - "EU_REMOTE" (Remote within Europe/Germany)
       - "GLOBAL_REMOTE" (Work from anywhere)
       - "NON_EU_REMOTE" (Remote but requires US/LATAM/APAC timezones or residency)
       - "HYBRID" (Requires office presence)
       - "ONSITE" (100% Office)
    4. Calculate detailed match score (0-100).
    5. Identify specific Pros and Cons.
    6. List critical skills the candidate is MISSING.
    7. Extract Key Responsibilities (Max 5).
    8. Extract Required Skills (Max 5).

    CANDIDATE PROFILE:
    {profile_str}

    JOB DESCRIPTION:
    {job_description[:10000]}

    Output strictly in valid JSON format matching this schema:
    {{
        "match_score": 0-100,
        "remote_status": "EU_REMOTE" | "GLOBAL_REMOTE" | "NON_EU_REMOTE" | "HYBRID" | "ONSITE",
        "pros": ["point 1", "point 2"],
        "cons": ["point 1", "point 2"],
        "missing_skills": ["skill 1", "skill 2"],
        "key_responsibilities": ["resp 1", "resp 2", "resp 3", "resp 4", "resp 5"],
        "required_skills": ["skill 1", "skill 2", "skill 3", "skill 4", "skill 5"],
        "language": "DE" | "EN",
        "job_domain": "string"
    }}
    """

    try:
        model = genai.GenerativeModel('gemini-2.0-flash') # Use Flash for speed/cost efficiency
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Parse JSON
        analysis = json.loads(response.text)
        return analysis

    except Exception as e:
        print(f"Error analyzing job: {e}")
        return {
            "match_score": 0,
            "pros": [],
            "cons": ["Error during AI analysis"],
            "missing_skills": [],
            "language": "EN", # Default
            "job_domain": "General"
        }

# Example of a "Compressed Profile" for Token Optimization
# This avoids sending a 4-page PDF. 
# It should be manually curated or generated once from the CV.
EXAMPLE_PROFILE = {
    "skills": ["Python", "FastAPI", "AWS (EC2, Lambda)", "PostgreSQL", "React", "TypeScript", "Docker"],
    "target_roles": ["Senior Backend Engineer", "Full Stack Developer", "AI Engineer"],
    "experience_summary": "7 years total. 4 years in Python backend. 2 years leading teams. Strong focus on API design and cloud infrastructure.",
    "preferences": "Remote only. Product-focused companies. No betting/gambling industries."
}

# Logic Flow Snippet (Conceptual for main.py)
# jobs_to_analyze = db.query("SELECT * FROM jobs WHERE is_excluded = 0 ORDER BY layer2_score DESC LIMIT 20")
# for job in jobs_to_analyze:
#     result = analyze_job_relevance(job['description'], EXAMPLE_PROFILE)
#     db.update_job(job['id'], result)
