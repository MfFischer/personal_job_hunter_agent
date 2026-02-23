CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY, -- URL hash or UUID
    title TEXT,
    company TEXT,
    url TEXT UNIQUE,
    description TEXT,
    source TEXT,
    posted_date TEXT,
    is_remote BOOLEAN,
    raw_data JSON,
    job_hash TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS ai_usage_log (
    date TEXT PRIMARY KEY,
    request_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS job_scores (
    job_id TEXT PRIMARY KEY,
    keyword_score INTEGER,
    is_excluded BOOLEAN,
    exclusion_reason TEXT,
    ai_match_score INTEGER DEFAULT 0,
    ai_analysis_json JSON,
    language TEXT, -- 'DE' or 'EN'
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    status TEXT DEFAULT 'pending', -- pending, generated, applied, rejected
    cover_letter_text TEXT,
    notes TEXT,
    is_reported BOOLEAN DEFAULT 0,
    reported_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
