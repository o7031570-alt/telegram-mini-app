import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get DATABASE_URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    # Fallback to SQLite
    os.makedirs('database', exist_ok=True)
    DATABASE_URL = "sqlite:///database/posts.db"
    logger.warning("⚠️ Using SQLite as DATABASE_URL is not set. This is for local testing only.")

# Fix PostgreSQL URL format
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Configure engine based on database type
if 'sqlite' in DATABASE_URL:
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={'check_same_thread': False},  # SQLite specific
        echo=False  # Turn off SQL echo
    )
else:
    # PostgreSQL configuration
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, unique=True, nullable=False)
    content = Column(Text, nullable=False)
    media_type = Column(String(50), default='text')
    category = Column(String(100), default='general')
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'content': self.content,
            'media_type': self.media_type,
            'category': self.category,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

def init_database():
    """Initialize database tables one by one to avoid SQLite errors"""
    try:
        # Create tables one by one
        Base.metadata.create_all(bind=engine, tables=[Post.__table__])
        
        if 'sqlite' in DATABASE_URL:
            logger.info(f"✅ Connected to SQLite database: database/posts.db")
        else:
            logger.info(f"✅ Connected to PostgreSQL database")
            
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        
        # Try alternative approach for SQLite
        if 'sqlite' in DATABASE_URL:
            try:
                logger.info("🔄 Trying alternative SQLite initialization...")
                
                # Use raw SQL for SQLite
                with engine.connect() as conn:
                    conn.execute('''
                        CREATE TABLE IF NOT EXISTS posts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            message_id INTEGER UNIQUE NOT NULL,
                            content TEXT NOT NULL,
                            media_type TEXT DEFAULT 'text',
                            category TEXT DEFAULT 'general',
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    conn.commit()
                    
                logger.info("✅ SQLite tables created successfully")
                return True
            except Exception as e2:
                logger.error(f"❌ SQLite initialization also failed: {str(e2)}")
        
        return False

# Initialize database
db_initialized = init_database()

class ChannelStorage:
    def __init__(self):
        self.session = SessionLocal()
        logger.info("📊 ChannelStorage initialized")
    
    def fetch_posts(self, limit=100, offset=0):
        """Fetch posts from database"""
        try:
            if not db_initialized:
                return []
                
            posts = self.session.query(Post).order_by(Post.timestamp.desc()).limit(limit).offset(offset).all()
            return [p.to_dict() for p in posts]
        except Exception as e:
            logger.error(f"Error fetching posts: {e}")
            return []
        finally:
            self.session.close()
    
    def count_posts(self, category=None):
        """Count total posts"""
        try:
            if not db_initialized:
                return 0
                
            query = self.session.query(Post)
            if category:
                query = query.filter(Post.category == category)
            return query.count()
        except Exception as e:
            logger.error(f"Error counting posts: {e}")
            return 0
        finally:
            self.session.close()
    
    def get_categories(self):
        """Get all unique categories"""
        try:
            if not db_initialized:
                return []
                
            categories = self.session.query(Post.category).distinct().all()
            return [c[0] for c in categories if c[0]]
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
        finally:
            self.session.close()
    
    def add_sample_data(self):
        """Add sample data for testing"""
        try:
            if not db_initialized:
                return False
                
            # Check if data already exists
            count = self.session.query(Post).count()
            if count == 0:
                sample_posts = [
                    Post(
                        message_id=1,
                        content="Welcome to Telegram Mini App! This is a sample post.",
                        media_type="text",
                        category="general"
                    ),
                    Post(
                        message_id=2,
                        content="Important announcement for all users.",
                        media_type="text",
                        category="important"
                    ),
                    Post(
                        message_id=3,
                        content="Daily news update with latest information.",
                        media_type="text",
                        category="news"
                    )
                ]
                
                self.session.add_all(sample_posts)
                self.session.commit()
                logger.info(f"✅ Added {len(sample_posts)} sample posts")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding sample data: {e}")
            self.session.rollback()
            return False
        finally:
            self.session.close()

# Create storage instance and add sample data if empty
try:
    storage = ChannelStorage()
    # Add sample data if database is empty
    storage.add_sample_data()
except Exception as e:
    logger.error(f"Failed to create storage: {e}")
    # Create dummy storage as fallback
    class DummyStorage:
        def fetch_posts(self, **kwargs): 
            return [
                {"id": 1, "message_id": 1, "content": "Sample post 1", "media_type": "text", "category": "general"},
                {"id": 2, "message_id": 2, "content": "Sample post 2", "media_type": "text", "category": "news"}
            ]
        def count_posts(self, category=None): 
            return 2
        def get_categories(self): 
            return ["general", "news"]
    storage = DummyStorage()