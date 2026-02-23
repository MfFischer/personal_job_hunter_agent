import requests

def test_working_nomads():
    url = "https://www.workingnomads.co/jobsapi/jobs.json"
    print(f"Testing WorkingNomads API: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        data = response.json()
        print(f"Found {len(data)} jobs.")
        
        if data:
            job = data[0]
            print(f"Sample Job Keys: {job.keys()}")
            print(f"Title: {job.get('title')}")
            print(f"Company: {job.get('company_name')}")
            print(f"Location: {job.get('location')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_working_nomads()
