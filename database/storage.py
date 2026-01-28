"""
Database storage module for Railway PostgreSQL
"""

import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration for Railway
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Fix for Railway's PostgreSQL URL
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    logger.info("Using PostgreSQL database from Railway")
else:
    # Fallback to SQLite for local development
    DATABASE_URL = "sqlite:///./database/posts.db"
    # Create database directory if it doesn't exist
    os.makedirs('./database', exist_ok=True)
    logger.warning("Using SQLite as DATABASE_URL is not set. This is for local testing only.")

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    class Post(Base):
        __tablename__ = "posts"
        id = Column(Integer, primary_key=True, index=True)
        message_id = Column(Integer, unique=True, index=True, nullable=False)
        content = Column(Text, nullable=False)
        media_type = Column(String(50), default='text')
        category = Column(String(100), default='general')
        timestamp = Column(DateTime, default=datetime.utcnow)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        def to_dict(self):
            return {
                'id': self.id,
                'message_id': self.message_id,
                'content': self.content,
                'media_type': self.media_type,
                'category': self.category,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created/verified successfully")
    
except Exception as e:
    logger.error(f"❌ Database connection error: {e}")
    raise

class ChannelStorage:
    def __init__(self):
        self.db = SessionLocal()
        logger.info("✅ Database storage initialized")
    
    def save_post(self, post_data):
        """Save a post to database"""
        try:
            post = Post(
                message_id=post_data.get('message_id'),
                content=post_data.get('content', ''),
                media_type=post_data.get('media_type', 'text'),
                category=post_data.get('category', 'general'),
                timestamp=post_data.get('timestamp')
            )
            self.db.add(post)
            self.db.commit()
            self.db.refresh(post)
            return True
        except Exception as e:
            logger.error(f"Error saving post: {e}")
            self.db.rollback()
            return False
    
    def fetch_posts(self, category=None, limit=100, offset=0):
        """Fetch posts with optional filtering"""
        try:
            query = self.db.query(Post)
            
            if category:
                query = query.filter(Post.category == category)
            
            # Order by newest first
            query = query.order_by(Post.timestamp.desc())
            
            # Apply pagination
            posts = query.offset(offset).limit(limit).all()
            
            return [post.to_dict() for post in posts]
        except Exception as e:
            logger.error(f"Error fetching posts: {e}")
            return []
    
    def count_posts(self, category=None):
        """Count total posts with optional filtering"""
        try:
            query = self.db.query(func.count(Post.id))
            
            if category:
                query = query.filter(Post.category == category)
            
            return query.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting posts: {e}")
            return 0
    
    def get_categories(self):
        """Get all unique categories"""
        try:
            categories = self.db.query(Post.category).distinct().all()
            return [cat[0] for cat in categories if cat[0]]
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return ['general']
    
    def get_post_by_id(self, message_id):
        """Get a specific post by message_id"""
        try:
            post = self.db.query(Post).filter(Post.message_id == message_id).first()
            return post.to_dict() if post else None
        except Exception as e:
            logger.error(f"Error getting post by ID: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        self.db.close()

# Create a global instance
storage = ChannelStorage()