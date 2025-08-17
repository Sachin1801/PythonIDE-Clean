-- Users table
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT CHECK(role IN ('student', 'professor')) DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- File metadata table
CREATE TABLE file_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    file_path TEXT NOT NULL,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_submitted BOOLEAN DEFAULT 0,
    submission_id TEXT UNIQUE,
    grade REAL,
    feedback TEXT,
    graded_by TEXT,
    graded_at TIMESTAMP,
    UNIQUE(username, file_path),
    FOREIGN KEY(username) REFERENCES users(username)
);

-- Sessions table
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY(username) REFERENCES users(username)
);

-- Create indexes
CREATE INDEX idx_submission_id ON file_metadata(submission_id);
CREATE INDEX idx_username_path ON file_metadata(username, file_path);
CREATE INDEX idx_sessions_username ON sessions(username);