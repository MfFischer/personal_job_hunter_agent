import requests
from bs4 import BeautifulSoup

def test_google_jobs():
    # Google Jobs doesn't have a clean, public RSS feed. 
    # Directly scraping the search page often hits generic search results or Captchas.
    # An alternative is using specialized aggregators that have RSS like Indeed/Glassdoor (often blocked)
    # or smaller tech boards with RSS.
    
    # Let's test a generic Google search for remote jobs to see what we get.
    url = "https://www.google.com/search?q=remote+python+jobs+europe&ibp=htl;jobs"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    print(f"Testing Google Jobs Scrape: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Google Jobs results are usually inside a specific div class, which changes frequently.
        # Let's look for common job-related text to see if we got the actual UI or a Captcha.
        text = soup.get_text().lower()
        if "did you mean" in text or "captcha" in text:
            print("WARNING: Likely blocked or hit captcha.")
            
        # Try to find list items or divs that might be jobs
        # Often they use 'li' under specific 'ul' or complex div structures.
        job_titles = soup.find_all('div', class_='BjJfJf PUpOsf') # Example class, likely wrong/changed
        print(f"Found {len(job_titles)} elements with standard Google Job class (BjJfJf PUpOsf).")
        
        # Let's just print a snippet of the HTML to see what we are dealing with.
        print("\nHTML Snippet (first 1000 chars):")
        print(response.text[:1000])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_google_jobs()
