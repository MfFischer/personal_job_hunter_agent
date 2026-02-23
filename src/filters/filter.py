def score_job(job_data: dict, candidate_profile: dict = None) -> tuple[int, bool, str]:
    """
    Scoring Logic:
    - Exclusion: Onsite/Hybrid
    - Negative Constraints: Mismatching Tech Stacks (Ruby, Java, etc.)
    - Scoring: Keywords based on Profile
    
    Returns: (score, is_excluded, exclusion_reason)
    """
    description = (job_data.get('description') or "").lower()
    title = (job_data.get('title') or "").lower()
    full_text = f"{title} {description}"

    # 1. Exclusion Logic (Location & Role)
    description_lower = description.lower()
    title_lower = title.lower()
    full_text_lower = full_text.lower()

    # --- LAYER 1: HARD LOCATION FILTER END ---
    # User Requirement: Remote (EU Preferred) or Remote (Global)
    # Reject: US-Only, Onsite, Hybrid
    
    # 1.1 Explicit Exclusions
    exclusion_keywords = [
        "us only", "usa only", "united states only", "north america only", 
        "must reside in the us", "must reside in the usa", "u.s. only", "u.s.a. only",
        "hybrid", "onsite", "on-site", "office presence", "must relocate", "office based",
        "remote us", "remote latam", "remote apac"
    ]
    if any(k in description_lower for k in exclusion_keywords):
        return 0, True, "Layer 1: Detected Forbidden Location/Mode (US/Hybrid/Onsite)"

    # 1.2 EU / Remote Validation (Soft Check acting as strong bias)
    # If it says "Remote" but mentions no region -> OK (Assume Global)
    # If it mentions "EU", "Europe", "Germany" -> Bonus OK
    # If it mentions "Timezone" -> Check if EU compatible (UTC-1 to UTC+3)? (Skipped for now)
    
    # 2. Role Mismatch: Exclude Sales/Non-Tech
    sales_keywords = ["account executive", "sales", "business development", "sdr", "bdr", "marketing manager"]
    if any(k in title_lower for k in sales_keywords) and "sales" not in (candidate_profile.get('core_roles', []) if candidate_profile else []):
         return 0, True, "Layer 1: Detected Sales/Non-Technical Role"

    # 2. Hard Stack Mismatch Logic (The Fix)
    if candidate_profile:
        # Define stacks that differ from your core. 
        # If job title implies these, and you don't list them -> Exclude.
        # This list should ideally be dynamic, but for PoC we hardcode common mismatches.
        hard_stacks = {
            "ruby": ["ruby", "rails"],
            "java": ["java", "spring"],
            "c#": [".net", "c#", "c-sharp"],
            "php": ["php", "laravel"],
            "go": ["golang", "go "], # "go " with space to avoid matching "good"
            "rust": ["rust"],
            "node": ["node.js", "nodejs", "express"],
            "react": ["react", "react.js"]
        }
        
        # Get your actual skills
        my_stack = set()
        for s in candidate_profile.get('primary_stack', []) + candidate_profile.get('secondary_stack', []) + candidate_profile.get('skills', []):
            my_stack.add(s.lower())
        
        # If title mentions a stack you don't have -> Exclude
        for tech, keywords in hard_stacks.items():
            if tech in title: # Job is explicitly a "Ruby Engineer"
                # Check if we have ANY of the related keywords
                has_skill = any(k in s for s in my_stack for k in keywords) 
                if not has_skill:
                    return 0, True, f"Mismatch: Job is for {tech}, but not in profile."

    # 3. Positive Scoring Logic
    score = 0
    # Use profile keywords if available, else fallback
    keywords = candidate_profile.get('strength_keywords', []) if candidate_profile else ["python", "aws", "backend"]
    # Add primary/secondary stack to keywords for better matching
    if candidate_profile:
        keywords += candidate_profile.get('primary_stack', []) 
        keywords += candidate_profile.get('secondary_stack', [])
        # Include role-based keywords directly
        for role in candidate_profile.get('core_roles', []):
            keywords.append(role)
            # Add split terms for broadness (e.g., "Product Engineer" -> "Product")
            for part in role.split():
                if len(part) > 3: # Avoid "and", "the"
                    keywords.append(part)
    
    # Deduplicate and lowercase
    keywords = list(set([k.lower() for k in keywords]))
    
    matched_keywords = []
    for word in keywords:
        if word in full_text:
            score += 5
            matched_keywords.append(word)
            
    # Seniority Bonus (if matches)
    if candidate_profile and candidate_profile.get('seniority_level', '').lower() in title:
        score += 10

    # 4. Aggressive Exclude if irrelevant to profile
    if score == 0:
        return 0, True, "Layer 1: No matching profile keywords (Stack/Roles) found in job text."

    return score, False, ""
