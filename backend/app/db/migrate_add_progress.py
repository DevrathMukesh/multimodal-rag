"""
Migration script to add progress column to documents table.

Run this script once to add the progress column to existing databases.
For new databases, the column will be created automatically via SQLAlchemy.

Usage:
    python -m app.db.migrate_add_progress
"""
import sqlite3
import os
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def migrate_add_progress_column() -> bool:
    """Add progress column to documents table if it doesn't exist."""
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
        logger.warning(f"Migration only supports SQLite databases. Got: {db_url}")
        return False
    
    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # If database doesn't exist yet, SQLAlchemy will create it with the column
    if not os.path.exists(db_path):
        logger.info(f"Database file not found at {db_path}. It will be created with the column automatically.")
        return True
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(documents)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "progress" in columns:
            logger.info(f"Column 'progress' already exists in {db_path}. Migration not needed.")
            conn.close()
            return True
        
        # Add the column
        logger.info(f"Adding 'progress' column to documents table in {db_path}...")
        cursor.execute("ALTER TABLE documents ADD COLUMN progress INTEGER DEFAULT 0")
        conn.commit()
        
        # Update existing documents to have 0 progress (or 100 if completed)
        cursor.execute("UPDATE documents SET progress = CASE WHEN status = 'completed' THEN 100 ELSE 0 END WHERE progress IS NULL")
        conn.commit()
        conn.close()
        
        logger.info("Migration completed successfully!")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error during migration: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    migrate_add_progress_column()

