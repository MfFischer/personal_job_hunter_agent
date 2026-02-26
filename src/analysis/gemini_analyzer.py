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

    exp_breakdown = resume_profile.get('experience_breakdown', {})
    exp_breakdown_str = ", ".join([f"{k}: {v}" for k, v in exp_breakdown.items()]) if exp_breakdown else "Not provided"

    profile_str = f"""
    SKILLS: {", ".join(skills)}
    ROLES: {", ".join(resume_profile.get('core_roles', []))}
    EXPERIENCE SUMMARY: {resume_profile.get('experience_summary', '')}
    EXPERIENCE BREAKDOWN: {exp_breakdown_str}
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
    4. EXPERIENCE RELEVANCE: The candidate has a diverse background. When evaluating if they meet a job's "Years of Experience" requirement, YOU MUST ONLY count the years from the specific relevant field in EXPERIENCE BREAKDOWN (e.g., do not use 10 years of founder experience to fulfill a 5-year software engineering requirement). If they lack the required years in the specific field, lower their score.

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

    import time
    from google.api_core.exceptions import ResourceExhausted

    max_retries = 3
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash') # Use Flash for speed/cost efficiency
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parse JSON
            analysis = json.loads(response.text)
            return analysis

        except ResourceExhausted as e:
            print(f"Rate Limit Hit (429) on attempt {attempt + 1}. Sleeping for 60s...")
            time.sleep(60)
            if attempt == max_retries - 1:
                print("Max retries reached. Failing this job.")
                return None
        except Exception as e:
            print(f"Error analyzing job: {e}")
            # Return None so the upstream knows it failed and doesn't permanently write score 0
            return None

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
