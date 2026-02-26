import google.generativeai as genai
import os

# Configuration for CV Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CV_PATHS = {
    "EN": os.path.join(BASE_DIR, "assets", "cv_en.pdf"),
    "DE": os.path.join(BASE_DIR, "assets", "cv_de.pdf")
}

def get_cv_path(language: str) -> str:
    """Returns the correct CV path based on the language."""
    return CV_PATHS.get(language, CV_PATHS["EN"])

def generate_cover_letter(job_data: dict, analysis_results: dict, candidate_profile: dict) -> str:
    """
    Generates a tailored cover letter using Gemini.

    Args:
        job_data: Dictionary containing job details (title, company, description).
        analysis_results: Dictionary containing AI analysis (pros, cons, missing_skills, language).
        candidate_profile: Dictionary containing the user's profile.

    Returns:
        The generated cover letter text.
    """
    
    
    match_score = analysis_results.get('match_score', 0)

    # 1. "Should Apply?" Gate
    # Don't waste tokens/time on low-quality matches
    if match_score < 65:
        return None

    # Determine Tone Logic
    if match_score > 85:
        tone_instruction = "TONE: Authoritative, expert, and value-driven. Use phrases like 'I am confident I can immediately deliver...', 'My expertise in X allows me to...'. Focus on immediate impact."
        tone_label = "ASSERTIVE"
    elif match_score < 70:
        tone_instruction = "TONE: Curious, adaptable, and focused on transferable skills. Use phrases like 'I am excited to explore...', 'My background in X provides a unique perspective on Y...'. Do NOT sound like an expert in the domain, sound like a high-potential learner."
        tone_label = "EXPLORATORY"
    else:
        # The key missing in the previous dict approach
        tone_instruction = "TONE: Professional, confident, yet humble. Balanced and not exaggerated."
        tone_label = "PROFESSIONAL"

    
    # 2. Framing Strategy (Impact vs Adaptability)
    if match_score > 85:
        framing_strategy = "STRATEGY: FOCUS ON IMMEDIATE IMPACT. Use assertive language ('I will drive X', 'My expertise in Y ensures...')."
    elif match_score >= 65:
        framing_strategy = "STRATEGY: FOCUS ON ADAPTABILITY & TRANSFERABLE SKILLS. Show enthusiasm to learn the specific domain nuances while leveraging strong core engineering/product foundations."
    else:
        framing_strategy = "STRATEGY: PROFESSIONAL & BALANCED."

    # Construct the Prompt
    # OPTIMIZATION: Use structured data instead of full description to save tokens and reduce hallucination.
    prompt = f"""
    You are an expert Career Coach and Professional Writer.
    Write a tailored COVER LETTER for the following job application.

    ## NO MARKDOWN. OUTPUT RAW TEXT ONLY.

    ## INPUTS
    1. ROLE: {job_data.get('title')} at {job_data.get('company')}
    2. JOB DOMAIN: {analysis_results.get('job_domain', 'General')}
    3. COMPANY CONTEXT: {job_data.get('company_summary', 'Not provided. Do NOT fabricate specific company mission/values if not found.')}
    
    4. JOB ANALYSIS (Structured):
    - Key Responsibilities: {', '.join(analysis_results.get('key_responsibilities', [])[:5])}
    - Required Skills: {', '.join(analysis_results.get('required_skills', [])[:5])}
    - Pros (Candidate Fit): {', '.join(analysis_results.get('pros', []))}
    - Gaps (Candidate Mismatch): {', '.join(analysis_results.get('cons', []))}
    
    5. CANDIDATE PROFILE:
     Core Industries: {', '.join(candidate_profile.get('industries', []))}
     Experience Summary: {candidate_profile.get('experience_summary')}
     Experience Breakdown: {', '.join([f"{k}: {v}" for k, v in candidate_profile.get('experience_breakdown', {}).items()]) if candidate_profile.get('experience_breakdown') else 'Not provided'}

    ## CRITICAL SAFEGUARDS
    1. **NO SENIORITY/EXPERIENCE INFLATION**: Do NOT exaggerate years of experience in specific skills. If applying for a software engineering role, do NOT claim '18 years of software engineering' if the breakdown says otherwise. Stick strictly to the "Experience Breakdown" for specific domains, and only use "Experience Summary" for holistic framing.
    2. **NO FABRICATION**: Do NOT invent achievements, technologies, or experience not provided.
    3. **DOMAIN HONESTY**: If 'JOB DOMAIN' mismatches Candidate 'Core Industries', use "PIVOT" framing.
    4. **FORMAT**: Output ONLY the cover letter text. NO markdown (no bold/italics), NO explanations, NO "Here is the cover letter:" preambles.

    ## FRAMING INSTRUCTION
    {framing_strategy}
    {tone_instruction}

    ## STRUCTURE
    - Opening: Enthusiastic.
    - Body: Connect specific "Pros" to "Key Responsibilities".
    - Bridging: Address "Gaps" using the PIVOT strategy (if needed).
    - Closing: Call to action.
    - Sign-off: "Sincerely, {candidate_profile.get('name', 'Maria Fe Fischer')}"
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        import traceback
        # traceback.print_exc() # Reduce noise in logs
        print(f"Error generating cover letter (API): {e}")
        
        # FALLBACK: Template-based Generation (if API fails, e.g. Rate Limit)
        print("Using Fallback Template Generator...")
        return f"""
Dear Hiring Team,

I am writing to express my enthusiastic interest in the {job_data.get('title')} position at {job_data.get('company')}. With my background as a {candidate_profile.get('core_roles', ['Professional'])[0]}, I am confident I can bring immediate value to your team.

Reflecting on the role, I see a strong alignment with my experience in {', '.join(candidate_profile.get('primary_stack', [])[:3])}. I am particularly drawn to this opportunity because of the job's focus on {analysis_results.get('job_domain', 'technical excellence')}.

My key strengths include:
*   {analysis_results.get('pros', ['Proven track record in similar roles'])[0] if analysis_results.get('pros') else 'Proven technical execution'}
*   {candidate_profile.get('experience_summary', 'Extensive industry experience')}

I am excited about the possibility of contributing to {job_data.get('company')}'s success and would welcome the chance to discuss how my skills match your needs.

Sincerely,
{candidate_profile.get('name', 'Maria Fe Fischer')}
        """.strip()
