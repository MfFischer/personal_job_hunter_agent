import requests

def debug_locations():
    url = "https://remotive.com/api/remote-jobs?category=software-dev&search=python"
    resp = requests.get(url)
    data = resp.json()
    jobs = data.get('jobs', [])
    
    locations = set()
    for j in jobs:
        loc = str(j.get('candidate_required_location', '')).strip()
        locations.add(loc)
        
    print(f"Total Unique Location Strings: {len(locations)}")
    for l in sorted(locations)[:50]: # Print first 50
        print(f" - '{l}'")

if __name__ == "__main__":
    debug_locations()
