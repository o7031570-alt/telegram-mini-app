import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager with enhanced features for @for_you_today"""
    
    def __init__(self):
        self.db_type = self._get_db_type()
        self.conn = self._create_connection()
        self._init_db()
    
    def _get_db_type(self):
        """Determine database type from environment"""
        if "DATABASE_URL" in os.environ:
            return "postgres"
        return "sqlite"
    
    def _create_connection(self):
        """Create database connection"""
        if self.db_type == "postgres":
            database_url = os.environ.get("DATABASE_URL")
            if database_url:
                # Handle Heroku-style PostgreSQL URL
                if database_url.startswith("postgres://"):
                    database_url = database_url.replace("postgres://", "postgresql://", 1)
                
                try:
                    conn = psycopg2.connect(
                        database_url,
                        cursor_factory=RealDictCursor,
                        sslmode='require' if 'railway' in database_url else 'prefer'
                    )
                    logger.info("✅ Connected to PostgreSQL database")
                    return conn
                except Exception as e:
                    logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
                    # Fallback to SQLite
                    self.db_type = "sqlite"
        
        # SQLite fallback
        os.makedirs("database", exist_ok=True)
        db_path = os.path.join("database", "posts.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        logger.info(f"✅ Connected to SQLite database: {db_path}")
        return conn
    
    def _init_db(self):
        """Initialize database tables for @for_you_today"""
        try:
            cursor = self.conn.cursor()
            
            if self.db_type == "postgres":
                # PostgreSQL schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                        id SERIAL PRIMARY KEY,
                        message_id BIGINT UNIQUE NOT NULL,
                        content TEXT,
                        media_type VARCHAR(50) NOT NULL,
                        category VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        additional_info TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        channel_username VARCHAR(100) DEFAULT '@for_you_today'
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS logs (
                        id SERIAL PRIMARY KEY,
                        level VARCHAR(20) NOT NULL,
                        source VARCHAR(50) NOT NULL,
                        action VARCHAR(100) NOT NULL,
                        details TEXT,
                        error_type VARCHAR(100),
                        error_message TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS channel_stats (
                        id SERIAL PRIMARY KEY,
                        total_posts INTEGER DEFAULT 0,
                        last_post_time TIMESTAMP,
                        categories JSONB,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp DESC);
                    CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category);
                    CREATE INDEX IF NOT EXISTS idx_posts_channel ON posts(channel_username);
                    CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC);
                """)
                
            else:
                # SQLite schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id INTEGER UNIQUE NOT NULL,
                        content TEXT,
                        media_type TEXT NOT NULL,
                        category TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        additional_info TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        channel_username TEXT DEFAULT '@for_you_today'
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        level TEXT NOT NULL,
                        source TEXT NOT NULL,
                        action TEXT NOT NULL,
                        details TEXT,
                        error_type TEXT,
                        error_message TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS channel_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        total_posts INTEGER DEFAULT 0,
                        last_post_time DATETIME,
                        categories TEXT,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp DESC);
                    CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category);
                """)
            
            self.conn.commit()
            logger.info("✅ Database tables initialized for @for_you_today")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            self.conn.rollback()
    
    def save_message(self, message_id: int, content: str, media_type: str, 
                     category: str, timestamp: datetime, additional_info: str = None) -> bool:
        """Save a message from @for_you_today channel"""
        try:
            cursor = self.conn.cursor()
            
            if self.db_type == "postgres":
                cursor.execute("""
                    INSERT INTO posts (message_id, content, media_type, category, timestamp, additional_info)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (message_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        media_type = EXCLUDED.media_type,
                        category = EXCLUDED.category,
                        timestamp = EXCLUDED.timestamp,
                        additional_info = EXCLUDED.additional_info
                """, (message_id, content, media_type, category, timestamp, additional_info))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO posts 
                    (message_id, content, media_type, category, timestamp, additional_info)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (message_id, content, media_type, category, timestamp, additional_info))
            
            self.conn.commit()
            logger.info(f"✅ Saved message {message_id} from @for_you_today")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save message {message_id}: {e}")
            self.conn.rollback()
            return False
    
    def get_all_posts(self, category: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all posts from @for_you_today channel"""
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT * FROM posts WHERE channel_username = '@for_you_today'"
            params = []
            
            if category:
                if self.db_type == "postgres":
                    query += " AND category = %s"
                else:
                    query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                if self.db_type == "postgres":
                    query += " LIMIT %s"
                else:
                    query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            
            if self.db_type == "postgres":
                rows = cursor.fetchall()
                posts = [dict(row) for row in rows]
            else:
                rows = cursor.fetchall()
                posts = [dict(row) for row in rows]
            
            # Convert datetime objects to ISO format
            for post in posts:
                for key in ['timestamp', 'created_at']:
                    if key in post and post[key]:
                        if isinstance(post[key], datetime):
                            post[key] = post[key].isoformat()
                # Ensure channel info
                post['channel'] = '@for_you_today'
                post['channel_url'] = 'https://t.me/for_you_today'
            
            return posts
            
        except Exception as e:
            logger.error(f"❌ Failed to get posts: {e}")
            return []
    
    def search_posts(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search posts from @for_you_today channel"""
        try:
            cursor = self.conn.cursor()
            
            if self.db_type == "postgres":
                sql = """
                    SELECT * FROM posts 
                    WHERE channel_username = '@for_you_today' 
                    AND content ILIKE %s
                """
                params = [f"%{query}%"]
            else:
                sql = """
                    SELECT * FROM posts 
                    WHERE channel_username = '@for_you_today' 
                    AND content LIKE ?
                """
                params = [f"%{query}%"]
            
            if category:
                if self.db_type == "postgres":
                    sql += " AND category = %s"
                else:
                    sql += " AND category = ?"
                params.append(category)
            
            sql += " ORDER BY timestamp DESC"
            
            cursor.execute(sql, params)
            
            if self.db_type == "postgres":
                rows = cursor.fetchall()
                posts = [dict(row) for row in rows]
            else:
                rows = cursor.fetchall()
                posts = [dict(row) for row in rows]
            
            # Convert datetime objects
            for post in posts:
                for key in ['timestamp', 'created_at']:
                    if key in post and post[key]:
                        if isinstance(post[key], datetime):
                            post[key] = post[key].isoformat()
                post['channel'] = '@for_you_today'
            
            return posts
            
        except Exception as e:
            logger.error(f"❌ Failed to search posts: {e}")
            return []
    
    def get_post_by_id(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific post by message ID"""
        try:
            cursor = self.conn.cursor()
            
            if self.db_type == "postgres":
                cursor.execute("""
                    SELECT * FROM posts 
                    WHERE message_id = %s AND channel_username = '@for_you_today'
                """, (message_id,))
            else:
                cursor.execute("""
                    SELECT * FROM posts 
                    WHERE message_id = ? AND channel_username = '@for_you_today'
                """, (message_id,))
            
            if self.db_type == "postgres":
                row = cursor.fetchone()
                if row:
                    post = dict(row)
                else:
                    return None
            else:
                row = cursor.fetchone()
                if row:
                    post = dict(row)
                else:
                    return None
            
            # Convert datetime
            for key in ['timestamp', 'created_at']:
                if key in post and post[key]:
                    if isinstance(post[key], datetime):
                        post[key] = post[key].isoformat()
            
            post['channel'] = '@for_you_today'
            post['channel_url'] = 'https://t.me/for_you_today'
            
            return post
            
        except Exception as e:
            logger.error(f"❌ Failed to get post {message_id}: {e}")
            return None
    
    def get_post_count(self) -> int:
        """Get total number of posts from @for_you_today"""
        try:
            cursor = self.conn.cursor()
            
            if self.db_type == "postgres":
                cursor.execute("""
                    SELECT COUNT(*) as count FROM posts 
                    WHERE channel_username = '@for_you_today'
                """)
                result = cursor.fetchone()
                return result['count']
            else:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM posts 
                    WHERE channel_username = '@for_you_today'
                """)
                result = cursor.fetchone()
                return result[0]
                
        except Exception as e:
            logger.error(f"❌ Failed to get post count: {e}")
            return 0
    
    def get_category_stats(self) -> Dict[str, int]:
        """Get post count by category for @for_you_today"""
        try:
            cursor = self.conn.cursor()
            
            if self.db_type == "postgres":
                cursor.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM posts 
                    WHERE channel_username = '@for_you_today'
                    GROUP BY category 
                    ORDER BY count DESC
                """)
                rows = cursor.fetchall()
                return {row['category']: row['count'] for row in rows}
            else:
                cursor.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM posts 
                    WHERE channel_username = '@for_you_today'
                    GROUP BY category 
                    ORDER BY count DESC
                """)
                rows = cursor.fetchall()
                return {row[0]: row[1] for row in rows}
                
        except Exception as e:
            logger.error(f"❌ Failed to get category stats: {e}")
            return {}
    
    def log_error(self, error_type: str, error_message: str, update_id: Optional[int] = None):
        """Log an error to the database"""
        try:
            cursor = self.conn.cursor()
            
            if self.db_type == "postgres":
                cursor.execute("""
                    INSERT INTO logs (level, source, action, error_type, error_message)
                    VALUES ('error', 'bot', 'error_handler', %s, %s)
                """, (error_type, error_message))
            else:
                cursor.execute("""
                    INSERT INTO logs (level, source, action, error_type, error_message)
                    VALUES ('error', 'bot', 'error_handler', ?, ?)
                """, (error_type, error_message))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"❌ Failed to log error: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        return {
            'type': self.db_type,
            'channel': '@for_you_today',
            'post_count': self.get_post_count(),
            'categories': list(self.get_category_stats().keys())
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        self.close()