  -- Create posts table
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    message_id INTEGER UNIQUE NOT NULL,
    content TEXT NOT NULL,
    media_type VARCHAR(50) DEFAULT 'text',
    category VARCHAR(100) DEFAULT 'general',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_posts_message_id ON posts(message_id);
CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category);
CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp DESC);

-- Insert sample data (optional)
INSERT INTO posts (message_id, content, media_type, category, timestamp) VALUES
(1, 'Welcome to our channel!', 'text', 'general', '2024-01-01 10:00:00'),
(2, 'Important announcement', 'text', 'important', '2024-01-02 11:00:00'),
(3, 'News update for today', 'text', 'news', '2024-01-03 12:00:00')
ON CONFLICT (message_id) DO NOTHING;