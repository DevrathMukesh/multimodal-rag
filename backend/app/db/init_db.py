from app.db.base import Base
from app.db.session import engine
from app.utils.file import ensure_dir
from app.core.config import settings
from app.db.migrate_add_sources import migrate_add_sources_column
import logging

logger = logging.getLogger(__name__)


def init_directories() -> None:
    ensure_dir(settings.data_dir)
    ensure_dir(settings.uploads_dir)
    ensure_dir(settings.chroma_dir)


def init_db() -> None:
    """Initialize database schema and run migrations."""
    try:
        # Create all tables (for new databases)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}", exc_info=True)
        raise
    
    # Run migrations for existing databases
    try:
        success = migrate_add_sources_column()
        if success:
            logger.info("Database migration completed successfully")
        else:
            logger.warning("Database migration may have failed - check logs above")
    except Exception as e:
        logger.error(f"Error running database migration: {e}", exc_info=True)
        # Don't raise - migration failures shouldn't prevent app startup
        # if the column doesn't exist, operations will fail anyway


