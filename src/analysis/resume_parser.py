import os
import json
import logging
import google.generativeai as genai
from pathlib import Path

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_resumes_to_profile(assets_dir: str = None) -> dict:
    if assets_dir is None:
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")
    """
    Parses cv_en.pdf (and optionally cv_de.pdf) to generate a structured candidate profile.
    Returns the profile dict and saves it to data/profile.json.
    """
    
    # 1. Setup paths
    cv_en_path = Path(assets_dir) / "cv_en.pdf"
    # cv_de_path = Path(assets_dir) / "cv_de.pdf" # Optional integration later
    
    if not cv_en_path.exists():
        logging.error(f"Resume not found at {cv_en_path}. Please upload it.")
        return None

    # 2. Configure Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY not found.")
        return None
    genai.configure(api_key=api_key)

    try:
        logging.info("Uploading Resume to Gemini...")
        # Upload the file
        sample_file = genai.upload_file(path=cv_en_path, display_name="Candidate CV")
        
        # 3. Prompt
        prompt = """
        You are an expert Technical Recruiter and Career Coach.
        Analyze the attached Resume/CV and extract a structured 'Candidate Profile' in JSON format.
        
        Your goal is to create a profile that perfectly describes this candidate's strengths, skills, and target roles.
        
        Output stricly VALID JSON with this schema:
        {
          "name": "Candidate Name",
          "core_roles": ["Role Title 1", "Role Title 2"],
          "primary_stack": ["Tech 1", "Tech 2", "Tech 3"],
          "secondary_stack": ["Tech 4", "Tech 5"],
          "industries": ["Industry 1", "Industry 2"],
          "seniority_level": "Junior" | "Mid-level" | "Senior" | "Lead" | "Principal",
          "preferred_environment": "Remote" | "Hybrid" | "Onsite",
          "strength_keywords": ["Keyword 1", "Keyword 2", "Keyword 3"],
          "derived_search_queries": [
              "3-5 specific, high-intent search queries for job boards (e.g., 'Python Backend Remote EU')"
          ],
          "experience_summary": "A concise 2-3 sentence professional summary suitable for a cover letter intro.",
          "languages": ["English", "German (Native/Fluent/Basic)", etc.]
        }
        """
        
        logging.info("Analyzing Resume (this may take a few seconds)...")
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(
            [prompt, sample_file],
            generation_config={"response_mime_type": "application/json"}
        )
        
        # 4. Parse & Save
        profile_data = json.loads(response.text)
        
        # Ensure data directory exists
        data_dir = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"))
        data_dir.mkdir(exist_ok=True)
        
        profile_path = data_dir / "profile.json"
        with open(profile_path, "w", encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2)
            
        logging.info(f"Success! Profile saved to {profile_path}")
        return profile_data

    except Exception as e:
        logging.error(f"Error parsing resume: {e}")
        return None

if __name__ == "__main__":
    # Test run
    from dotenv import load_dotenv
    load_dotenv()
    parse_resumes_to_profile()
