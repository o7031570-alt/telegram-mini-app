CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    media_type TEXT DEFAULT 'text',
    category TEXT DEFAULT 'general',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id)
);

CREATE INDEX IF NOT EXISTS idx_category ON posts(category);
CREATE INDEX IF NOT EXISTS idx_timestamp ON posts(timestamp);
