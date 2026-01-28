#!/usr/bin/env python3
"""
Database migration script for Railway PostgreSQL
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

def migrate_postgres():
    """Migrate to PostgreSQL"""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set")
        print("Please add PostgreSQL database on Railway")
        return False
    
    # Fix URL format for Railway
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    print(f"🔄 Migrating to PostgreSQL database...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Create tables
        with engine.connect() as conn:
            # Read schema file
            schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
            if os.path.exists(schema_file):
                with open(schema_file, 'r') as f:
                    schema_sql = f.read()
                
                # Execute schema
                for statement in schema_sql.split(';'):
                    statement = statement.strip()
                    if statement:
                        conn.execute(text(statement))
                
                print("✅ Database schema created successfully")
            
            # Check existing data
            result = conn.execute(text("SELECT COUNT(*) FROM posts"))
            count = result.scalar()
            print(f"📊 Total posts in database: {count}")
            
            conn.commit()
        
        print("✅ Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    migrate_postgres()