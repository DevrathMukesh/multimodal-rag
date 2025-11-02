"""
Migration script to add sources_json column to messages table.

Run this script once to add the sources_json column to existing databases.
For new databases, the column will be created automatically via SQLAlchemy.

Usage:
    python -m app.db.migrate_add_sources
"""
import sqlite3
import os
from pathlib import Path
from app.core.config import settings

def migrate_add_sources_column():
    """Add sources_json column to messages table if it doesn't exist."""
    # Determine database path - use the same logic as session.py
    db_url = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    
    # Extract SQLite path from URL
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        # Handle relative paths - resolve from current working directory
        if not os.path.isabs(db_path):
            # Use os.getcwd() to match how SQLAlchemy resolves relative paths
            db_path = os.path.join(os.getcwd(), db_path)
            # Normalize the path
            db_path = os.path.normpath(db_path)
    else:
        print(f"Migration only supports SQLite databases. Got: {db_url}")
        return False
    
    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # If database doesn't exist yet, SQLAlchemy will create it with the column
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}. It will be created with the column automatically.")
        return True
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "sources_json" in columns:
            print(f"Column 'sources_json' already exists in {db_path}. Migration not needed.")
            conn.close()
            return True
        
        # Add the column
        print(f"Adding 'sources_json' column to messages table in {db_path}...")
        cursor.execute("ALTER TABLE messages ADD COLUMN sources_json TEXT")
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    migrate_add_sources_column()
