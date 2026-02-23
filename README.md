# 🤖 Autonomous Job Hunter Agent

An autonomous, 24/7 AI-powered job acquisition engine that scrapes remote tech jobs, aggressively filters them against your personal resume using localized AI matching, and autonomously drafts customized cover letters for the highest-scoring matches using the Gemini API.

## 🌟 Highlights

- **100% Free to Run:** Uses WWR/RemoteOK feeds and the Google Gemini 2.0 Flash Free Tier.
- **Smart Pacing:** Engineered to maximize the API Free Tier (processes up to 30 top-tier jobs per day without hitting the 15 RPM limits).
- **Aggressive Local Filtering:** Before making any costly API calls, the agent downloads 10,000-character job descriptions via `BeautifulSoup` and strictly checks them against your exact tech stack and roles.
- **Zero Hallucination Generation:** The embedded AI prompt rigorously enforces a professional, factual tone based _only_ on the skills found in your resume.

---

## 🚀 Quick Start Guide (Desktop / Local)

### 1. Requirements

- Python 3.10+
- A Google Gemini API Key (Get one free at [Google AI Studio](https://aistudio.google.com/))
- A Gmail Account with an "App Password" (for sending the daily report)

### 2. Setup

Clone the repository, create a virtual environment, and install the dependencies:

```bash
git clone https://github.com/MfFischer/personal_job_hunter_agent.git
cd personal_job_hunter_agent
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration

1. Rename `.env.example` to `.env`.
2. Fill in your credentials:

```env
GEMINI_API_KEY="AIzaSyYourKeyHere..."
GMAIL_USER="your.email@gmail.com"
GMAIL_APP_PASSWORD="abcd efgh ijkl mnop"
```

### 4. Inject Your Brain (The Resume)

The agent needs to know exactly who you are to filter jobs and write letters.

1. Place your resume in the `assets/` folder and name it **`cv_en.pdf`**.
2. Run the intelligence extractor:

```bash
python src/analysis/resume_parser.py
```

> **What this does:** The AI will read your PDF, extract your core roles, primary tech stack, and secondary stack, and generate a highly-structured `data/profile.json` file. **If you ever update your resume, you must run this command again** so the agent learns your new skills!

### 5. Run the Engine

You can manually run the entire pipeline (Scrape -> Filter -> Analyze -> Generate -> Email) with one command:

```bash
python daily_run.py
```

_Note: The script includes 30-second delays during the AI phase to respect Gemini's free-tier rate limits. A full run with 30 jobs may take ~15 minutes._

---

## ☁️ Running on a Cloud VPS (24/7 Automation)

If you want the agent to hunt for jobs while you sleep, deploy it to a Linux VPS (Ubuntu/Debian).

1. Upload the project folder to your VPS (e.g., `/var/www/jobhunter`).
2. Run the included setup script:

```bash
chmod +x setup_remote.sh
./setup_remote.sh
```

3. Add a Cron job to run the agent every morning at 09:30:

```bash
crontab -e
```

Add this line:

```text
30 9 * * * cd /var/www/jobhunter && /var/www/jobhunter/venv/bin/python daily_run.py >> /var/www/jobhunter/job_hunter.log 2>&1
```

---

## 🧠 Architecture Overview

**Layer 1: Broad Discovery**
Scrapes high-volume URLs (We Work Remotely, RemoteOK, Remotive) searching for generic categories like `software-dev` or `product`.

**Layer 2: Local Aggressive Filtering**
Uses `BeautifulSoup` to scrape the full webpage of each job. It then instantly discards any job that doesn't contain matching keywords locally extracted from your `profile.json` (saving AI costs).

**Layer 3: Remote AI Analysis**
The Top 30 surviving jobs are sent to Gemini to analyze the domain, true remote status, and assign a `/100` Match Score based strictly on your PDF.

**Layer 4: Document Generation & Reporting**
Gemini drafts a customized cover letter for highly matched jobs. Finally, the server complies an HTML email report with the job links, pros/cons, and attached cover letters, sending it straight to your inbox.
