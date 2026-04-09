"""Initialize database and create all tables."""

import logging
import sys

from app.db.database import engine, Base, init_pgvector
from app.models.need import Need
from app.models.volunteer import Volunteer
from app.models.assignment import Assignment
from app.models.alert_log import AlertLog

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def init_db():
    """Create all database tables and enable pgvector."""
    try:
        logger.info("Initializing database...")

        # Enable pgvector extension
        init_pgvector()

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")

    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_db()
