def score_job(job_data: dict, candidate_profile: dict) -> tuple[int, bool, str]:
    """
    Refined Scoring Logic:
    1. Exclusion: Onsite/Hybrid (existing)
    2. Negative Constraints: Mismatching Tech Stacks
       - If Job Title contains X (e.g. "Ruby", "Java") AND Candidate Profile does NOT have X
       - -> EXCLUDE or massive penalty.
    3. Management Roles:
       - If Title contains "Manager", "Owner", "Lead" -> Check 'seniority_level' or 'management_skills'.
    
    Returns: (score, is_excluded, exclusion_reason)
    """
    
    title = (job_data.get('title') or "").lower()
    description = (job_data.get('description') or "").lower()
    full_text = f"{title} {description}"
    
    # ... existing exclusion logic ...
    
    # NEW: Stack Mismatch Check
    # Define "Hard Stacks" that define a role. If you don't know them, you can't do the job.
    hard_stacks = {
        "ruby": ["ruby", "rails"],
        "java": ["java", "spring"],
        "c#": [".net", "c#"],
        "php": ["php", "laravel"],
        "go": ["golang", "go "],
        "rust": ["rust"]
    }
    
    # Get candidate's primary stack (normalized to lower case)
    candidate_stack = [s.lower() for s in candidate_profile.get('primary_stack', []) + candidate_profile.get('secondary_stack', [])]
    candidate_stack_str = " ".join(candidate_stack)
    
    # Check if job title implies a stack we don't have
    for stack_name, keywords in hard_stacks.items():
        # If job title explicitly mentions "Ruby Engineer"
        if stack_name in title:
            # And we don't have "ruby" or "rails" in our stack
            if not any(k in candidate_stack_str for k in keywords):
                return 0, True, f"Mismatch: Job requires {stack_name}, but not in profile."

    # ... existing scoring logic ...
