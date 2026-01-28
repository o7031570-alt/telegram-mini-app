"""
Simple database storage for Telegram Mini App
"""

import os
import logging
from datetime import datetime

# Try to import SQLAlchemy, but don't fail if not available
try:
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    print("⚠️ SQLAlchemy not available, using dummy storage")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChannelStorage:
    def __init__(self):
        """Initialize storage - use SQLAlchemy if available, otherwise dummy"""
        if not SQLALCHEMY_AVAILABLE:
            logger.warning("⚠️ SQLAlchemy not available, using dummy storage")
            self.dummy_mode = True
            self.dummy_data = [
                {
                    'id': 1,
                    'message_id': 1,
                    'content': 'Welcome to Telegram Mini App!',
                    'media_type': 'text',
                    'category': 'general',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'id': 2,
                    'message_id': 2,
                    'content': 'Sample post for testing',
                    'media_type': 'text',
                    'category': 'news',
                    'timestamp': datetime.now().isoformat()
                }
            ]
            return
        
        try:
            # Get database URL
            DATABASE_URL = os.environ.get('DATABASE_URL')
            
            if not DATABASE_URL:
                # Use SQLite for local development
                os.makedirs('database', exist_ok=True)
                DATABASE_URL = "sqlite:///database/posts.db"
                logger.info("📁 Using SQLite database")
            
            # Fix PostgreSQL URL format
            if DATABASE_URL.startswith('postgres://'):
                DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
            
            # Create engine
            if 'sqlite' in DATABASE_URL:
                engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
            else:
                engine = create_engine(DATABASE_URL)
            
            # Create session
            Session = sessionmaker(bind=engine)
            self.session = Session()
            
            # Define model
            Base = declarative_base()
            
            class Post(Base):
                __tablename__ = 'posts'
                id = Column(Integer, primary_key=True)
                message_id = Column(Integer, unique=True)
                content = Column(Text)
                media_type = Column(String(50), default='text')
                category = Column(String(100), default='general')
                timestamp = Column(DateTime, default=datetime.utcnow)
            
            # Create tables
            Base.metadata.create_all(engine)
            
            self.Post = Post
            self.dummy_mode = False
            
            # Add sample data if empty
            if self.session.query(Post).count() == 0:
                sample_posts = [
                    Post(
                        message_id=1,
                        content='Welcome to Telegram Mini App!',
                        media_type='text',
                        category='general'
                    ),
                    Post(
                        message_id=2,
                        content='Sample post for testing',
                        media_type='text',
                        category='news'
                    )
                ]
                self.session.add_all(sample_posts)
                self.session.commit()
                logger.info("✅ Added sample posts to database")
            
            logger.info("✅ Database storage initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            self.dummy_mode = True
            self.dummy_data = [
                {
                    'id': 1,
                    'message_id': 1,
                    'content': 'Welcome to Telegram Mini App!',
                    'media_type': 'text',
                    'category': 'general',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'id': 2,
                    'message_id': 2,
                    'content': 'Sample post for testing',
                    'media_type': 'text',
                    'category': 'news',
                    'timestamp': datetime.now().isoformat()
                }
            ]
    
    def fetch_posts(self, limit=100, offset=0):
        """Fetch posts from database"""
        if self.dummy_mode:
            return self.dummy_data[offset:offset + limit]
        
        try:
            posts = self.session.query(self.Post).order_by(self.Post.timestamp.desc()).limit(limit).offset(offset).all()
            return [
                {
                    'id': p.id,
                    'message_id': p.message_id,
                    'content': p.content,
                    'media_type': p.media_type,
                    'category': p.category,
                    'timestamp': p.timestamp.isoformat() if p.timestamp else None
                }
                for p in posts
            ]
        except Exception as e:
            logger.error(f"Error fetching posts: {e}")
            return self.dummy_data
    
    def count_posts(self, category=None):
        """Count total posts"""
        if self.dummy_mode:
            return len(self.dummy_data)
        
        try:
            query = self.session.query(self.Post)
            if category:
                query = query.filter(self.Post.category == category)
            return query.count()
        except Exception as e:
            logger.error(f"Error counting posts: {e}")
            return len(self.dummy_data)
    
    def get_categories(self):
        """Get all unique categories"""
        if self.dummy_mode:
            return list(set([p['category'] for p in self.dummy_data]))
        
        try:
            categories = self.session.query(self.Post.category).distinct().all()
            return [c[0] for c in categories if c[0]]
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return list(set([p['category'] for p in self.dummy_data]))