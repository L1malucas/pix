"""Database session management."""
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """
    Get database session.

    Yields:
        Session: SQLAlchemy database session

    Usage in FastAPI:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("database_session_error", error=str(e), exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


# Type alias for dependency injection
DBSession = Annotated[Session, Depends(get_db)]
