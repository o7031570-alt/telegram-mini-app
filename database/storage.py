"""
Database storage module for PostgreSQL on Railway
"""

import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration for Railway
def get_database_url():
    """Get database URL with proper formatting"""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # Fix for Railway's PostgreSQL URL
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        logger.info("Using PostgreSQL database from Railway")
        return DATABASE_URL
    else:
        # Fallback to SQLite for local development
        os.makedirs('./database', exist_ok=True)
        DATABASE_URL = "sqlite:///./database/posts.db"
        logger.warning("Using SQLite as DATABASE_URL is not set. This is for local testing only.")
        return DATABASE_URL

# Get database URL
DATABASE_URL = get_database_url()

# Configure engine with connection pooling for PostgreSQL
engine_kwargs = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

if 'postgresql' in DATABASE_URL:
    # PostgreSQL specific settings
    engine_kwargs.update({
        'pool_size': 5,
        'max_overflow': 10,
        'echo': False
    })

try:
    engine = create_engine(DATABASE_URL, **engine_kwargs)
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
    
    if 'postgresql' in DATABASE_URL:
        logger.info("✅ PostgreSQL database connected successfully")
    else:
        logger.info("✅ SQLite database connected successfully")
    
except Exception as e:
    logger.error(f"❌ Database connection error: {e}")
    raise

class ChannelStorage:
    def __init__(self):
        self.db = SessionLocal()
        logger.info("Database storage initialized")
    
    def save_post(self, post_data):
        """Save a post to database"""
        try:
            # Check if post already exists
            existing = self.db.query(Post).filter(
                Post.message_id == post_data.get('message_id')
            ).first()
            
            if existing:
                # Update existing post
                existing.content = post_data.get('content', existing.content)
                existing.media_type = post_data.get('media_type', existing.media_type)
                existing.category = post_data.get('category', existing.category)
                existing.timestamp = post_data.get('timestamp', existing.timestamp)
                self.db.commit()
                return True
            else:
                # Create new post
                post = Post(
                    message_id=post_data.get('message_id'),
                    content=post_data.get('content', ''),
                    media_type=post_data.get('media_type', 'text'),
                    category=post_data.get('category', 'general'),
                    timestamp=post_data.get('timestamp')
                )
                self.db.add(post)
                self.db.commit()
                return True
                
        except SQLAlchemyError as e:
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
        except SQLAlchemyError as e:
            logger.error(f"Error fetching posts: {e}")
            return []
    
    def count_posts(self, category=None):
        """Count total posts with optional filtering"""
        try:
            query = self.db.query(func.count(Post.id))
            
            if category:
                query = query.filter(Post.category == category)
            
            return query.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Error counting posts: {e}")
            return 0
    
    def get_categories(self):
        """Get all unique categories"""
        try:
            categories = self.db.query(Post.category).distinct().all()
            return [cat[0] for cat in categories if cat[0]]
        except SQLAlchemyError as e:
            logger.error(f"Error getting categories: {e}")
            return ['general']
    
    def get_post_by_id(self, message_id):
        """Get a specific post by message_id"""
        try:
            post = self.db.query(Post).filter(Post.message_id == message_id).first()
            return post.to_dict() if post else None
        except SQLAlchemyError as e:
            logger.error(f"Error getting post by ID: {e}")
            return None
    
    def get_recent_posts(self, days=7):
        """Get recent posts from last N days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            posts = self.db.query(Post).filter(
                Post.timestamp >= cutoff_date
            ).order_by(Post.timestamp.desc()).all()
            
            return [post.to_dict() for post in posts]
        except SQLAlchemyError as e:
            logger.error(f"Error getting recent posts: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        self.db.close()

# Create global instance
storage = ChannelStorage()