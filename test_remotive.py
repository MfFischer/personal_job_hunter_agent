import requests

def test_remotive():
    url = "https://remotive.com/api/remote-jobs?category=software-dev&search=python"
    print(f"Testing Remotive API: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        data = response.json()
        jobs = data.get('jobs', [])
        print(f"Found {len(jobs)} jobs.")
        
        if jobs:
            job = jobs[0]
            print(f"Sample Job Keys: {job.keys()}")
            print(f"Title: {job.get('title')}")
            print(f"Company: {job.get('company_name')}")
            print(f"Location: {job.get('candidate_required_location')}")
            # print(f"Description snippet: {job.get('description')[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_remotive()
