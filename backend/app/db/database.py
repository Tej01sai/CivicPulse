"""Database connection and session management."""

import logging
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Create engine with pgvector support
engine = create_engine(
    settings.database_url,
    echo=False,
    poolclass=NullPool,  # Disable pooling for compatibility with serverless
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to inject database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_pgvector():
    """Enable pgvector extension in PostgreSQL."""
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("pgvector extension enabled")
        except Exception as e:
            logger.error(f"Failed to enable pgvector: {e}")
            conn.rollback()
