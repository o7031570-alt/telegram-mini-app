#!/usr/bin/env python3
"""
SQLite storage module for Telegram channel posts.
Termux-compatible paths.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path
import logging

# Termux-compatible relative path
DB_PATH = Path(__file__).parent / "posts.db"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChannelStorage:
    """SQLite storage for Telegram channel posts"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._init_db()
    
    def _init_db(self):
        """Initialize database with required tables"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    media_type TEXT DEFAULT 'text',
                    category TEXT DEFAULT 'general',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(message_id)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_category 
                ON posts(category)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON posts(timestamp)
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def save_post(self, message_id, content, media_type='text', category='general'):
        """Save a channel post to database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO posts 
                (message_id, content, media_type, category, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (message_id, content, media_type, category, datetime.now()))
            
            conn.commit()
            conn.close()
            logger.info(f"Post saved: {message_id} ({category})")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to save post {message_id}: {e}")
            return False
    
    def fetch_posts(self, category=None, limit=100, offset=0):
        """Fetch posts from database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT * FROM posts 
                    WHERE category = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                ''', (category, limit, offset))
            else:
                cursor.execute('''
                    SELECT * FROM posts 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
            
            rows = cursor.fetchall()
            conn.close()
            
            posts = [dict(row) for row in rows]
            logger.info(f"Fetched {len(posts)} posts")
            return posts
            
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch posts: {e}")
            return []
    
    def count_posts(self, category=None):
        """Count total posts"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            if category:
                cursor.execute('SELECT COUNT(*) FROM posts WHERE category = ?', (category,))
            else:
                cursor.execute('SELECT COUNT(*) FROM posts')
            
            count = cursor.fetchone()[0]
            conn.close()
            return count
            
        except sqlite3.Error as e:
            logger.error(f"Failed to count posts: {e}")
            return 0
    
    def get_categories(self):
        """Get list of all unique categories"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('SELECT DISTINCT category FROM posts ORDER BY category')
            categories = [row[0] for row in cursor.fetchall()]
            conn.close()
            return categories
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get categories: {e}")
            return []


# Convenience functions
def save_post(message_id, content, media_type='text', category='general'):
    storage = ChannelStorage()
    return storage.save_post(message_id, content, media_type, category)

def fetch_posts(category=None, limit=100, offset=0):
    storage = ChannelStorage()
    return storage.fetch_posts(category, limit, offset)
