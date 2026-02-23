import logging
import os
from src.reporting.email_sender import send_daily_digest
from dotenv import load_dotenv

# Load Env
load_dotenv("g:/automation projects/personal job hunter/.env")

# Configure Logging
logging.basicConfig(level=logging.INFO)

print(f"User: {os.getenv('GMAIL_USER')}")
print(f"Pass set: {'Yes' if os.getenv('GMAIL_APP_PASSWORD') else 'No'}")

# Run Sender
send_daily_digest(limit=5)
