import logging
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from src.main import main as run_pipeline
from src.reporting.email_sender import send_daily_digest

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
                    , filename='daily_run.log', filemode='a')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

def daily_job():
    logging.info("=== Starting Daily Job Hunter Run ===")
    
    try:
        # 1. Run the Core Pipeline (Fetch, Filter, Analyze, Generate)
        run_pipeline()
        
        # 2. Wait a bit to ensure DB writes are fully committed (safety)
        time.sleep(5)
        
        # 3. Send the Report
        logging.info(">>> Starting Reporting Phase")
        send_daily_digest(limit=30)
        
    except Exception as e:
        logging.error(f"Critical Error in Daily Run: {e}")
        import traceback
        logging.error(traceback.format_exc())

    logging.info("=== Daily Run Complete ===\n")

if __name__ == "__main__":
    daily_job()
