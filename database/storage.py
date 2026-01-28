import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway က DATABASE_URL environment variable ကိုသုံးပါ
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./database/posts.db"
    logger.warning("Using SQLite as DATABASE_URL is not set. This is for local testing only.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, unique=True, index=True, nullable=False)
    content = Column(String, nullable=False)
    media_type = Column(String, default='text')
    category = Column(String, default='general')
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class ChannelStorage:
    def __init__(self):
        self.db = SessionLocal()
        logger.info(f"Database storage initialized with: {DATABASE_URL[:50]}...")

    # ... (save_post, fetch_posts, count_posts, get_categories functions remain the same as before) ...

storage = ChannelStorage()
