import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import logging
from src.database import db_manager

def send_daily_digest(limit=30, to_email="afefischer@gmail.com"):
    logging.info(f"Preparing Daily Digest for {to_email}...")
    
    # 1. Fetch Top Unreported Jobs
    conn = db_manager.get_connection()
    conn.row_factory = db_manager.sqlite3.Row
    cursor = conn.cursor()
    
    # Query logic: Unreported, has AI score, not excluded
    cursor.execute('''
        SELECT j.*, s.ai_match_score, s.ai_analysis_json, s.language, a.cover_letter_text, a.id as app_id
        FROM jobs j
        JOIN job_scores s ON j.id = s.job_id
        LEFT JOIN applications a ON j.id = a.job_id
        WHERE s.ai_match_score > 0
          AND (a.is_reported IS NULL OR a.is_reported = 0)
        ORDER BY s.ai_match_score DESC
        LIMIT ?
    ''', (limit,))
    
    jobs = [dict(row) for row in cursor.fetchall()]
    
    if not jobs:
        logging.info("No new jobs to report.")
        return

    # 2. Construct Email
    msg = MIMEMultipart()
    msg['Subject'] = f"Job Hunter Daily Digest: {len(jobs)} Top Candidates"
    msg['From'] = os.getenv("GMAIL_USER")
    msg['To'] = to_email

    html_body = "<h1>🚀 Top Job Candidates for Today</h1>"
    
    import json
    
    import re
    import urllib.parse

    for job in jobs:
        score = job['ai_match_score']
        analysis = json.loads(job['ai_analysis_json']) if job['ai_analysis_json'] else {}
        domain = analysis.get('job_domain', 'General')
        cover_letter = job.get('cover_letter_text', '')

        # --- SMART FEATURES ---
        # 1. Extract Email for Mailto
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        match = re.search(email_pattern, job['description'] or '')
        contact_email = match.group(0) if match else ""
        
        # 2. Build Mailto Link
        mailto_link = ""
        if contact_email:
            subject = urllib.parse.quote(f"Application for {job['title']} - {domain} Candidate")
            # We can't pre-fill full cover letter in mailto body (URL length limits), 
            # so we just put a starter or the full thing if short.
            # Using concise check-in.
            body = urllib.parse.quote(f"Dear Hiring Team,\n\nPlease find my application attached.\n\nBest,\nMaria")
            mailto_link = f'<a href="mailto:{contact_email}?subject={subject}&body={body}" style="background-color: #9b59b6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-left: 10px;">✉️ Email Application</a>'
        
        # 3. Add Attachment (Virtual - we write to temp file then attach)
        # We handle actual attachment logic below in the loop by creating MIMEApplication parts
        
        html_body += f"""
        <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 8px; font-family: sans-serif;">
            <h2 style="color: {'#2ecc71' if score > 85 else '#f39c12'}; margin-top: 0;">{job['title']} (Score: {score})</h2>
            <p style="font-size: 14px; color: #555;">
                <strong>Company:</strong> {job['company']} | 
                <strong>Domain:</strong> {domain} | 
                <strong>Location:</strong> {'Remote' if job['is_remote'] else 'Onsite'}
            </p>
            
            <div style="margin: 15px 0;">
                <a href="{job['url']}" style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">👉 View Job</a>
                {mailto_link}
                <p style="font-size: 11px; color: #888; margin-top: 5px;">Link: <a href="{job['url']}">{job['url']}</a></p>
            </div>
            
            <div style="background-color: #f9f9f9; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                <strong>Why match?</strong>
                <ul style="margin: 5px 0; padding-left: 20px;">
                    {"".join([f"<li>{p}</li>" for p in analysis.get('pros', [])[:3]])}
                </ul>
            </div>
            
            <h3>Cover Letter Draft:</h3>
            <p style="font-size: 12px; color: #7f8c8d;"><i>Attached as .txt file. Preview:</i></p>
            <textarea style="width: 100%; height: 100px; font-family: monospace; padding: 10px; border: 1px solid #ccc;">{cover_letter[:500]}...</textarea>
        </div>
        """
        
        # Attach Cover Letter as TXT
        if cover_letter:
            fname = f"cover_letter_{job['id'][:8]}.txt"
            part = MIMEApplication(cover_letter.encode('utf-8'), Name=fname)
            part['Content-Disposition'] = f'attachment; filename="{fname}"'
            msg.attach(part)
        
        # Mark as reported (Optimistic update)
        if job['app_id']:
            cursor.execute("UPDATE applications SET is_reported = 1, reported_at = CURRENT_TIMESTAMP WHERE id = ?", (job['app_id'],))
        else:
            # If application didn't exist for some reason, create stub
            pass 

    msg.attach(MIMEText(html_body, 'html'))
    
    # 3. Attach CVs (Simulated based on Language)
    # In a full run, we would attach specific CVs per job, but for digest we attach both
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cv_en = os.path.join(base_dir, "assets", "cv_en.pdf")
    if os.path.exists(cv_en):
        with open(cv_en, "rb") as f:
            part = MIMEApplication(f.read(), Name="CV_English.pdf")
            part['Content-Disposition'] = 'attachment; filename="CV_English.pdf"'
            msg.attach(part)

    # 4. Send
    try:
        user = os.getenv("GMAIL_USER")
        password = os.getenv("GMAIL_APP_PASSWORD")
        
        if not user or not password:
            logging.error("GMAIL credentials not set in .env. Skipping email.")
            return

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
            server.send_message(msg)
            
        conn.commit()
        logging.info(f"Email sent successfully with {len(jobs)} jobs.")
        
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        conn.rollback()
    
    conn.close()
