from app.db.base import Base
from app.db.session import engine
from app.utils.file import ensure_dir
from app.core.config import settings
from app.db.migrate_add_sources import migrate_add_sources_column
from app.db.migrate_add_status import migrate_add_status_column
from app.db.migrate_add_progress import migrate_add_progress_column
import logging

# Import models to ensure they're registered with Base.metadata before table creation
from app.models.document import Document  # noqa: F401
from app.models.message import Message  # noqa: F401

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
        migrate_add_sources_column()
        migrate_add_status_column()
        migrate_add_progress_column()
        logger.info("Database migrations completed")
    except Exception as e:
        logger.error(f"Error running database migrations: {e}", exc_info=True)
        # Don't raise - migration failures shouldn't prevent app startup


