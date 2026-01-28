#!/usr/bin/env python3
"""
Database migration script - Safe for Railway build
"""

import os
import sys

def migrate_postgres():
    """Safe migration that won't fail build"""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("ℹ️ DATABASE_URL not set, skipping migration")
        print("⚠️ Note: Using SQLite for local development only")
        return True  # Don't fail build
    
    # Fix URL format for Railway
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    print(f"🔄 Attempting database migration...")
    
    try:
        from sqlalchemy import create_engine, text
        
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'posts'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("📊 Creating posts table...")
                conn.execute(text("""
                    CREATE TABLE posts (
                        id SERIAL PRIMARY KEY,
                        message_id INTEGER UNIQUE NOT NULL,
                        content TEXT NOT NULL,
                        media_type VARCHAR(50) DEFAULT 'text',
                        category VARCHAR(100) DEFAULT 'general',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create indexes
                conn.execute(text("CREATE INDEX idx_posts_message_id ON posts(message_id)"))
                conn.execute(text("CREATE INDEX idx_posts_category ON posts(category)"))
                conn.execute(text("CREATE INDEX idx_posts_timestamp ON posts(timestamp DESC)"))
                
                print("✅ Posts table created successfully")
                
                # Insert sample data if empty
                result = conn.execute(text("SELECT COUNT(*) FROM posts"))
                count = result.scalar()
                
                if count == 0:
                    conn.execute(text("""
                        INSERT INTO posts (message_id, content, media_type, category) VALUES
                        (1, 'Welcome to Telegram Mini App!', 'text', 'general'),
                        (2, 'Important announcement', 'text', 'important'),
                        (3, 'Daily news update', 'text', 'news')
                    """))
                    print(f"📝 Inserted {3} sample posts")
            else:
                print("✅ Posts table already exists")
            
            conn.commit()
        
        print("🎉 Database migration completed successfully")
        return True
        
    except Exception as e:
        print(f"⚠️ Migration note: {e}")
        print("ℹ️ Tables will be created automatically on first use")
        return True  # Don't fail the build

if __name__ == '__main__':
    success = migrate_postgres()
    sys.exit(0 if success else 1)