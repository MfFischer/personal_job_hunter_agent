import feedparser
import requests
from bs4 import BeautifulSoup
import logging

class JobScraper:
    def fetch_jobs(self):
        raise NotImplementedError

class RSSScraper(JobScraper):
    def __init__(self, rss_url, source_name="RSS"):
        self.rss_url = rss_url
        self.source_name = source_name

    def fetch_jobs(self):
        feed = feedparser.parse(self.rss_url)
        jobs = []
        logging.info(f"Fetching RSS: {self.rss_url} ({len(feed.entries)} entries)")
        
        for entry in feed.entries:
            url = entry.get('link')
            description = entry.get('summary', '') or entry.get('description', '')
            
            # --- DEEP SCRAPE START ---
            # WWR already provides full text in summary (10k+ chars). Deep scraping triggers 403.
            if "weworkremotely.com" in url:
                pass # Summary is sufficient
            else:
                try:
                    full_text = self._fetch_full_description(url)
                    if full_text and len(full_text) > len(description):
                        description = full_text # Upgrade to full text
                except Exception as e:
                    logging.warning(f"Deep Scrape failed for {url}: {e}")
            # --- DEEP SCRAPE END ---

            jobs.append({
                "title": entry.get('title', 'No Title'),
                "company": entry.get('author', 'Unknown'), 
                "url": url,
                "description": description,
                "source": self.source_name,
                "posted_date": entry.get('published'),
                "is_remote": True 
            })
        return jobs

    def _fetch_full_description(self, url):
        """Fetches the URL and extracts text from <main>, <article>, or <body>."""
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) User-Job-Hunter/1.0'}, timeout=5)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Priority tags for job content
            content = None
            for selector in ['main', 'article', '#job-description', '.job-description', 'body']:
                element = soup.select_one(selector)
                if element:
                    # Remove scripts and styles
                    for script in element(["script", "style", "nav", "footer", "header"]):
                        script.extract()
                    content = element.get_text(separator=' ', strip=True)
                    break
            
            return content if content and len(content) > 500 else None
        except Exception:
            return None

class JSONScraper(JobScraper):
    def __init__(self, json_url, source_name="JSON"):
        self.json_url = json_url
        self.source_name = source_name

    def fetch_jobs(self):
        logging.info(f"Fetching JSON: {self.json_url}")
        try:
            # Add explicit User-Agent to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            resp = requests.get(self.json_url, headers=headers, timeout=10)
            if resp.status_code != 200:
                logging.error(f"Failed to fetch JSON: {resp.status_code}")
                logging.error(f"Response: {resp.text[:200]}")
                return []
            
            try:
                data = resp.json()
            except Exception:
                logging.error("Failed to parse JSON response. Content might be HTML.")
                return []
                
            # RemoteOK returns a list where 1st item is metadata (sometimes) or strict list of jobs
            # It seems RemoteOK returns [ {metadata}, {job}, {job}... ]
            
            jobs = []
            for item in data:
                # Ensure it's a dict
                if not isinstance(item, dict): continue
                
                # RemoteOK uses 'position' for title
                title = item.get('title') or item.get('position')
                url = item.get('url') or item.get('apply_url')
                
                if not title or not url:
                    continue # Skip metadata block or invalid items
                
                jobs.append({
                    "title": title,
                    "company": item.get('company', 'Unknown'),
                    "url": url,
                    "description": item.get('description', ''), # Usually contains HTML
                    "source": self.source_name,
                    "posted_date": item.get('date'),
                    "is_remote": True 
                })
            logging.info(f"JSON Scraper found {len(jobs)} jobs.")
            return jobs
        except Exception as e:
            logging.error(f"JSON Scraper Error: {e}")
            return []

class SimpleHTMLScraper(JobScraper):
    def __init__(self, url, source_name="HTML"):
        self.url = url
        self.source_name = source_name

    def fetch_jobs(self):
        # Extremely basic implementation for PoC
        # Real world would need specific selectors per site
        try:
            resp = requests.get(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(resp.text, 'html.parser')
            jobs = []
            # Mock Scrape: Find all 'a' tags with 'job' in href
            for link in soup.find_all('a', href=True):
                if 'job' in link['href'] or 'career' in link['href']:
                    jobs.append({
                        "title": link.text.strip(),
                        "company": "Unknown",
                        "url": link['href'] if link['href'].startswith('http') else self.url + link['href'],
                        "description": "Click to view description", # HTML scraping without deep crawling
                        "source": self.source_name,
                        "posted_date": None,
                        "is_remote": False
                    })
            return jobs
        except Exception as e:
            logging.error(f"Error scraping {self.url}: {e}")
            return []

class RemotiveScraper(JobScraper):
    def __init__(self, url, source_name="Remotive"):
        self.url = url
        self.source_name = source_name

    def fetch_jobs(self):
        logging.info(f"Fetching Remotive JSON: {self.url}")
        try:
            resp = requests.get(self.url, timeout=10)
            if resp.status_code != 200:
                logging.error(f"Failed to fetch Remotive JSON: {resp.status_code}")
                return []
            
            data = resp.json()
            raw_jobs = data.get('jobs', [])
            jobs = []
            
            # EU/Worldwide Location strict pre-filter
            # Remotive often uses exact strings or lists like "USA, UK, Europe"
            valid_locations = ["worldwide", "anywhere", "europe", "germany", "uk", "remote", "global", "eu", "emea"]
            invalid_locations = ["us only", "usa only", "north america", "americas only", "latin america"]
            
            for item in raw_jobs:
                location_raw = item.get('candidate_required_location', '')
                location = str(location_raw).lower() if location_raw else ""
                
                # Check for explicit invalid locations first
                is_invalid = False
                for invalid in invalid_locations:
                    if invalid in location:
                        is_invalid = True
                        break
                
                if is_invalid:
                    continue
                    
                # Check if it mentions a valid location or is just "worldwide"
                is_valid = False
                if not location: # If empty String, assume worldwide on this board
                    is_valid = True
                else:
                    # In Remotive "Remote" usually means worldwide if not otherwise specified
                    for valid in valid_locations:
                        if valid in location:
                            is_valid = True
                            break
                            
                if not is_valid:
                    continue # Skip if it requires somewhere else (e.g., 'Asia Only')

                jobs.append({
                    "title": item.get('title', 'No Title'),
                    "company": item.get('company_name', 'Unknown'),
                    "url": item.get('url'),
                    "description": item.get('description', ''),
                    "source": self.source_name,
                    "posted_date": item.get('publication_date'),
                    "is_remote": True 
                })
            logging.info(f"Remotive Scraper found {len(jobs)} jobs (Filtered for EU/Worldwide).")
            return jobs
        except Exception as e:
            logging.error(f"Remotive Scraper Error: {e}")
            return []

